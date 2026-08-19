import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="Netflix Movies Analyzer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Custom styling
# ---------------------------------------------------------
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #1f1f1f 0%, #141414 100%);
        border: 1px solid #333;
        border-radius: 12px;
        padding: 18px 20px;
        text-align: center;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #E50914;
        margin: 0;
    }
    .kpi-label {
        font-size: 13px;
        color: #b3b3b3;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0;
    }
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #141414;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Banner
# ---------------------------------------------------------
try:
    st.image("netflix_banner.jpeg", use_container_width=True)
except Exception as e:
    st.warning(f"Banner image not found or could not be loaded: {e}")

st.title("🎬 Netflix Movies Data Analysis App")
st.markdown("""
Explore Netflix movies and TV shows data — genres, popularity, ratings, and release trends.
Use the sidebar to filter everything below by genre.
""")

CSV_PATH = "mymoviedb.csv"

@st.cache_data
def load_data(path):
    df = pd.read_csv(path, lineterminator='\n')
    return df

# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
try:
    df = load_data(CSV_PATH)
except Exception as e:
    st.error(f"Could not load '{CSV_PATH}': {e}")
    st.stop()

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

# ---------------------------------------------------------
# Sidebar filter
# ---------------------------------------------------------
st.sidebar.header("🔍 Filter Options")
unique_genres = sorted(df['Genre'].dropna().unique())
selected_genre = st.sidebar.selectbox("Select Genre to Filter", options=["All"] + unique_genres)

filtered_df = df if selected_genre == "All" else df[df['Genre'] == selected_genre]

if filtered_df.empty:
    st.warning(f"No data available for genre: {selected_genre}")
    st.stop()

st.sidebar.markdown(f"**{len(filtered_df):,}** rows match this filter")

