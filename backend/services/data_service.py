import pandas as pd
from datetime import datetime
from difflib import get_close_matches

# Define file paths (relative to your project root)
MEASUREMENTS_FILE = '../Data/copernicus_data/hab_dashboard_data.csv'
EVENTS_FILE = '../Data/haedat_search.csv'

# Load both CSVs globally (only once at import time)
try:
    measurements_df = pd.read_csv(MEASUREMENTS_FILE)
except Exception as e:
    print("Error loading measurements data:", e)
    measurements_df = pd.DataFrame()

measurements_df.rename(columns={
    'sst': 'sea_surface_temperature',
    # add any other mappings here if needed
}, inplace=True)

try:
    events_df = pd.read_csv(EVENTS_FILE, encoding='latin1')
except Exception as e:
    print("Error loading events data:", e)
    events_df = pd.DataFrame()

# Parse dates once during load (more efficient)
if not measurements_df.empty:
    measurements_df['timestamp'] = pd.to_datetime(measurements_df['timestamp'], errors='coerce')

if not events_df.empty:
    events_df['initialDate'] = pd.to_datetime(events_df['initialDate'], errors='coerce')

def extract_measurements(site, start_date, end_date):
    # parse dates safely
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # filter rows for site + date range
    filtered = measurements_df[
        (measurements_df['site_name'] == site) &
        (measurements_df['timestamp'] >= start_date) &
        (measurements_df['timestamp'] <= end_date)
    ]

    # if no data found
    if filtered.empty:
        raise ValueError("No measurements found for given site and date range.")

    # select required columns
    filtered = filtered[[
        'timestamp',
        'latitude',
        'longitude',
        'chlorophyll_a',
        'sea_surface_temperature',
        'turbidity',
        'bloom_label',
        'bloom_probability'
    ]]

    # convert to list of dicts
    result = filtered.to_dict(orient='records')

    return result

# def get_event_count(site, start_date, end_date):
#     if events_df.empty:
#         return 0

#     start_date = pd.to_datetime(start_date)
#     end_date = pd.to_datetime(end_date)

#     filtered = events_df[
#         (events_df['locationText'] == site) &
#         (events_df['initialDate'] >= start_date) &
#         (events_df['initialDate'] <= end_date)
#     ]

#     return len(filtered)


def get_event_count(site, start_date, end_date):
    if events_df.empty:
        return 0

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Get unique locations from events_df
    unique_locations = events_df['locationText'].dropna().unique().tolist()

    # Fuzzy match the closest location
    match = get_close_matches(site, unique_locations, n=1, cutoff=0.6)

    if not match:
        return 0  # no close match found

    matched_site = match[0]

    # Filter by matched site and date range
    filtered = events_df[
        (events_df['locationText'] == matched_site) &
        (events_df['initialDate'] >= start_date) &
        (events_df['initialDate'] <= end_date)
    ]

    return len(filtered)

def get_all_sites_with_ranges():
    if measurements_df.empty:
        return []

    # Ensure timestamp is parsed
    measurements_df['timestamp'] = pd.to_datetime(measurements_df['timestamp'], errors='coerce')

    site_ranges = measurements_df.groupby('site_name')['timestamp'].agg(['min', 'max']).reset_index()

    result = []
    for _, row in site_ranges.iterrows():
        result.append({
            "site": row['site_name'],
            "start_date": row['min'].strftime('%Y-%m-%d'),
            "end_date": row['max'].strftime('%Y-%m-%d')
        })

    return result

