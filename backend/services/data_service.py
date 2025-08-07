import pandas as pd
from datetime import datetime
from difflib import get_close_matches
import logging
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL not found")

engine: Engine = create_engine(DATABASE_URL)

def load_measurements_data():
    QLIMIT = int(os.getenv("QLIMIT", 10000))
    try:
        logger.info("🔄 Loading measurements from DB...")
        df = pd.read_sql_query("""
            SELECT * FROM measurements 
            WHERE site_name IS NOT NULL 
            ORDER BY timestamp DESC 
            LIMIT %s
        """, engine, params=(QLIMIT,))
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        logger.info(f"✅ Loaded {len(df):,} measurement records")
        return df
    except Exception as e:
        logger.error(f"❌ Failed to load measurements: {e}")
        return pd.DataFrame()

def load_events_data():
    QLIMIT = int(os.getenv("QLIMIT", 10000))
    try:
        logger.info("🔄 Loading events from DB...")
        df = pd.read_sql_query("""
            SELECT * FROM hab_events 
            ORDER BY "initialDate" DESC 
            LIMIT %s
        """, engine, params=(QLIMIT,))
        df['initialDate'] = pd.to_datetime(df['initialDate'], errors='coerce')
        logger.info(f"✅ Loaded {len(df):,} event records")
        return df
    except Exception as e:
        logger.error(f"❌ Failed to load events: {e}")
        return pd.DataFrame()

measurements_df = load_measurements_data()
events_df = load_events_data()


def extract_measurements(site, start_date, end_date, limit=50000):
    start_time = time.perf_counter()
    logger.info(f"Extracting measurements for site: {site}, date range: {start_date} to {end_date}")

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    filtered = measurements_df[
        (measurements_df['site_name'] == site) &
        (measurements_df['timestamp'] >= start_date) &
        (measurements_df['timestamp'] <= end_date)
    ]

    logger.info(f"Found {len(filtered)} records after filtering")

    if filtered.empty:
        raise ValueError("No measurements found for given site and date range.")

    filtered = filtered.sort_values('timestamp', ascending=False)
    if len(filtered) > limit:
        logger.warning(f"Limiting to {limit} most recent records.")
        filtered = filtered.head(limit)

    desired_columns = [
        'timestamp', 'latitude', 'longitude', 'chlorophyll_a', 
        'sst', 'sea_surface_temperature', 'turbidity', 'salinity', 
        'wind_speed', 'wave_height', 'bloom_label', 'bloom_probability', 
        'risk_level', 'dataset_source', 'time_period', 'region'
    ]
    available_columns = [col for col in desired_columns if col in filtered.columns]
    filtered = filtered[available_columns]

    if 'sst' in filtered.columns and 'sea_surface_temperature' not in filtered.columns:
        filtered = filtered.rename(columns={'sst': 'sea_surface_temperature'})

    elapsed_time = time.perf_counter() - start_time
    logger.info(
        f"✅ extract_measurements() done: returned {len(filtered)} records "
        f"for site '{site}'; total time ~{elapsed_time:.3f}s"
    )

    return filtered.to_dict(orient='records')

def get_event_count(site, start_date, end_date):
    if events_df.empty:
        return 0

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    unique_locations = events_df['locationText'].dropna().unique().tolist()
    match = get_close_matches(site, unique_locations, n=1, cutoff=0.6)
    if not match:
        return 0

    matched_site = match[0]
    filtered = events_df[
        (events_df['locationText'] == matched_site) &
        (events_df['initialDate'] >= start_date) &
        (events_df['initialDate'] <= end_date)
    ]

    return len(filtered)

def get_all_sites_with_ranges():
    logger.info("Getting all sites with ranges...")
    start_time = time.perf_counter()

    if measurements_df.empty:
        logger.warning("Measurements dataframe is empty; returning []")
        return []

    named_sites = measurements_df[measurements_df['site_name'] != 'Open Water']
    sites_to_process = named_sites if len(named_sites) > 0 else measurements_df

    sites_to_process_clean = sites_to_process.dropna(subset=['timestamp'])
    grouping_columns = ['site_name']
    if 'region' in measurements_df.columns:
        grouping_columns.append('region')

    site_stats = sites_to_process_clean.groupby(grouping_columns, observed=True).agg({
        'timestamp': ['min', 'max', 'count'],
        'chlorophyll_a': ['mean'],
        'bloom_probability': 'mean',
        'latitude': 'mean',
        'longitude': 'mean'
    }).round(4)

    site_stats.columns = ['_'.join(col).strip() for col in site_stats.columns.values]
    site_stats = site_stats.reset_index()

    result = []
    skipped = 0
    for _, row in site_stats.iterrows():
        try:
            start_date = row['timestamp_min']
            end_date = row['timestamp_max']
            if pd.isna(start_date) or pd.isna(end_date):
                skipped += 1
                continue

            result.append({
                "site": row['site_name'],
                "region": row.get('region', 'Unknown'),
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "total_records": int(row['timestamp_count']),
                "avg_chlorophyll": float(row['chlorophyll_a_mean']),
                "avg_bloom_probability": float(row['bloom_probability_mean']),
                "dominant_risk_level": "medium",
                "primary_data_source": "satellite",
                "center_lat": float(row['latitude_mean']),
                "center_lon": float(row['longitude_mean'])
            })
        except Exception as e:
            skipped += 1
            logger.warning(f"Skipping site due to error: {e}")
            continue

    result.sort(key=lambda x: x['total_records'], reverse=True)

    elapsed_time = time.perf_counter() - start_time
    logger.info(f"✅ get_all_sites_with_ranges() done: returned {len(result)} sites (skipped {skipped}); total time ~{elapsed_time:.3f}s")

    return result

def get_site_summary_stats():
    start_time = time.perf_counter()
    logger.info("Computing site summary stats...")

    if measurements_df.empty:
        elapsed = time.perf_counter() - start_time
        logger.info(f"✅ get_site_summary_stats() done: dataframe empty; total time ~{elapsed:.3f}s")
        return {}

    # Safe date formatter (handles NaT)
    def _fmt(ts):
        return ts.strftime('%Y-%m-%d') if pd.notna(ts) else None

    total_records = len(measurements_df)
    unique_sites = measurements_df['site_name'].nunique()

    start_ts = measurements_df['timestamp'].min()
    end_ts = measurements_df['timestamp'].max()

    regions = (
        measurements_df['region'].value_counts().to_dict()
        if 'region' in measurements_df.columns else {}
    )
    data_sources = (
        measurements_df['dataset_source'].value_counts().to_dict()
        if 'dataset_source' in measurements_df.columns else {}
    )
    risk_distribution = (
        measurements_df['risk_level'].value_counts().to_dict()
        if 'risk_level' in measurements_df.columns else {}
    )

    chlorophyll = measurements_df['chlorophyll_a']
    summary = {
        "total_records": total_records,
        "unique_sites": unique_sites,
        "date_range": {
            "start": _fmt(start_ts),
            "end": _fmt(end_ts)
        },
        "regions": regions,
        "data_sources": data_sources,
        "risk_distribution": risk_distribution,
        "chlorophyll_stats": {
            "mean": float(chlorophyll.mean()),
            "median": float(chlorophyll.median()),
            "std": float(chlorophyll.std()),
            "min": float(chlorophyll.min()),
            "max": float(chlorophyll.max())
        }
    }

    elapsed = time.perf_counter() - start_time
    logger.info(
        f"✅ get_site_summary_stats() done: summarized {total_records} records across {unique_sites} sites; total time ~{elapsed:.3f}s"
    )
    return summary