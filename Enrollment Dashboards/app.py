import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Set page config
st.set_page_config(page_title="Enrollment Management Dashboard", layout="wide")

# Load data
@st.cache_data
def load_data():
    # Update the path to where your CSV file is located
    df = pd.read_csv("data/enrollment.csv")
    
    # Convert date columns to datetime
    date_columns = ['Inquiry Date Submitted', 'Application Date Submitted', 
                   'Candidate decision date', 'School Decision Date']
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df

df = load_data()

# Sidebar for global filters
st.sidebar.title("Filters")

# Year filter
selected_years = st.sidebar.multiselect(
    "Select Academic Years",
    options=sorted(df['Entering Year'].unique()),
    default=sorted(df['Entering Year'].unique())[-3:]  # Last 3 years by default
)

# Apply filters
filtered_df = df[df['Entering Year'].isin(selected_years)]

# Main dashboard title
st.title("Enrollment Management Dashboard")

# Statistics Section
st.markdown("### Statistics")

# Calculate correct pipeline statistics
total_inquiries = len(filtered_df[filtered_df['Candidate Status'] == 'Inquiry'])
total_applications = len(filtered_df[filtered_df['Candidate Status'].isin(['Applicant', 'File Complete', 'Decision', 'Contract'])])
total_accepted = len(filtered_df[filtered_df['Candidate Decision'] == 'Accepted'])
total_contracts = len(filtered_df[filtered_df['Candidate Status'] == 'Contract'])

# Create three columns for the first row of statistics
col1, col2, col3 = st.columns(3)

# Display first row of metrics
with col1:
    st.markdown(f"""
        <div style='text-align: center'>
            <h1 style='font-size: 48px; margin-bottom: 0;'>{total_inquiries}</h1>
            <p style='color: #666; margin-top: 0;'># of inquiries</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div style='text-align: center'>
            <h1 style='font-size: 48px; margin-bottom: 0;'>{total_applications}</h1>
            <p style='color: #666; margin-top: 0;'># of applications</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div style='text-align: center'>
            <h1 style='font-size: 48px; margin-bottom: 0;'>{total_contracts}</h1>
            <p style='color: #666; margin-top: 0;'># of contracts</p>
        </div>
    """, unsafe_allow_html=True)

# Create four columns for the second row of statistics
col4, col5, col6, col7 = st.columns(4)

# Calculate rates
acceptance_rate = (total_accepted / total_applications * 100) if total_applications > 0 else 0
yield_rate = (total_contracts / total_accepted * 100) if total_accepted > 0 else 0

with col4:
    st.metric("Total Applicants", total_applications)
    
with col5:
    st.metric("Total Accepted", total_accepted)
    
with col6:
    st.metric("Acceptance Rate", f"{acceptance_rate:.1f}%")
    
with col7:
    st.metric("Yield Rate", f"{yield_rate:.1f}%")

st.markdown("---")  # Add a divider line

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["Application Pipeline", "Demographics", "Timeline Analysis"])

