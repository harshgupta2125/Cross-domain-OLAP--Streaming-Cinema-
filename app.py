import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import data_source
import etl_engine

# App configuration and top-level text
st.set_page_config(page_title="Movie Cross-Domain OLAP", layout="wide")
st.title("🎬 Movie Analytics: Box Office vs. Streaming")
st.markdown("### Project: Cross-Domain OLAP (Real IMDb Data + Synthetic Streaming Data)")

# Load data
with st.spinner("Loading Data..."):
    df_imdb = data_source.get_imdb_data()
    if df_imdb.empty:
        st.error("❌ Could not find 'movies.csv'. Please add it to the folder.")
        st.stop()
    df_netflix = data_source.generate_netflix_data(df_imdb)

# Integrate datasets
df_main = etl_engine.perform_integration(df_imdb, df_netflix)

# Sidebar controls for slicing and dicing
st.sidebar.header("🎛️ OLAP Dimensions")
all_genres = df_main['Primary_Genre'].unique()
selected_genres = st.sidebar.multiselect("Filter by Genre", all_genres, default=all_genres[:5])
min_r, max_r = float(df_main['Rating'].min()), float(df_main['Rating'].max())
rating_range = st.sidebar.slider("Filter by IMDb Rating", min_r, max_r, (min_r, max_r))

# Apply filters
mask = (df_main['Primary_Genre'].isin(selected_genres)) & \
       (df_main['Rating'].between(rating_range[0], rating_range[1]))
df_filtered = df_main[mask]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Movies Analyzed", len(df_filtered))
col2.metric("Total Box Office", f"${df_filtered['Gross'].sum()/1e9:.2f} B")
col3.metric("Total Streaming Hours", f"{df_filtered['Total_Hours_Viewed'].sum()/1e6:.1f} M")
col4.metric("Avg IMDb Rating", f"{df_filtered['Rating'].mean():.1f}")

st.divider()

# Scatter and bar charts
c1, c2 = st.columns(2)

with c1:
    st.subheader("💰 Commercial Success vs. Streaming Popularity")
    st.markdown("*Does a high Box Office (Domain A) mean high Streaming Views (Domain B)?*")

    # base scatter
    fig_scatter = px.scatter(
        df_filtered,
        x="Gross",
        y="Total_Hours_Viewed",
        size="Rating" if "Rating" in df_filtered.columns else None,
        color="Primary_Genre",
        hover_name="Movie Name" if "Movie Name" in df_filtered.columns else None,
        log_x=True,
        title="Box Office vs. Streaming Hours (Size = Rating)"
    )

    # interactive selection: choose a movie to highlight
    movies_list = df_filtered["Movie Name"].dropna().unique().tolist() if "Movie Name" in df_filtered.columns else []
    selected_movie = st.selectbox("Select a movie to highlight on the chart", options=["(none)"] + movies_list)

    # when a movie is selected, add a highlighted marker + annotation
    if selected_movie and selected_movie != "(none)":
        sel = df_filtered[df_filtered["Movie Name"] == selected_movie]
        if not sel.empty:
            row = sel.iloc[0]
            xval = row.get("Gross", None)
            yval = row.get("Total_Hours_Viewed", None)
            if pd.notna(xval) and pd.notna(yval):
                fig_scatter.add_trace(
                    go.Scatter(
                        x=[xval],
                        y=[yval],
                        mode="markers+text",
                        marker=dict(size=20, color="red", symbol="star"),
                        text=[selected_movie],
                        textposition="top center",
                        name="Selected Movie",
                        hoverinfo="text"
                    )
                )
                fig_scatter.add_annotation(
                    x=xval,
                    y=yval,
                    text=f"{selected_movie}",
                    showarrow=True,
                    arrowhead=2,
                    ax=0,
                    ay=-40
                )

    st.plotly_chart(fig_scatter, use_container_width=True)

with c2:
    st.subheader("🏆 Genre Performance")
    df_grouped = etl_engine.get_genre_aggregation(df_filtered)
    fig_bar = go.Figure(data=[
        go.Bar(name='Box Office Gross', x=df_grouped['Primary_Genre'], y=df_grouped['Gross'], yaxis='y'),
        go.Bar(name='Streaming Hours', x=df_grouped['Primary_Genre'], y=df_grouped['Total_Hours_Viewed'], yaxis='y2')
    ])
    fig_bar.update_layout(
        title="Revenue vs. Views by Genre",
        yaxis=dict(title="Gross Revenue ($)"),
        yaxis2=dict(title="Hours Viewed", overlaying='y', side='right'),
        barmode='group'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Drill-down table with selection helper
with st.expander("🔍 View Integrated Data Warehouse Table"):
    if not df_filtered.empty:
        st.dataframe(df_filtered[['Movie Name', 'Primary_Genre', 'Rating', 'Gross', 'Total_Hours_Viewed', 'Revenue_Per_View_Hour']])
        st.markdown("Or pick a movie from the dropdown above to highlight it on the scatter.")
    else:
        st.info("No data to display for the selected filters.")