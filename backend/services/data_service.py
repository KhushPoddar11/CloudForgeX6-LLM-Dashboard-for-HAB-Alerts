import pandas as pd
from datetime import datetime
from difflib import get_close_matches
import logging
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Optional: load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL not found")

engine: Engine = create_engine(DATABASE_URL)

# Load measurements from DB
def load_measurements_data():
    try:
        logger.info("🔄 Loading measurements from DB...")
        df = pd.read_sql_query("""
            SELECT * FROM measurements 
            WHERE site_name IS NOT NULL 
            ORDER BY timestamp DESC 
            LIMIT 100000
        """, engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        logger.info(f"✅ Loaded {len(df):,} measurement records")
        return df
    except Exception as e:
        logger.error(f"❌ Failed to load measurements: {e}")
        return pd.DataFrame()

# Load events from DB
def load_events_data():
    try:
        logger.info("🔄 Loading events from DB...")
        df = pd.read_sql_query("""
            SELECT * FROM hab_events 
            ORDER BY initialDate DESC 
            LIMIT 100000
        """, engine)
        df['initialDate'] = pd.to_datetime(df['initialDate'], errors='coerce')
        logger.info(f"✅ Loaded {len(df):,} event records")
        return df
    except Exception as e:
        logger.error(f"❌ Failed to load events: {e}")
        return pd.DataFrame()

# Load data at startup
measurements_df = load_measurements_data()
events_df = load_events_data()

# Your existing logic continues below (unchanged)

def extract_measurements(site, start_date, end_date, limit=100000):
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
    if measurements_df.empty:
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
    for _, row in site_stats.iterrows():
        try:
            start_date = row['timestamp_min']
            end_date = row['timestamp_max']
            if pd.isna(start_date) or pd.isna(end_date):
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
            logger.warning(f"Skipping site due to error: {e}")
            continue

    result.sort(key=lambda x: x['total_records'], reverse=True)
    return result

def get_site_summary_stats():
    if measurements_df.empty:
        return {}

    return {
        "total_records": len(measurements_df),
        "unique_sites": measurements_df['site_name'].nunique(),
        "date_range": {
            "start": measurements_df['timestamp'].min().strftime('%Y-%m-%d'),
            "end": measurements_df['timestamp'].max().strftime('%Y-%m-%d')
        },
        "regions": measurements_df['region'].value_counts().to_dict() if 'region' in measurements_df.columns else {},
        "data_sources": measurements_df['dataset_source'].value_counts().to_dict() if 'dataset_source' in measurements_df.columns else {},
        "risk_distribution": measurements_df['risk_level'].value_counts().to_dict() if 'risk_level' in measurements_df.columns else {},
        "chlorophyll_stats": {
            "mean": float(measurements_df['chlorophyll_a'].mean()),
            "median": float(measurements_df['chlorophyll_a'].median()),
            "std": float(measurements_df['chlorophyll_a'].std()),
            "min": float(measurements_df['chlorophyll_a'].min()),
            "max": float(measurements_df['chlorophyll_a'].max())
        }
    }
