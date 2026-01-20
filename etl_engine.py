import pandas as pd

def perform_integration(df_imdb, df_netflix):
    """
    Performs the Hash Inner Join between Theatrical (A) and Streaming (B).
    """
    # 1. Standardize Join Keys (Normalization)
    df_imdb["join_key"] = df_imdb["Movie Name"].astype(str).str.lower().str.strip()
    
    # 2. Perform Hash Inner Join
    merged_df = pd.merge(
        df_imdb, 
        df_netflix, 
        left_on="join_key", 
        right_on="Movie_Name", 
        how="inner"
    )
    
    # 3. Clean up the resulting schema
    merged_df = merged_df.drop(columns=["join_key", "Movie_Name"])
    
    # 4. Remove Duplicates (in case multiple matches found)
    merged_df = merged_df.drop_duplicates(subset=["ID"])
    
    # Derived metric: Revenue per streaming hour (safe division)
    merged_df["Revenue_Per_View_Hour"] = merged_df.apply(
        lambda x: (x.get("Gross", 0) / x.get("Total_Hours_Viewed", 1)) if x.get("Total_Hours_Viewed", 0) > 0 else 0,
        axis=1
    )

    return merged_df

def get_genre_aggregation(df):
    """
    OLAP Roll-Up Operation: Group by Genre
    """
    return df.groupby("Primary_Genre")[["Gross", "Total_Hours_Viewed", "Votes"]].mean().reset_index()