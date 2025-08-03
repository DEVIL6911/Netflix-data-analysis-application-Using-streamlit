import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from PIL import Image
st.set_page_config(page_title="Netflix Movies Analyzer", layout="wide")
try:
    st.image("netflix_banner.jpeg", use_column_width=True)
except Exception as e:
    st.warning("Banner image not found or could not be loaded.")

# Title and Description
st.title(" Netflix Movies Data Analysis App")
st.markdown("""
This interactive app helps you explore and analyze Netflix movies and TV shows data.
Upload your own CSV file to begin exploring insights like:
- Most frequent genres
- Popularity & vote averages
- Year-wise trends
""")

# File Upload
file = st.file_uploader(" Upload your CSV file", type=["csv"])

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file, lineterminator='\n')
    return df

# Load and Clean Data
if file:
    df = load_data(file)

    st.success(" Data successfully loaded!")
    st.dataframe(df.head())

    # Required columns check
    required_cols = ['Title', 'Release_Date', 'Genre', 'Vote_Average', 'Popularity']
    if not all(col in df.columns for col in required_cols):
        st.error(f"Missing one or more required columns: {', '.join(required_cols)}")
        st.stop()

    # Data Cleaning
    df.dropna(subset=required_cols, inplace=True)
    df['Release_Date'] = pd.to_datetime(df['Release_Date'], errors='coerce')
    df['Release_Year'] = df['Release_Date'].dt.year
    df['Genre'] = df['Genre'].fillna('Unknown').str.split(', ')
    df = df.explode('Genre').reset_index(drop=True)
    df['Genre'] = df['Genre'].astype('category')

    st.sidebar.header("🔍 Filter Options")
    unique_genres = sorted(df['Genre'].dropna().unique())
    selected_genre = st.sidebar.selectbox("Select Genre to Filter", options=["All"] + unique_genres)

    filtered_df = df if selected_genre == "All" else df[df['Genre'] == selected_genre]

    # Pie Chart: Popularity Category Distribution
    st.markdown("###  Q1. Popularity Categories (Out of 10,000 movies)")
    col1, col2 = st.columns(2)

    with col1:
        labels = ['not_popular', 'below_avg', 'average', 'popular']
        sizes = [2467, 2450, 2412, 2398]
        fig1 = px.pie(
            names=labels, values=sizes,
            color_discrete_sequence=px.colors.sequential.RdBu,
            title="Popularity Distribution by Category",
            hole=0.3
        )
        st.plotly_chart(fig1, use_container_width=True)

    # Bar Chart: Genre Distribution
    with col2:
        st.markdown("###  Q2. Most Frequent Genres")
        genre_counts = df['Genre'].value_counts().reset_index()
        genre_counts.columns = ['Genre', 'Count']
        fig2 = px.bar(genre_counts, y='Genre', x='Count', orientation='h', color='Count',
                      title="Genre Frequency", height=500)
        st.plotly_chart(fig2, use_container_width=True)

    # Q3. Highest Vote Average
    st.markdown("###  Q3. Highest Vote Average")
    edges = [df['Vote_Average'].min(),
             df['Vote_Average'].quantile(0.25),
             df['Vote_Average'].quantile(0.5),
             df['Vote_Average'].quantile(0.75),
             df['Vote_Average'].max()]

    labels = ['not_popular', 'below_avg', 'average', 'popular']
    df['Vote_Category'] = pd.cut(df['Vote_Average'], bins=edges, labels=labels, include_lowest=True)

    max_vote = df['Vote_Average'].max()
    top_movies = df[df['Vote_Average'] == max_vote]
    st.info(f" Highest vote average: {max_vote}")
    st.dataframe(top_movies[['Title', 'Vote_Average', 'Genre']])

    # Distribution Plot of Vote Categories
    fig3 = px.histogram(df, x='Vote_Category', color='Vote_Category',
                        title="Vote Average Categories Distribution")
    st.plotly_chart(fig3, use_container_width=True)

    # Q4 & Q5: Most and Least Popular Movies
    st.markdown("### Q4 & Q5. Movies by Popularity")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🔺 Most Popular Movie")
        most_popular = df[df['Popularity'] == df['Popularity'].max()]
        st.dataframe(most_popular[['Title', 'Popularity', 'Genre']])

    with col2:
        st.markdown("#### 🔻 Least Popular Movie")
        least_popular = df[df['Popularity'] == df['Popularity'].min()]
        st.dataframe(least_popular[['Title', 'Popularity', 'Genre']])

    # Bonus: Release Trend
    st.markdown("###  Bonus: Trend of Releases Over Years")
    year_counts = df['Release_Year'].value_counts().sort_index()
    fig4 = px.line(x=year_counts.index, y=year_counts.values, labels={'x': 'Year', 'y': 'Number of Releases'},
                   title="Number of Netflix Releases by Year")
    st.plotly_chart(fig4, use_container_width=True)

    # Search Option
    st.markdown("### 🔎 Search a Movie")
    search_query = st.text_input("Enter movie title or keyword:")
    if search_query:
        search_result = df[df['Title'].str.contains(search_query, case=False, na=False)]
        st.dataframe(search_result[['Title', 'Genre', 'Vote_Average', 'Popularity']])

else:
    st.warning("⚠️ Please upload a CSV file to continue.")