with tab1:
    # Application Pipeline Funnel
    stages = ['Inquiry', 'Applicant', 'File Complete', 'Decision', 'Contract']
    stage_counts = [len(filtered_df[filtered_df['Candidate Status'] == stage]) for stage in stages]
    
    fig_funnel = go.Figure(go.Funnel(
        y=stages,
        x=stage_counts,
        textinfo="value+percent initial"
    ))
    fig_funnel.update_layout(title_text="Application Pipeline Funnel")
    st.plotly_chart(fig_funnel, use_container_width=True)
    
    # Status by grade level
    st.subheader("Application Status by Grade Level")
    
    # Define custom grade order
    grade_order = [
        'Kindergarten', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 
        'Grade 5', 'Grade 6', 'Grade 7', 'Grade 8', 'Grade 9', 
        'Grade 10', 'Grade 11', 'Grade 12'
    ]
    
    # Create crosstab for status
    status_by_grade = pd.crosstab(filtered_df['Entering Grade'], 
                                 filtered_df['Candidate Status'])
    
    # Create bar plot for status
    fig_status = px.bar(status_by_grade,
                       barmode='group',
                       title="Application Status by Grade Level")
    st.plotly_chart(fig_status, use_container_width=True)
    
    # Inquiry Distribution Section
    st.subheader("Inquiry Distribution")

    # 1. Inquiries by Grade Level
    grade_inquiries = filtered_df[filtered_df['Candidate Status'] == 'Inquiry']['Entering Grade'].value_counts().reset_index()
    grade_inquiries.columns = ['Grade Level', 'Number of Inquiries']
    
    # Sort by grade order
    grade_inquiries['Grade Level'] = pd.Categorical(grade_inquiries['Grade Level'], 
                                                  categories=grade_order,
                                                  ordered=True)
    grade_inquiries = grade_inquiries.sort_values('Grade Level')
    
    fig_grade_inquiry = go.Figure()
    fig_grade_inquiry.add_trace(go.Bar(
        x=grade_inquiries['Number of Inquiries'],
        y=grade_inquiries['Grade Level'],
        orientation='h',
        marker_color='#3182CE',
        text=grade_inquiries['Number of Inquiries'],
        textposition='outside',
    ))
    
    fig_grade_inquiry.update_layout(
        title="Inquiries by Grade Level",
        height=400,
        yaxis={
            'categoryorder': 'array',
            'categoryarray': grade_inquiries['Grade Level'].tolist()[::-1],
            'title': '',
        },
        xaxis={
            'title': 'Number of Inquiries',
            'showgrid': True,
            'gridwidth': 1,
            'gridcolor': 'LightGray'
        },
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='white',
    )
    
    st.plotly_chart(fig_grade_inquiry, key="grade_inquiry_chart", use_container_width=True)
    
    # 2. Inquiries by Month
    # First filter by selected school year and inquiry status
    inquiries_df = filtered_df[
        (filtered_df['Candidate Status'] == 'Inquiry')
    ].copy()
    
    # Convert dates properly
    inquiries_df['Inquiry_Date'] = pd.to_datetime(
        inquiries_df['Inquiry Date Submitted'],
        format='mixed',
        errors='coerce'
    )
    
    # Extract month name
    inquiries_df['Month'] = inquiries_df['Inquiry_Date'].dt.strftime('%B')
    
    # Get counts by month
    monthly_counts = inquiries_df['Month'].value_counts().reset_index()
    monthly_counts.columns = ['Month', 'Number of Inquiries']
    
    # Define month order for academic year
    month_order = [
        'August', 'September', 'October', 'November', 'December',
        'January', 'February', 'March', 'April', 'May', 'June', 'July'
    ]
    
    # Create base DataFrame with all months
    all_months = pd.DataFrame({'Month': month_order})
    
    # Merge with counts and fill missing values
    monthly_inquiries = pd.merge(
        all_months,
        monthly_counts,
        on='Month',
        how='left'
    )
    
    # Fill NaN with 0 and ensure int type
    monthly_inquiries['Number of Inquiries'] = monthly_inquiries['Number of Inquiries'].fillna(0).astype(int)
    
    # Set up categorical ordering of months
    monthly_inquiries['Month'] = pd.Categorical(
        monthly_inquiries['Month'],
        categories=month_order,
        ordered=True
    )
    
    # Sort in reverse to match the grade level chart
    monthly_inquiries = monthly_inquiries.sort_values('Month', ascending=False)
    
    # Create the horizontal bar chart
    fig_monthly_inquiry = go.Figure()
    
    fig_monthly_inquiry.add_trace(go.Bar(
        x=monthly_inquiries['Number of Inquiries'],
        y=monthly_inquiries['Month'],
        orientation='h',
        marker_color='#3182CE',
        text=monthly_inquiries['Number of Inquiries'],
        textposition='outside',
    ))
    
    fig_monthly_inquiry.update_layout(
        title="Inquiries by Month",
        height=400,
        yaxis={
            'categoryorder': 'array',
            'categoryarray': month_order[::-1],
            'title': '',
        },
        xaxis={
            'title': 'Number of Inquiries',
            'showgrid': True,
            'gridwidth': 1,
            'gridcolor': 'LightGray',
            'range': [0, monthly_inquiries['Number of Inquiries'].max() * 1.1]  # Add 10% padding
        },
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='white',
    )
    
    st.plotly_chart(fig_monthly_inquiry, key="monthly_inquiries", use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        # Gender distribution
        gender_dist = filtered_df['Gender'].value_counts()
        fig_gender = px.pie(values=gender_dist.values, 
                          names=gender_dist.index,
                          title="Gender Distribution")
        st.plotly_chart(fig_gender)
    
    with col2:
        # International vs Domestic
        intl_dist = filtered_df['International'].value_counts()
        fig_intl = px.pie(values=intl_dist.values,
                         names=intl_dist.index,
                         title="International vs Domestic Students")
        st.plotly_chart(fig_intl)
    
    # Financial Aid distribution
    fa_dist = filtered_df['Financial Aid'].value_counts()
    fig_fa = px.bar(x=fa_dist.index,
                    y=fa_dist.values,
                    title="Financial Aid Distribution")
    st.plotly_chart(fig_fa, use_container_width=True)

with tab3:
    # Timeline analysis
    if 'Application Date Submitted' in filtered_df.columns:
        filtered_df['Application Month'] = filtered_df['Application Date Submitted'].dt.strftime('%Y-%m')
        monthly_apps = filtered_df.groupby('Application Month').size().reset_index()
        monthly_apps.columns = ['Month', 'Number of Applications']
        monthly_apps = monthly_apps.sort_values('Month')
        
        fig_timeline = px.line(
            monthly_apps,
            x='Month',
            y='Number of Applications',
            title="Application Submissions Over Time",
            markers=True
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Average time to decision
    filtered_df['Days_to_Decision'] = (filtered_df['School Decision Date'] - 
                                     filtered_df['Application Date Submitted']).dt.days
    avg_decision_time = filtered_df.groupby('Entering Year')['Days_to_Decision'].mean().reset_index()
    avg_decision_time.columns = ['Year', 'Average Days']
    
    fig_decision_time = px.bar(
        avg_decision_time,
        x='Year',
        y='Average Days',
        title="Average Days to Decision by Year"
    )
    st.plotly_chart(fig_decision_time, use_container_width=True)

# Add download button for filtered data
st.sidebar.download_button(
    label="Download Filtered Data",
    data=filtered_df.to_csv(index=False).encode('utf-8'),
    file_name='filtered_enrollment_data.csv',
    mime='text/csv'
)

## add huge bar chart that lets you compare all inquery and application information for all years. 
## it should be easy for the admissions office to look at the data and compare month to month and year to year 
#To see where they are and where they can improve. (See if you can find the good chart Nina showed you as an example)