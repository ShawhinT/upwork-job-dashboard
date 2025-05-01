import pandas as pd
import re
import numpy as np


def parse_hourly_rate(text):
    """Extract minimum and maximum hourly rates from a text string.

    Args:
        text (str): Text containing hourly rate information (e.g., "Hourly: $75.00 - $100.00")

    Returns:
        tuple: A tuple containing (min_rate, max_rate) as floats. Returns (np.nan, np.nan) if no match found.
    """
    # Example: "Hourly: $75.00 - $100.00" or "Hourly: $75.00"
    if pd.isna(text):
        return np.nan, np.nan
    match = re.search(r"\$([\d,\.]+)(?:\s*-\s*\$([\d,\.]+))?", text)
    if match:
        min_rate = float(match.group(1).replace(',', ''))
        max_rate = float(match.group(2).replace(',', '')) if match.group(2) else min_rate
        return min_rate, max_rate
    return np.nan, np.nan

def parse_hours_per_week(text):
    """Extract the number of hours per week from a text string.

    Args:
        text (str): Text containing hours per week information (e.g., "30+ hrs/week")

    Returns:
        float: Number of hours per week. Returns 25 if text contains "less than" and np.nan if no match found.
    """
    # Example: "30+ hrs/week", "Less than 30 hrs/week"
    if pd.isna(text):
        return np.nan
    match = re.search(r"(\d+)\+?\s*hrs?/week", text)
    if match:
        return float(match.group(1))
    if "less than" in text.lower():
        return 25  # reasonable estimate
    return np.nan

def parse_duration_weeks(text):
    """Convert duration text to number of weeks.

    Args:
        text (str): Text containing duration information (e.g., "1 to 3 months")

    Returns:
        float: Number of weeks. Returns 2 for "less than 1 month" and np.nan if no match found.
    """
    # Example: "1 to 3 months", "Less than 1 month"
    if pd.isna(text):
        return np.nan
    match = re.search(r"(\d+)\s*to\s*(\d+)\s*months?", text)
    if match:
        avg_months = (float(match.group(1)) + float(match.group(2))) / 2
        return avg_months * 4
    match = re.search(r"(\d+)\s*months?", text)
    if match:
        return float(match.group(1)) * 4
    if "less than 1 month" in text.lower():
        return 2  # estimate 2 weeks
    return np.nan

def parse_fixed_price(text):
    """Extract fixed price amount from a text string.

    Args:
        text (str): Text containing fixed price information (e.g., "$750.00")

    Returns:
        float: Fixed price amount. Returns np.nan if no match found.
    """
    # Example: "$750.00"
    if pd.isna(text):
        return np.nan
    match = re.search(r"\$([\d,\.]+)", text)
    if match:
        return float(match.group(1).replace(',', ''))
    return np.nan

def estimate_total_pay(row):
    """Calculate the estimated total pay for a job posting.

    This function estimates total pay based on whether the job is hourly or fixed price.
    For hourly jobs, it calculates: avg_rate * hours_per_week * weeks
    For fixed price jobs, it returns the fixed price amount.

    Args:
        row (pd.Series): A pandas Series containing job posting information with keys:
            - hourly_or_fixed: String indicating if job is hourly or fixed price
            - duration_or_budget: String containing duration/hours for hourly jobs or
                                fixed price amount for fixed price jobs

    Returns:
        float: Estimated total pay amount. Returns np.nan if unable to calculate.
    """
    if isinstance(row['hourly_or_fixed'], str) and 'hourly' in row['hourly_or_fixed'].lower():
        min_rate, max_rate = parse_hourly_rate(row['hourly_or_fixed'])
        avg_rate = np.nanmean([min_rate, max_rate])
        hours_per_week = parse_hours_per_week(row['duration_or_budget'])
        weeks = parse_duration_weeks(row['duration_or_budget'])
        if np.isnan(hours_per_week):
            hours_per_week = 30  # fallback
        if np.isnan(weeks):
            weeks = 8  # fallback to 2 months
        return avg_rate * hours_per_week * weeks
    elif isinstance(row['hourly_or_fixed'], str) and 'fixed' in row['hourly_or_fixed'].lower():
        return parse_fixed_price(row['duration_or_budget'])
    else:
        return np.nan

def get_pay_type(text):
    """Return 'Hourly' or 'Fixed' based on the hourly_or_fixed text."""
    if isinstance(text, str):
        if 'hourly' in text.lower():
            return 'Hourly'
        elif 'fixed' in text.lower():
            return 'Fixed'
    return np.nan

def standardize_search_term_column(df):
    """
    Standardizes and maps the 'search_term' column in the dataframe to standardized categories.
    - Lowercases all values.
    - Maps to a set of predefined categories.
    - Imputes missing values using forward fill.
    """
    # Impute missing values of search_term using previous row's search_term
    df['search_term'] = df['search_term'].ffill()
    # Standardize search_term values
    df['search_term'] = df['search_term'].str.lower()
    # Map search_term values to standardized categories
    search_term_map = {
        'ai': 'AI',
        'artificial': 'AI',
        'intelligent': 'AI',
        'machine': 'ML',
        'learning': 'ML',
        'statistics': 'statistics',
        'engineer': 'data engineering',
        'data': 'data engineering',
        'python': 'data engineering',  # or 'ML' if you prefer
    }
    df['search_term'] = df['search_term'].map(search_term_map)
    return df

def clean_and_standardize_skill(skill):
    """
    Standardizes and cleans a single skill string.
    - Removes non-skill entries (e.g., '+1', '+4', etc.)
    - Standardizes capitalization and maps synonyms to canonical forms
    - Removes generic or non-skill words
    Returns None if the skill should be dropped.
    """
    if pd.isna(skill) or not str(skill).strip():
        return None

    # Remove non-skill entries like "+1"
    if re.match(r'^\+\d+$', str(skill).strip()):
        return None

    # Remove known non-skills
    non_skills = set([
        'female', 'budget', 'company', 'project', 'article', 'review', 'advertisement', 'advertising',
        'media', 'english', 'accuracy verification', 'casual tone', 'presentation', 'resume',
        'error detection', 'draft documentation', 'product knowledge', 'client management',
        'communication skills', 'critical thinking skills', 'personal computer', 'smartphone',
        'phone communication', 'accounts payable', 'accounts receivable', 'customer experience',
        'heap', 'review', 'scientist', 'engineer', 'engineering', 'learn', 'learning'
        # Add more as needed
    ])
    skill_lower = str(skill).strip().lower()
    if skill_lower in non_skills:
        return None

    # Canonical mapping for common synonyms
    canonical_map = {
        'ai': 'Artificial Intelligence',
        'artificial': 'Artificial Intelligence',
        'artificial intelligence': 'Artificial Intelligence',
        'machine': 'Machine Learning',
        'machine learning': 'Machine Learning',
        'ml': 'Machine Learning',
        'python': 'Python',
        'data': 'Data Science',
        'data science': 'Data Science',
        'statistics': 'Statistics',
        'statistical': 'Statistics',
        'statistic': 'Statistics',
        'deep learning': 'Deep Learning',
        'nlp': 'Natural Language Processing',
        'natural language processing': 'Natural Language Processing',
        # Add more mappings as needed
    }
    if skill_lower in canonical_map:
        return canonical_map[skill_lower]

    # Otherwise, just title-case for consistency
    return str(skill).strip().title()
