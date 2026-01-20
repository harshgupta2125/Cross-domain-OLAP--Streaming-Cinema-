import pandas as pd
import numpy as np
import re

def clean_currency(value):
    """
    Converts string currency (e.g., '$100M', '$50,000') to float.
    Returns 0.0 if data is missing or invalid.
    """
    if pd.isna(value) or value == '':
        return 0.0
    
    val_str = str(value).replace('$', '').replace(',', '').strip()
    try:
        if 'M' in val_str.upper():
            return float(val_str.upper().replace('M', '')) * 1_000_000
        return float(val_str)
    except:
        return 0.0

def get_imdb_data(filepath="movies.csv"):
    """
    Loads Domain A (Theatrical Data) with the NEW schema.
    """
    expected_cols = ["ID", "Movie Name", "Rating", "Runtime", "Genre", "Metascore", "Votes", "Gross", "Link"]

    # Try multiple parsing strategies to handle messy CSVs
    parsers = []
    try:
        parsers.append(("csv", pd.read_csv(filepath)))
    except Exception as e:
        parsers.append(("csv_err", e))

    try:
        import csv as _csv
        parsers.append(("tsv", pd.read_csv(filepath, sep='\t', engine='python', quoting=_csv.QUOTE_NONE, escapechar='\\')))
    except Exception as e:
        parsers.append(("tsv_err", e))

    try:
        parsers.append(("fwf", pd.read_fwf(filepath)))
    except Exception as e:
        parsers.append(("fwf_err", e))

    # Try a regex-split fallback if structured parsing failed
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [ln.rstrip('\n') for ln in f]
        header = lines[0]
        cols = re.split(r"\s{2,}", header.strip())
        rows = []
        for ln in lines[1:]:
            parts = re.split(r"\s{2,}", ln.strip())
            # Pad or trim to match header length
            if len(parts) < len(cols):
                parts += [''] * (len(cols) - len(parts))
            elif len(parts) > len(cols):
                parts = parts[:len(cols)]
            rows.append(parts)
        df_regex = pd.DataFrame(rows, columns=cols)
        parsers.append(("regex", df_regex))
    except Exception as e:
        parsers.append(("regex_err", e))

    # Select the first parser result that contains the expected cols (or at least 'Movie Name')
    df = None
    for name, result in parsers:
        if isinstance(result, pd.DataFrame):
            lower_cols = [c for c in result.columns]
            if 'Movie Name' in lower_cols or set(expected_cols).intersection(lower_cols):
                df = result
                parser_used = name
                break

    if df is None or df.empty:
        # Nothing worked
        print("Error loading IMDb data: could not parse file with available strategies")
        return pd.DataFrame()

    # Normalize column names if they differ slightly
    # Map common variants to expected names
    col_map = {}
    for c in df.columns:
        lc = c.strip()
        if lc.lower() == 'movie name':
            col_map[c] = 'Movie Name'
        if lc.lower() == 'votes':
            col_map[c] = 'Votes'
        if lc.lower() == 'gross':
            col_map[c] = 'Gross'
        if lc.lower() == 'rating':
            col_map[c] = 'Rating'
        if lc.lower() == 'genre':
            col_map[c] = 'Genre'
        if lc.lower() == 'runtime':
            col_map[c] = 'Runtime'
        if lc.lower() == 'id':
            col_map[c] = 'ID'
        if lc.lower() == 'metascore':
            col_map[c] = 'Metascore'
        if lc.lower() == 'link':
            col_map[c] = 'Link'

    df = df.rename(columns=col_map)

    # Ensure expected columns exist (add missing with defaults)
    for c in expected_cols:
        if c not in df.columns:
            df[c] = ''

    # 1. Clean Gross Revenue
    df["Gross"] = df["Gross"].apply(clean_currency)

    # 2. Clean Genre
    df["Primary_Genre"] = df["Genre"].astype(str).apply(lambda x: x.split(',')[0].strip())

    # 3. Clean Rating & Votes
    df["Rating"] = pd.to_numeric(df["Rating"], errors='coerce').fillna(0)
    df["Votes"] = pd.to_numeric(df["Votes"], errors='coerce').fillna(0)

    # 4. Filter out rows without movie name
    df = df.dropna(subset=["Movie Name"]) if "Movie Name" in df.columns else df
    df = df[df["Movie Name"] != ""]

    print(f"Loaded IMDb data using parser: {parser_used}; shape={df.shape}")
    return df

def generate_netflix_data(df_imdb):
    """
    Simulates Domain B (Streaming Data) using the NEW 'Votes' column 
    for higher accuracy simulation.
    """
    if df_imdb.empty:
        return pd.DataFrame()

    netflix_data = []
    
    for _, row in df_imdb.iterrows():
        if row["Votes"] > 1000: 
            if np.random.random() > 0.2: 
                base_views = row["Votes"] * np.random.uniform(5, 15)
                rating_boost = (row["Rating"] * 250_000)
                random_noise = np.random.normal(0, 100_000)
                total_hours = abs(base_views + rating_boost + random_noise)
                netflix_data.append({
                    "Movie_Name": row["Movie Name"].strip().lower(),
                    "Platform": "Netflix",
                    "Total_Hours_Viewed": int(total_hours),
                    "Available_Regions": np.random.randint(5, 190)
                })
    
    return pd.DataFrame(netflix_data)