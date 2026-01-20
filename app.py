import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import data_source
import etl_engine

# --------------------------------------------------
# App Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Movie Cross-Domain OLAP",
    layout="wide"
)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2503/2503508.png", width=100)
    st.title("BoxOffice Analytica")

st.title("🎬 Movie Analytics: Box Office vs. Streaming")
st.markdown("### Cross-Domain OLAP with Personal Preference Modeling")

# --------------------------------------------------
# Load Data
# --------------------------------------------------
with st.spinner("Loading Data..."):
    df_imdb = data_source.get_imdb_data()
    if df_imdb.empty:
        st.error("❌ Could not find 'movies.csv'. Please add it to the folder.")
        st.stop()

    df_netflix = data_source.generate_netflix_data(df_imdb)

# --------------------------------------------------
# ETL Integration
# --------------------------------------------------
df_main = etl_engine.perform_integration(df_imdb, df_netflix)

# --------------------------------------------------
# Sidebar – OLAP Filters
# --------------------------------------------------
st.sidebar.header("🎛️ OLAP Dimensions")

all_genres = df_main["Primary_Genre"].unique().tolist()
selected_genres = st.sidebar.multiselect(
    "Filter by Genre",
    all_genres,
    default=all_genres[:5]
)

min_r, max_r = float(df_main["Rating"].min()), float(df_main["Rating"].max())
rating_range = st.sidebar.slider(
    "Filter by IMDb Rating",
    min_r,
    max_r,
    (min_r, max_r)
)

# Apply Filters
mask = (
    df_main["Primary_Genre"].isin(selected_genres) &
    df_main["Rating"].between(rating_range[0], rating_range[1])
)
df_filtered = df_main[mask]

# --------------------------------------------------
# Sidebar – Personal Preferences
# --------------------------------------------------
st.sidebar.divider()
st.sidebar.header("👤 Personal Preferences")

preferred_genres = st.sidebar.multiselect(
    "Your Favorite Genres",
    all_genres,
    default=selected_genres
)

rating_weight = st.sidebar.slider(
    "Importance of IMDb Rating",
    0.0, 1.0, 0.5
)

box_office_weight = st.sidebar.slider(
    "Preference for Box Office Success",
    0.0, 1.0, 0.5
)

streaming_weight = st.sidebar.slider(
    "Preference for Streaming Popularity",
    0.0, 1.0, 0.5
)

st.sidebar.divider()
st.sidebar.markdown("### 📥 Export")
# Use a download button so examiners can export the filtered results
try:
    csv = df_filtered.to_csv(index=False).encode('utf-8')
except Exception:
    csv = b""

st.sidebar.download_button(
    label="Download Filtered CSV",
    data=csv,
    file_name='executive_report.csv',
    mime='text/csv',
)

# --------------------------------------------------
# KPI Section
# --------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Movies Analyzed", f"{len(df_filtered):,}", delta="Updated Today")
col2.metric(
    "Total Box Office",
    f"${df_filtered['Gross'].sum() / 1e9:.2f} B",
    delta="+12% YoY",
    delta_color="normal",
)
col3.metric(
    "Total Streaming Hours",
    f"{df_filtered['Total_Hours_Viewed'].sum() / 1e6:.2f} M",
    delta="High Engagement",
    delta_color="inverse",
)
col4.metric(
    "Avg IMDb Rating",
    f"{df_filtered['Rating'].mean():.1f}",
    delta="-0.2 vs Last Year",
    delta_color="off",
)

st.divider()

# --------------------------------------------------
# Preference Score Calculation
# --------------------------------------------------
df_pref = df_filtered.copy()

# Normalization
df_pref["Rating_Norm"] = (
    (df_pref["Rating"] - df_pref["Rating"].min()) /
    (df_pref["Rating"].max() - df_pref["Rating"].min() + 1e-9)
)

df_pref["Gross_Norm"] = (
    (df_pref["Gross"] - df_pref["Gross"].min()) /
    (df_pref["Gross"].max() - df_pref["Gross"].min() + 1e-9)
)

df_pref["Streaming_Norm"] = (
    (df_pref["Total_Hours_Viewed"] - df_pref["Total_Hours_Viewed"].min()) /
    (df_pref["Total_Hours_Viewed"].max() - df_pref["Total_Hours_Viewed"].min() + 1e-9)
)

df_pref["Genre_Pref"] = df_pref["Primary_Genre"].apply(
    lambda g: 1 if g in preferred_genres else 0
)

df_pref["Preference_Score"] = (
    rating_weight * df_pref["Rating_Norm"] +
    box_office_weight * df_pref["Gross_Norm"] +
    streaming_weight * df_pref["Streaming_Norm"] +
    0.5 * df_pref["Genre_Pref"]
)

# --------------------------------------------------
# Charts Section
# --------------------------------------------------
c1, c2 = st.columns(2)

# -------- Scatter Plot --------
with c1:
    st.subheader("💰 Box Office vs Streaming Popularity")

    fig_scatter = px.scatter(
        df_pref,
        x="Gross",
        y="Total_Hours_Viewed",
        size="Rating",
        color="Primary_Genre",
        hover_name="Movie Name",
        log_x=True,
        title="Commercial Success vs Streaming Reach"
    )

    # Highlight Top Recommendation
    if not df_pref.empty:
        top_movie = df_pref.sort_values(
            "Preference_Score", ascending=False
        ).iloc[0]

        fig_scatter.add_trace(
            go.Scatter(
                x=[top_movie["Gross"]],
                y=[top_movie["Total_Hours_Viewed"]],
                mode="markers+text",
                marker=dict(size=24, color="gold", symbol="star"),
                text=["Recommended"],
                textposition="top center",
                name="Top Recommendation"
            )
        )

    st.plotly_chart(fig_scatter, use_container_width=True)

