"""
data_source.py

Contains functions to load real IMDb data and generate synthetic streaming data.
Minimal inline comments; function docstrings explain behavior.
"""
import pandas as pd
import numpy as np

def get_imdb_data():
    """
    Load IMDb data from 'Movies.csv' and perform basic cleaning / column standardization.
    Returns an empty DataFrame on FileNotFoundError.
    """
    try:
        df = pd.read_csv('Movies.csv')

        if 'Gross' in df.columns:
            df['Gross'] = df['Gross'].astype(str).str.replace(r'[$,M]', '', regex=True)
            df['Gross'] = pd.to_numeric(df['Gross'], errors='coerce').fillna(0) * 1_000_000

        if 'Runtime' in df.columns:
            df['Runtime'] = df['Runtime'].astype(str).str.replace(' min', '')
            df['Runtime'] = pd.to_numeric(df['Runtime'], errors='coerce')

        if 'Genre' in df.columns:
            df['Primary_Genre'] = df['Genre'].astype(str).str.split(',').str[0].str.strip()
        else:
            df['Primary_Genre'] = 'Unknown'

        if 'Movie Name' in df.columns:
            df['Join_Key'] = df['Movie Name'].astype(str).str.lower().str.strip()

        return df
    except FileNotFoundError:
        return pd.DataFrame()

def generate_netflix_data(imdb_df):
    """
    Generate synthetic streaming metrics for movies present in the IMDb DataFrame.
    """
    if imdb_df.empty:
        return pd.DataFrame()

    movies = imdb_df[['Movie Name', 'Join_Key', 'Rating']].drop_duplicates()
    generated_data = []
    np.random.seed(42)

    for index, row in movies.iterrows():
        base_views = np.random.randint(100_000, 5_000_000)
        rating_multiplier = 1.0
        if pd.notnull(row['Rating']) and row['Rating'] > 8.0:
            rating_multiplier = np.random.uniform(1.5, 3.0)
        final_views = int(base_views * rating_multiplier)

        generated_data.append({
            'Join_Key': row['Join_Key'],
            'Streaming_Platform': np.random.choice(['Netflix', 'Hulu', 'Prime']),
            'Total_Hours_Viewed': final_views,
            'Weeks_in_Top_10': np.random.randint(0, 15)
        })

    return pd.DataFrame(generated_data)