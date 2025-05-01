import pandas as pd
from functions import (
    parse_hourly_rate, parse_hours_per_week, parse_duration_weeks,
    parse_fixed_price, estimate_total_pay, get_pay_type, standardize_search_term_column,
    clean_and_standardize_skill
)

# Load CSV
df = pd.read_csv('data/upwork-extract.csv')
print(df.shape)
print(df.head())

# change column names
df.columns = [
    "date_posted", "job_title", "job_url", "search_term", "payment_status",
    "client_rating_text", "client_rating_value", "client_rating_details", "client_total_spent",
    "spent", "client_location", "hourly_or_fixed", "job_expertise_level",
    "est_time_or_budget", "duration_or_budget", "job_description", "skill_1",
    "skill_2", "skill_3", "skill_4", "skill_5", "num_proposals",
    "proposals_range", "skill_6", "skill_7", "skill_8", "skill_9",
    "skill_10", "skill_11", "skill_12", "skill_13"
]

# drop columns
cols_to_keep = [
    "job_title", "job_url", "search_term",
    "hourly_or_fixed", "est_time_or_budget", "duration_or_budget", "job_description", 
    "skill_1","skill_2", "skill_3", "skill_4", "skill_5", "skill_6", "skill_7", "skill_8", "skill_9",
    "skill_10", "skill_11", "skill_12", "skill_13"
]
df = df[cols_to_keep]

# drop duplicate jobs
df = df.drop_duplicates("job_url")

# Add new columns
df['pay_type'] = df['hourly_or_fixed'].apply(get_pay_type)
df[['hourly_rate_min', 'hourly_rate_max']] = df['hourly_or_fixed'].apply(
    lambda x: pd.Series(parse_hourly_rate(x))
)
df['est_hours_per_week'] = df['duration_or_budget'].apply(parse_hours_per_week)
df['est_duration_weeks'] = df['duration_or_budget'].apply(parse_duration_weeks)
df['fixed_price'] = df['duration_or_budget'].apply(parse_fixed_price)
df['estimated_total_pay'] = df.apply(estimate_total_pay, axis=1)

# drop rows where estimated_total_pay is NaN
df = df[df['estimated_total_pay'].notna()]

# remove unneeded columns
df = df.drop(columns=['hourly_or_fixed', 'duration_or_budget'])

# reorder columns
df = df[['job_title', 'job_url', 'search_term', 
'pay_type', 'hourly_rate_min', 'hourly_rate_max', 'est_hours_per_week', 'est_duration_weeks', 
'fixed_price', 'estimated_total_pay', 'job_description', 
'skill_1', 'skill_2', 'skill_3', 'skill_4', 'skill_6', 'skill_7', 
'skill_8', 'skill_9', 'skill_10', 'skill_11', 'skill_12', 'skill_13']]

# standardize search_term column
df = standardize_search_term_column(df)

# clean and standardize skills
skill_cols = [col for col in df.columns if col.startswith("skill_")]
for col in skill_cols:
    df[col] = df[col].apply(clean_and_standardize_skill)

# save to csv
df.head(100).to_csv("data/upwork-cleaned-100.csv", index=False)
df.to_csv("data/upwork-cleaned.csv", index=False)
