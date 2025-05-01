import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Load data
df = pd.read_csv("data/upwork-cleaned.csv")

# Clean up numeric columns (in case there are empty strings)
for col in ['hourly_rate_min', 'hourly_rate_max', 'fixed_price', 'estimated_total_pay']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Sidebar: search_term selector
search_terms = ['All'] + sorted(df['search_term'].dropna().unique())
selected_search_term = st.selectbox("Select search term", search_terms)

# Key stats for all jobs
all_num_jobs = len(df)
all_avg_hourly_rate = np.nanmean((df['hourly_rate_min'] + df['hourly_rate_max']) / 2)
all_avg_fixed_price = np.nanmean(df['fixed_price'])
all_avg_estimated_total_pay = np.nanmean(df['estimated_total_pay'])

# Key stats for filtered jobs
if selected_search_term != 'All':
    filtered_df = df[df['search_term'] == selected_search_term]
else:
    filtered_df = df

num_jobs = len(filtered_df)
avg_hourly_rate = np.nanmean((filtered_df['hourly_rate_min'] + filtered_df['hourly_rate_max']) / 2)
avg_fixed_price = np.nanmean(filtered_df['fixed_price'])
avg_estimated_total_pay = np.nanmean(filtered_df['estimated_total_pay'])

# Display stats
st.title("Upwork Job Dashboard")
if selected_search_term == 'All':
    st.subheader("Key Stats for All Jobs")
else:
    st.subheader(f"Key Stats for '{selected_search_term}' Jobs (compared to All Jobs)")

col1, col2, col3, col4 = st.columns(4)

# Number of Jobs
if selected_search_term == 'All':
    col1.metric("Number of Jobs", num_jobs)
else:
    col1.metric(
        "Number of Jobs",
        num_jobs,
        delta=f"{num_jobs - all_num_jobs:+}"
    )

# Avg Hourly Rate
if selected_search_term == 'All':
    col2.metric("Avg Hourly Rate", f"${avg_hourly_rate:,.2f}" if not np.isnan(avg_hourly_rate) else "N/A")
else:
    delta = avg_hourly_rate - all_avg_hourly_rate if not np.isnan(avg_hourly_rate) and not np.isnan(all_avg_hourly_rate) else None
    col2.metric(
        "Avg Hourly Rate",
        f"${avg_hourly_rate:,.2f}" if not np.isnan(avg_hourly_rate) else "N/A",
        delta=f"{delta:+.2f}" if delta is not None else "N/A"
    )

# Avg Fixed Price
if selected_search_term == 'All':
    col3.metric("Avg Fixed Price", f"${avg_fixed_price:,.2f}" if not np.isnan(avg_fixed_price) else "N/A")
else:
    delta = avg_fixed_price - all_avg_fixed_price if not np.isnan(avg_fixed_price) and not np.isnan(all_avg_fixed_price) else None
    col3.metric(
        "Avg Fixed Price",
        f"${avg_fixed_price:,.2f}" if not np.isnan(avg_fixed_price) else "N/A",
        delta=f"{delta:+.2f}" if delta is not None else "N/A"
    )

# Avg Estimated Total Pay
if selected_search_term == 'All':
    col4.metric("Avg Est. Total Pay", f"${avg_estimated_total_pay:,.2f}" if not np.isnan(avg_estimated_total_pay) else "N/A")
else:
    delta = avg_estimated_total_pay - all_avg_estimated_total_pay if not np.isnan(avg_estimated_total_pay) and not np.isnan(all_avg_estimated_total_pay) else None
    col4.metric(
        "Avg Est. Total Pay",
        f"${avg_estimated_total_pay:,.2f}" if not np.isnan(avg_estimated_total_pay) else "N/A",
        delta=f"{delta:+.2f}" if delta is not None else "N/A"
    )

# --- Distribution Plot ---
st.markdown("### Distribution of Estimated Total Pay (Interactive)")

pay_data = filtered_df['estimated_total_pay'].dropna()
pay_data = pay_data[pay_data > 0]

if len(pay_data) == 0:
    st.info("No estimated total pay data available for this selection.")
