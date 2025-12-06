"""
etl_engine.py

Integration and aggregation utilities.
Functions return DataFrames suitable for the dashboard.
"""
import pandas as pd

def perform_integration(df_imdb, df_netflix):
    """
    Merge IMDb and synthetic streaming data on 'Join_Key' and compute derived metrics.
    Returns empty DataFrame if inputs are empty.
    """
    if df_imdb.empty or df_netflix.empty:
        return pd.DataFrame()

    df_integrated = pd.merge(df_imdb, df_netflix, on='Join_Key', how='inner')

    df_integrated['Revenue_Per_View_Hour'] = df_integrated.apply(
        lambda x: x['Gross'] / x['Total_Hours_Viewed'] if x['Total_Hours_Viewed'] > 0 else 0, axis=1
    )

    return df_integrated

def get_genre_aggregation(df_integrated):
    """
    Aggregate Gross and Total_Hours_Viewed by Primary_Genre for visualization.
    """
    if 'Primary_Genre' not in df_integrated.columns:
        return pd.DataFrame()

    return df_integrated.groupby('Primary_Genre')[['Gross', 'Total_Hours_Viewed']].sum().reset_index()