# ---------------------------------------------------------
# KPI Row (reacts to genre filter)
# ---------------------------------------------------------
st.markdown(f"### 📊 Overview — {selected_genre}")
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-value">{filtered_df['Title'].nunique():,}</p>
        <p class="kpi-label">Titles</p>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-value">{filtered_df['Vote_Average'].mean():.2f}</p>
        <p class="kpi-label">Avg Vote</p>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-value">{filtered_df['Popularity'].mean():.0f}</p>
        <p class="kpi-label">Avg Popularity</p>
    </div>""", unsafe_allow_html=True)

with k4:
    top_year = int(filtered_df['Release_Year'].value_counts().idxmax()) if not filtered_df['Release_Year'].dropna().empty else "N/A"
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-value">{top_year}</p>
        <p class="kpi-label">Peak Release Year</p>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📈 Charts", "🏆 Top & Bottom", "🎞️ Titles in Genre", "🔎 Search"])

# ---------------- TAB 1: Charts ----------------
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Popularity Categories")
        pop_edges = [
            filtered_df['Popularity'].min(),
            filtered_df['Popularity'].quantile(0.25),
            filtered_df['Popularity'].quantile(0.5),
            filtered_df['Popularity'].quantile(0.75),
            filtered_df['Popularity'].max()
        ]
        pop_labels = ['not_popular', 'below_avg', 'average', 'popular']
        try:
            pop_cat = pd.cut(filtered_df['Popularity'], bins=pop_edges, labels=pop_labels, include_lowest=True, duplicates='drop')
            pop_counts = pop_cat.value_counts().reindex(pop_labels)
            fig1 = px.pie(
                names=pop_counts.index, values=pop_counts.values,
                color_discrete_sequence=px.colors.sequential.RdBu,
                title=f"Popularity Distribution — {selected_genre}",
                hole=0.35
            )
            fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig1, use_container_width=True)
        except ValueError:
            st.info("Not enough variation in popularity values to bucket for this genre.")

    with col2:
        st.markdown("#### Genre Frequency")
        genre_counts = df['Genre'].value_counts().reset_index()
        genre_counts.columns = ['Genre', 'Count']
        genre_counts['Highlight'] = genre_counts['Genre'].apply(
            lambda g: 'Selected' if g == selected_genre else 'Other'
        )
        fig2 = px.bar(
            genre_counts, y='Genre', x='Count', orientation='h',
            color='Highlight',
            color_discrete_map={'Selected': '#E50914', 'Other': '#4a4a4a'},
            title="Genre Frequency (across full dataset)", height=500
        )
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Vote Average Distribution")
    vote_edges = [
        filtered_df['Vote_Average'].min(),
        filtered_df['Vote_Average'].quantile(0.25),
        filtered_df['Vote_Average'].quantile(0.5),
        filtered_df['Vote_Average'].quantile(0.75),
        filtered_df['Vote_Average'].max()
    ]
    vote_labels = ['not_popular', 'below_avg', 'average', 'popular']
    try:
        vote_cat = pd.cut(filtered_df['Vote_Average'], bins=vote_edges, labels=vote_labels, include_lowest=True, duplicates='drop')
        fig3 = px.histogram(
            x=vote_cat, color=vote_cat,
            title=f"Vote Average Categories — {selected_genre}"
        )
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
    except ValueError:
        st.info("Not enough variation in vote averages to bucket for this genre.")

    st.markdown("#### Release Trend Over Years")
    year_counts = filtered_df['Release_Year'].value_counts().sort_index()
    fig4 = px.line(
        x=year_counts.index, y=year_counts.values,
        labels={'x': 'Year', 'y': 'Number of Releases'},
        title=f"Releases by Year — {selected_genre}"
    )
    fig4.update_traces(line_color='#E50914')
    fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig4, use_container_width=True)

# ---------------- TAB 2: Top & Bottom ----------------
with tab2:
    st.markdown(f"#### Highest Vote Average — {selected_genre}")
    max_vote = filtered_df['Vote_Average'].max()
    top_movies = filtered_df[filtered_df['Vote_Average'] == max_vote]
    st.info(f"Highest vote average: {max_vote}")
    st.dataframe(top_movies[['Title', 'Vote_Average', 'Genre']], use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🔺 Most Popular")
        most_popular = filtered_df[filtered_df['Popularity'] == filtered_df['Popularity'].max()]
        st.dataframe(most_popular[['Title', 'Popularity', 'Genre']], use_container_width=True)

    with col2:
        st.markdown("#### 🔻 Least Popular")
        least_popular = filtered_df[filtered_df['Popularity'] == filtered_df['Popularity'].min()]
        st.dataframe(least_popular[['Title', 'Popularity', 'Genre']], use_container_width=True)

# ---------------- TAB 3: Titles in selected genre ----------------
with tab3:
    st.markdown(f"#### All titles — {selected_genre} ({len(filtered_df):,} rows)")
    sort_col = st.selectbox("Sort by", options=['Popularity', 'Vote_Average', 'Release_Year', 'Title'], index=0)
    sort_dir = st.radio("Order", options=['Descending', 'Ascending'], horizontal=True)
    display_df = filtered_df.sort_values(
        by=sort_col, ascending=(sort_dir == 'Ascending')
    )[['Title', 'Genre', 'Release_Year', 'Vote_Average', 'Popularity']].drop_duplicates(subset='Title')
    st.dataframe(display_df, use_container_width=True, height=500)

# ---------------- TAB 4: Search ----------------
with tab4:
    st.markdown("#### 🔎 Search a Movie")
    search_query = st.text_input("Enter movie title or keyword:")
    search_scope = st.radio("Search within", options=[f"{selected_genre} only", "All genres"], horizontal=True)
    search_source = filtered_df if search_scope.startswith(selected_genre) else df
    if search_query:
        search_result = search_source[search_source['Title'].str.contains(search_query, case=False, na=False)]
        st.dataframe(
            search_result[['Title', 'Genre', 'Vote_Average', 'Popularity']].drop_duplicates(subset='Title'),
            use_container_width=True
        )
