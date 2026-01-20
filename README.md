# Cross-domain-OLAP -- Streaming Cinema

**Cross-domain OLAP for Box Office & Streaming analytics**

This repository demonstrates a compact OLAP-enabled analytics application that integrates theatrical (box office) data with simulated streaming metrics to support analysis and simple predictive decisioning for hypothetical movies.

**Quick Start**
- **Install:** `pip install -r requirements.txt`
- **Run:** `streamlit run app.py`
- **Main files:** [app.py](app.py), [data_source.py](data_source.py), [etl_engine.py](etl_engine.py), [movies.csv](movies.csv)

**What this project does**
- **Integrates** theatrical and streaming data to form a unified `df_main` data warehouse table via `etl_engine.perform_integration()`.
- **Provides OLAP-style exploration** through the Streamlit UI in `app.py`: filters (slice/dice), aggregations (roll-up), and drill-down tables.
- **Offers a Greenlight Simulator** (predictive module) that uses historical nearest-neighbor logic and robust scaling to estimate streaming potential for hypothetical projects.

**How OLAP is implemented (concepts & operations)**
- **Dimensions:** Categorical attributes used for slicing and grouping: `Primary_Genre`, `Rating` (as a ranged dimension), `Platform` (simulated streaming platform), and time-like buckets if extended.
- **Measures:** Numeric metrics that are aggregated: `Gross` (box office), `Total_Hours_Viewed` (streaming engagement), `Votes`, and `Revenue_Per_View_Hour` (derived).
- **Slice & Dice (Filtering):** The sidebar in `app.py` allows multi-dimensional filtering (genre, rating ranges, personal preferences). Those filters produce `df_filtered`, the active cube slice.
- **Roll-up (Aggregation):** The function `etl_engine.get_genre_aggregation()` performs a roll-up by `Primary_Genre` to compare aggregated Gross and Hours Viewed across genres.
- **Drill-down:** Expanders and data tables in `app.py` present row-level detail from the selected slice so you can inspect the virtual star-schema rows.

**ETL & Data Cleaning (where and how)**
- `data_source.py`: Responsible for ingesting `movies.csv`, robust parsing (handles messy TSV-like inputs), cleaning currency (`Gross`), extracting `Primary_Genre`, and forcing numeric types for `Rating` and `Votes`. It also synthesizes streaming data (`generate_netflix_data`) using `Votes` and `Rating` heuristics.
- `etl_engine.py`: Normalizes join keys, performs an inner join between theatrical and streaming domains, computes `Revenue_Per_View_Hour`, and exposes `get_genre_aggregation()` for OLAP roll-up.

**Greenlight Simulator (Predictive Module)**
- Purpose: Give producers a quick, defensible estimate of streaming potential for a hypothetical movie.
- Workflow: the simulator finds comparable historical movies (by genre and rating or by genre fallback), computes market averages (median/mean depending on logic), scales predictions by the user's proposed budget, applies a quality boost for high target ratings, and returns a verdict (`GREENLIGHT`, `MODERATE`, `HIGH RISK`).
- Safety: The simulator contains checks to handle zero/missing `Gross` and numeric coercion to avoid `inf` or `NaN` results.

**Notes for presenters**
- Pitch line: "Most dashboards only look at the past. The Greenlight Simulator uses historical nearest-neighbors and market scaling to make an actionable forward-looking recommendation for producers."
- If asked about methodology: explain you use OLAP filtering to create comparable cohorts, then median-based scaling to avoid outlier bias and unit-switching for readable outputs.

**Extending the project**
- Replace the heuristic simulator with a trained model (e.g., KNN or regression) using the same cohort selection for features.
- Persist `df_main` into a small parquet file or SQLite DB for faster warm starts.
- Add automated tests for `data_source` parsing and `etl_engine` joins.

**Contact / License**
- This project is MIT-licensed (see `LICENSE`).

----
Generated: concise README describing OLAP operations, ETL flow, simulator, and run instructions.