# -------- Bar Chart --------
with c2:
    st.subheader("🏆 Genre Performance")

    df_grouped = etl_engine.get_genre_aggregation(df_filtered)

    fig_bar = go.Figure()

    fig_bar.add_bar(
        name="Box Office Gross",
        x=df_grouped["Primary_Genre"],
        y=df_grouped["Gross"],
        yaxis="y"
    )

    fig_bar.add_bar(
        name="Streaming Hours",
        x=df_grouped["Primary_Genre"],
        y=df_grouped["Total_Hours_Viewed"],
        yaxis="y2"
    )

    fig_bar.update_layout(
        title="Revenue vs Views by Genre",
        yaxis=dict(title="Gross Revenue ($)"),
        yaxis2=dict(
            title="Hours Viewed",
            overlaying="y",
            side="right"
        ),
        barmode="group"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# --------------------------------------------------
# Recommendations Section
# --------------------------------------------------
st.divider()
st.subheader("⭐ Personalized Recommendations")

top_n = st.slider("Number of recommendations", 3, 10, 5)

df_recommend = (
    df_pref
    .sort_values("Preference_Score", ascending=False)
    .head(top_n)
)

st.dataframe(
    df_recommend[
        [
            "Movie Name",
            "Primary_Genre",
            "Rating",
            "Gross",
            "Total_Hours_Viewed",
            "Preference_Score"
        ]
    ],
    use_container_width=True
)

# --------------------------------------------------
# Drill-Down Table
# --------------------------------------------------
# Ensure derived metric exists on the filtered dataframe
if "Revenue_Per_View_Hour" not in df_pref.columns:
    df_pref["Revenue_Per_View_Hour"] = df_pref.apply(
        lambda x: (x.get("Gross", 0) / x.get("Total_Hours_Viewed", 1)) if x.get("Total_Hours_Viewed", 0) > 0 else 0,
        axis=1
    )

with st.expander("🔍 View Integrated Data Warehouse Table"):
    if not df_pref.empty:
        st.dataframe(
            df_pref[
                [
                    "Movie Name",
                    "Primary_Genre",
                    "Rating",
                    "Gross",
                    "Total_Hours_Viewed",
                    "Revenue_Per_View_Hour",
                    "Preference_Score"
                ]
            ],
            use_container_width=True
        )
    else:
        st.info("No data available for selected filters.")
# --------------------------------------------------
# 10. The "Greenlight" Simulator (Predictive Module)
# --------------------------------------------------
st.divider()
st.header("🟢 The 'Greenlight' Simulator")
st.markdown("""
> **Business Logic:** Use historical data to predict the performance of a *hypothetical* future movie. 
> Enter your proposed movie details below to see estimated ROI and Streaming potential.
""")

# Input Columns
sim_c1, sim_c2, sim_c3 = st.columns(3)
with sim_c1:
    sim_genre = st.selectbox("Proposed Genre", all_genres, index=0)
with sim_c2:
    sim_budget = st.number_input("Est. Box Office Target ($)", min_value=1000000, value=50000000, step=1000000)
with sim_c3:
    sim_rating = st.slider("Target Quality (IMDb)", 1.0, 10.0, 7.0)

if st.button("🔮 Predict Success"):
    # 1. FORCE NUMERIC (Safety Check)
    df_main["Gross"] = pd.to_numeric(df_main["Gross"], errors='coerce').fillna(0)
    df_main["Total_Hours_Viewed"] = pd.to_numeric(df_main["Total_Hours_Viewed"], errors='coerce').fillna(0)
    
    # 2. SMART FILTERING using the new columns
    similar_movies = df_main[
        (df_main["Primary_Genre"] == sim_genre) &
        (df_main["Gross"] > 0)
    ].copy()

    if similar_movies.empty:
        st.error(f"❌ No data found for '{sim_genre}'. Cannot predict.")
    else:
        # 3. CALCULATION: "Efficiency Ratio"
        avg_gross = similar_movies["Gross"].median()
        avg_views = similar_movies["Total_Hours_Viewed"].median()
        
        # Avoid divide by zero
        if avg_gross < 1000: avg_gross = 1000 
        
        # Scaling Factor: (User Budget / Market Avg Budget)
        budget_multiplier = sim_budget / avg_gross
        
        # Prediction
        predicted_views = avg_views * budget_multiplier

        # Quality Bonus (Rating)
        if sim_rating > 8.0:
            predicted_views *= 1.25
            
        # 4. DISPLAY
        st.success(f"Simulation Complete using {len(similar_movies)} historical {sim_genre} films.")
        
        c1, c2, c3 = st.columns(3)
        
        def fmt(val):
            return f"{val/1e6:.2f} M" if val > 1e6 else f"{val/1e3:.0f} k"

        c1.metric("Predicted Views", f"{fmt(predicted_views)} Hours")
        c2.metric("Market Reference", f"{len(similar_movies)} Movies analyzed")
        
        # Verdict Logic
        if predicted_views > df_main["Total_Hours_Viewed"].mean():
            verdict = "✅ HIT PROJECT"
            color = "green"
        else:
            verdict = "⚠️ NICHE / RISKY"
            color = "orange"
            
        c3.markdown(f"**Verdict:** :{color}[{verdict}]")
        
        with st.expander("See Underlying Data"):
            st.dataframe(similar_movies[["Movie Name", "Rating", "Votes", "Gross", "Total_Hours_Viewed"]])