else:
    # Set number of bins
    nbins = 20
    counts, bins = np.histogram(pay_data, bins=nbins)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    hover_texts = []

    # Prepare custom hover text for each bar
    for i in range(nbins):
        bin_mask = (pay_data >= bins[i]) & (pay_data < bins[i+1])
        jobs_in_bin = pay_data[bin_mask]
        count = len(jobs_in_bin)
        avg_pay = jobs_in_bin.mean() if count > 0 else 0
        hover_texts.append(
            f"Range: ${bins[i]:,.0f} - ${bins[i+1]:,.0f}<br>"
            f"Jobs: {count}<br>"
            f"Avg Est. Total Pay: ${avg_pay:,.2f}"
        )

    fig = go.Figure(
        data=[
            go.Bar(
                x=bin_centers,
                y=counts,
                width=(bins[1] - bins[0]),
                marker_color="#4e79a7",
                hovertext=hover_texts,
                hoverinfo="text"
            )
        ]
    )
    fig.update_layout(
        xaxis_title="Estimated Total Pay ($)",
        yaxis_title="Number of Jobs",
        title=f"Estimated Total Pay Distribution ({selected_search_term})",
        bargap=0.05
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Skill Bar Chart Section ---

# 1. Sorting option (must come first!)
sort_option = st.radio(
    "Sort skills by:",
    ["Most Popular", "Highest Paying"],
    horizontal=True
)

# 2. Gather all skills into a single Series
skill_cols = [col for col in filtered_df.columns if col.startswith("skill_")]
skills = pd.Series(dtype=str)
skill_pay = []

for col in skill_cols:
    col_skills = filtered_df[[col, 'estimated_total_pay']].dropna()
    for skill, pay in zip(col_skills[col], col_skills['estimated_total_pay']):
        if pd.notna(skill) and skill != '':
            skills = pd.concat([skills, pd.Series([skill])], ignore_index=True)
            skill_pay.append((skill, pay))

# 3. Count occurrences
skill_counts = skills.value_counts()

# 4. Calculate average estimated_total_pay per skill
from collections import defaultdict
pay_sum = defaultdict(float)
pay_count = defaultdict(int)
for skill, pay in skill_pay:
    pay_sum[skill] += pay
    pay_count[skill] += 1
avg_pay = {skill: pay_sum[skill]/pay_count[skill] for skill in pay_sum}

# 5. Create DataFrame for plotting
skill_df = pd.DataFrame({
    'Skill': skill_counts.index,
    'Count': skill_counts.values,
    'AvgPay': [avg_pay.get(skill, 0) for skill in skill_counts.index]
})

# 6. Sort by selected option
if sort_option == "Most Popular":
    skill_df = skill_df.sort_values("Count", ascending=False)
else:
    skill_df = skill_df.sort_values("AvgPay", ascending=False)

# 7. Show top 15 skills
skill_df = skill_df.head(15)

st.markdown("### Top Skills in Selected Jobs")

if skill_df.empty:
    st.info("No skills data available for this selection.")
else:
    fig2 = px.bar(
        skill_df,
        x="Count" if sort_option == "Most Popular" else "AvgPay",
        y="Skill",
        orientation="h",
        text="Count" if sort_option == "Most Popular" else "AvgPay",
        color="AvgPay" if sort_option == "Highest Paying" else "Count",
        color_continuous_scale="Blues" if sort_option == "Most Popular" else "Viridis",
        labels={"Count": "Number of Jobs", "AvgPay": "Avg Est. Total Pay ($)", "Skill": "Skill"},
        title="Top Skills by " + ("Popularity" if sort_option == "Most Popular" else "Avg Est. Total Pay"),
        custom_data=["Count", "AvgPay"]
    )
    fig2.update_layout(yaxis={'categoryorder':'total ascending'})
    fig2.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Number of Jobs: %{customdata[0]}<br>"
            "Avg Est. Total Pay: $%{customdata[1]:,.2f}<br>"
            "<extra></extra>"
        )
    )
    st.plotly_chart(fig2, use_container_width=True)
