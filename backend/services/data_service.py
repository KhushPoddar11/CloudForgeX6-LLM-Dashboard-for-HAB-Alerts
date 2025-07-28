import pandas as pd
from datetime import datetime
from difflib import get_close_matches
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEASUREMENTS_FILE = '../Data/copernicus_data/hab_dashboard_ENHANCED_data.csv'
EVENTS_FILE = '../Data/haedat_search.csv'

def load_measurements_data():
    """Load measurements data with optimizations for large files"""
    try:
        logger.info(f"Loading large dataset from {MEASUREMENTS_FILE}...")
        
        sample_df = pd.read_csv(MEASUREMENTS_FILE, nrows=5)
        logger.info(f"Dataset columns: {list(sample_df.columns)}")
        logger.info(f"Sample data:\n{sample_df}")
        
        chunk_size = 50000
        chunks = []
        
        dtype_dict = {
            'site_id': 'category',
            'site_name': 'category', 
            'region': 'category',
            'risk_level': 'category',
            'dataset_source': 'category',
            'time_period': 'category',
            'bloom_label': 'int8',
            'chlorophyll_a': 'float32',
            'sst': 'float32',
            'turbidity': 'float32',
            'salinity': 'float32',
            'wind_speed': 'float32',
            'wave_height': 'float32',
            'bloom_probability': 'float32',
            'latitude': 'float64',
            'longitude': 'float64'
        }
        
        actual_columns = sample_df.columns.tolist()
        filtered_dtype_dict = {k: v for k, v in dtype_dict.items() if k in actual_columns}
        
        logger.info(f"Using dtypes for columns: {list(filtered_dtype_dict.keys())}")
        
        for chunk in pd.read_csv(MEASUREMENTS_FILE, chunksize=chunk_size, dtype=filtered_dtype_dict):
            chunks.append(chunk)
            if len(chunks) % 20 == 0:  
                logger.info(f"Loaded {len(chunks)} chunks ({len(chunks) * chunk_size:,} records so far)")
        
        measurements_df = pd.concat(chunks, ignore_index=True)
        logger.info(f"Successfully loaded {len(measurements_df):,} total records")
        
        if 'site_name' in measurements_df.columns:
            unique_sites = measurements_df['site_name'].unique()
            logger.info(f"Unique sites found: {len(unique_sites)}")
            logger.info(f"Site names: {list(unique_sites)[:10]}...")  
            
            open_water_count = (measurements_df['site_name'] == 'Open Water').sum()
            named_sites_count = (measurements_df['site_name'] != 'Open Water').sum()
            logger.info(f"Open Water records: {open_water_count:,}")
            logger.info(f"Named site records: {named_sites_count:,}")
        
        return measurements_df
        
    except Exception as e:
        logger.error(f"Error loading measurements data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return pd.DataFrame()

def load_events_data():
    """Load events data"""
    try:
        events_df = pd.read_csv(EVENTS_FILE, encoding='latin1')
        logger.info(f"Loaded {len(events_df)} event records")
        return events_df
    except Exception as e:
        logger.error(f"Error loading events data: {e}")
        return pd.DataFrame()

logger.info("Initializing data service with enhanced dataset...")
measurements_df = load_measurements_data()
events_df = load_events_data()

if not measurements_df.empty:
    measurements_df['timestamp'] = pd.to_datetime(measurements_df['timestamp'], errors='coerce')
    logger.info(f"Date range: {measurements_df['timestamp'].min()} to {measurements_df['timestamp'].max()}")

if not events_df.empty:
    events_df['initialDate'] = pd.to_datetime(events_df['initialDate'], errors='coerce')

def extract_measurements(site, start_date, end_date, limit=1000):
    """Extract measurements with optimization for large datasets"""
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
        logger.warning(f"Large result set ({len(filtered)} rows). Limiting to {limit} most recent records.")
        filtered = filtered.head(limit)

    available_columns = []
    desired_columns = [
        'timestamp', 'latitude', 'longitude', 'chlorophyll_a', 
        'sst', 'sea_surface_temperature', 'turbidity', 'salinity', 
        'wind_speed', 'wave_height', 'bloom_label', 'bloom_probability', 
        'risk_level', 'dataset_source', 'time_period', 'region'
    ]
    
    for col in desired_columns:
        if col in filtered.columns:
            available_columns.append(col)
    
    logger.info(f"Available columns for export: {available_columns}")
    
    filtered = filtered[available_columns]
    
    if 'sst' in filtered.columns and 'sea_surface_temperature' not in filtered.columns:
        filtered = filtered.rename(columns={'sst': 'sea_surface_temperature'})

    result = filtered.to_dict(orient='records')
    logger.info(f"Returning {len(result)} measurement records for {site}")
    
    return result

def get_event_count(site, start_date, end_date):
    """Get event count (unchanged)"""
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
    """Get all sites with enhanced metadata - FIXED VERSION"""
    logger.info("Getting all sites with ranges...")
    
    if measurements_df.empty:
        logger.error("Measurements dataframe is empty!")
        return []

    logger.info(f"Total measurements in dataframe: {len(measurements_df)}")
    
    named_sites = measurements_df[measurements_df['site_name'] != 'Open Water']
    logger.info(f"Named sites (excluding Open Water): {len(named_sites)} records")
    
    if len(named_sites) == 0:
        logger.warning("No named sites found! Only 'Open Water' records available.")
        
        sites_to_process = measurements_df
    else:
        sites_to_process = named_sites

    try:
        grouping_columns = ['site_name']
        if 'region' in measurements_df.columns:
            grouping_columns.append('region')
        
        sites_to_process_clean = sites_to_process.dropna(subset=['timestamp'])
        logger.info(f"After removing NaT timestamps: {len(sites_to_process_clean)} records")
        
        if sites_to_process_clean.empty:
            logger.error("No valid timestamps found!")
            return []
        
        site_stats = sites_to_process_clean.groupby(grouping_columns, observed=True).agg({
            'timestamp': ['min', 'max', 'count'],
            'chlorophyll_a': ['mean', 'std', 'min', 'max'],
            'bloom_probability': 'mean',
            'latitude': 'mean',
            'longitude': 'mean'
        }).round(4)

        site_stats.columns = ['_'.join(col).strip() for col in site_stats.columns.values]
        site_stats = site_stats.reset_index()
        
        logger.info(f"Site stats columns: {list(site_stats.columns)}")
        logger.info(f"Site stats shape: {site_stats.shape}")

        result = []
        for _, row in site_stats.iterrows():
            try:
                start_date = row['timestamp_min']
                end_date = row['timestamp_max']
                
                if pd.isna(start_date) or pd.isna(end_date):
                    logger.warning(f"Skipping site {row['site_name']} due to invalid timestamps")
                    continue
                
                site_info = {
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
                }
                result.append(site_info)
                
            except Exception as e:
                logger.warning(f"Skipping site {row.get('site_name', 'unknown')} due to error: {e}")
                continue

        result.sort(key=lambda x: x['total_records'], reverse=True)
        
        logger.info(f"Successfully returning {len(result)} sites with enhanced metadata")
        if result:
            logger.info(f"Sample site: {result[0]['site']} with {result[0]['total_records']} records")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in site grouping: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []
def get_site_summary_stats():
    """Get summary statistics for the enhanced dataset"""
    if measurements_df.empty:
        return {}
    
    try:
        unique_sites = measurements_df['site_name'].nunique()
        stats = {
            "total_records": len(measurements_df),
            "unique_sites": unique_sites,
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
        
        logger.info(f"Summary stats generated successfully: {unique_sites} sites, {len(measurements_df):,} records")
        return stats
    except Exception as e:
        logger.error(f"Error generating summary stats: {e}")
        return {"error": str(e)}

if not measurements_df.empty:
    logger.info("Enhanced Dataset Loaded Successfully!")
    logger.info(f"Total records: {len(measurements_df):,}")
    logger.info(f"Unique sites: {measurements_df['site_name'].nunique()}")
    if 'region' in measurements_df.columns:
        logger.info(f"Regions: {list(measurements_df['region'].unique())}")
    logger.info(f"Date range: {measurements_df['timestamp'].min()} to {measurements_df['timestamp'].max()}")
    logger.info(f"Memory usage: {measurements_df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
else:
    logger.error("Failed to load dataset!")