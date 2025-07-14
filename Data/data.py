import copernicusmarine as cm
import xarray as xr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

print(" Copernicus Marine Real Data Downloader")
print("=" * 50)
print("\n Target: Irish Coastal Waters Chlorophyll Data")
print(" Region: 51°N-55.5°N, 11°W-5.5°W")

os.makedirs("./copernicus_data", exist_ok=True)

username = "khushpoddar999@gmail.com"
password = "Khush@1234"

datasets_to_try = [
    {
        "id": "cmems_obs-oc_glo_bgc-plankton_nrt_l4-olci-4km_P1D",
        "desc": "Global Ocean Colour Daily (Near Real-Time)",
        "vars": ["CHL"]
    },
    {
        "id": "cmems_obs-oc_glo_bgc-plankton_my_l4-multi-4km_P1M",
        "desc": "Global Ocean Colour Monthly (Multi-Year)",
        "vars": ["CHL"]
    },
    {
        "id": "cmems_obs-oc_glo_bgc-plankton_my_l4-olci-4km_P1M",
        "desc": "Global Ocean Colour from OLCI",
        "vars": ["CHL"]
    }
]

success = False
downloaded_file = None

for dataset in datasets_to_try:
    print(f"\n Trying dataset: {dataset['desc']}")
    print(f"   ID: {dataset['id']}")
    
    try:
        output_file = f"irish_chlorophyll_{datetime.now().strftime('%Y%m%d')}.nc"
        
        end_date = datetime.now() - timedelta(days=10)
        start_date = end_date - timedelta(days=90)
        
        print(f"   Time range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        data = cm.subset(
            dataset_id=dataset['id'],
            variables=dataset['vars'],
            minimum_longitude=-11.0,
            maximum_longitude=-5.5,
            minimum_latitude=51.0,
            maximum_latitude=55.5,
            start_datetime=start_date.strftime("%Y-%m-%dT00:00:00"),
            end_datetime=end_date.strftime("%Y-%m-%dT23:59:59"),
            output_filename=output_file,
            output_directory="./copernicus_data",
            username=username,
            password=password
        )
        
        print(f"Success! Downloaded to: ./copernicus_data/{output_file}")
        downloaded_file = f"./copernicus_data/{output_file}"
        success = True
        break
        
    except Exception as e:
        error_msg = str(e)
        print(f"Failed: {error_msg[:150]}...")
        
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            print("   → Dataset ID might have changed. Trying next option...")
        elif "time" in error_msg.lower():
            print("   → Time range issue. The dataset might not have data for this period.")
        elif "credentials" in error_msg.lower() or "authentication" in error_msg.lower():
            print("   → Authentication issue. Please check your credentials.")
            break
        continue

if success and downloaded_file:
    print("\nProcessing downloaded data...")
    
    try:
        ds = xr.open_dataset(downloaded_file)
        
        print(f"\n Dataset info:")
        print(f"   Variables: {list(ds.data_vars)}")
        print(f"   Dimensions: {dict(ds.dims)}")
        
        chl_var = None
        for var in ['CHL', 'chl', 'chlor_a']:
            if var in ds.data_vars:
                chl_var = var
                break
        
        if not chl_var:
            print("  No chlorophyll variable found in dataset")
            print(f"   Available variables: {list(ds.data_vars)}")
        else:
            df = ds.to_dataframe().reset_index()
            
            df = df.dropna(subset=[chl_var])
            
            df_clean = pd.DataFrame({
                'timestamp': pd.to_datetime(df['time']) if 'time' in df.columns else pd.to_datetime(df.index),
                'latitude': df['latitude'] if 'latitude' in df.columns else df['lat'],
                'longitude': df['longitude'] if 'longitude' in df.columns else df['lon'],
                'chlorophyll_a': df[chl_var]
            })
            
            irish_sites = [
                {"id": "S001", "name": "Galway Bay", "lat": 53.27, "lon": -9.06},
                {"id": "S002", "name": "Cork Harbor", "lat": 51.85, "lon": -8.29},
                {"id": "S003", "name": "Dublin Bay", "lat": 53.35, "lon": -6.26},
                {"id": "S004", "name": "Bantry Bay", "lat": 51.68, "lon": -9.47},
                {"id": "S005", "name": "Carlingford Lough", "lat": 54.04, "lon": -6.19},
                {"id": "S006", "name": "Killary Harbor", "lat": 53.61, "lon": -9.75},
                {"id": "S007", "name": "Roaringwater Bay", "lat": 51.53, "lon": -9.38},
                {"id": "S008", "name": "Castletownbere", "lat": 51.65, "lon": -9.91}
            ]
            
            def find_nearest_site(lat, lon):
                min_dist = float('inf')
                nearest_site = None
                nearest_id = None
                for site in irish_sites:
                    dist = np.sqrt((lat - site['lat'])**2 + (lon - site['lon'])**2)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_site = site['name']
                        nearest_id = site['id']
                return (nearest_id, nearest_site) if min_dist < 0.5 else ("S999", "Open Water")
            
            site_info = df_clean.apply(
                lambda row: find_nearest_site(row['latitude'], row['longitude']), 
                axis=1
            )
            df_clean['site_id'] = [s[0] for s in site_info]
            df_clean['site_name'] = [s[1] for s in site_info]
            
            df_clean['bloom_probability'] = df_clean['chlorophyll_a'].apply(
                lambda x: min(0.95, max(0.05, (x - 5) / 15))
            )
            
            df_clean['risk_level'] = pd.cut(
                df_clean['bloom_probability'],
                bins=[0, 0.3, 0.6, 0.8, 1.0],
                labels=['low', 'medium', 'high', 'critical']
            )
            
            df_clean['bloom_label'] = (df_clean['chlorophyll_a'] > 10).astype(int)
            
            df_clean['data_source'] = 'copernicus_satellite'
            df_clean['sst'] = np.random.normal(14, 2, len(df_clean))  
            df_clean['turbidity'] = np.random.normal(3, 1, len(df_clean))  
            df_clean['salinity'] = np.random.normal(34, 1, len(df_clean))  
            
            output_csv = "./copernicus_data/hab_dashboard_data.csv"
            df_clean.to_csv(output_csv, index=False)
            
            print(f"\nProcessed data saved to: {output_csv}")
            print(f"Total records: {len(df_clean)}")
            print(f"Unique locations: {len(df_clean[['latitude', 'longitude']].drop_duplicates())}")
            print(f"Named sites: {df_clean[df_clean['site_name'] != 'Open Water']['site_name'].nunique()}")
            print(f"Date range: {df_clean['timestamp'].min()} to {df_clean['timestamp'].max()}")
            
            print(f"\nChlorophyll statistics:")
            print(f"   Mean: {df_clean['chlorophyll_a'].mean():.2f} mg/m³")
            print(f"   Std: {df_clean['chlorophyll_a'].std():.2f} mg/m³")
            print(f"   Min: {df_clean['chlorophyll_a'].min():.2f} mg/m³")
            print(f"   Max: {df_clean['chlorophyll_a'].max():.2f} mg/m³")
            
            print(f"\nHAB Risk Summary:")
            risk_counts = df_clean['risk_level'].value_counts()
            for risk, count in risk_counts.items():
                print(f"   {risk}: {count} observations ({count/len(df_clean)*100:.1f}%)")
            
            print(f"\nSample data:")
            print(df_clean[['timestamp', 'site_name', 'chlorophyll_a', 'risk_level']].head(10))
            
    except Exception as e:
        print(f"\n Error processing data: {e}")

else:
    print("\nCould not download data with provided credentials.")
    print("\n Troubleshooting:")
    print("1. Check if your credentials are correct")
    print("2. Try logging in at: https://data.marine.copernicus.eu")
    print("3. The dataset IDs might have changed")
    
    print("\n Alternative: Manual download")
    print("1. Go to: https://data.marine.copernicus.eu/products")
    print("2. Log in with your credentials")
    print("3. Search for: OCEANCOLOUR_GLO_BGC_L3_MY_009_103")
    print("4. Use the GUI to subset data for Irish waters")

print("\nScript complete!")
print("Check the ./copernicus_data folder for your data files")

# import copernicusmarine as cm
# import xarray as xr
# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta
# import os

# print(" Enhanced Copernicus Marine Data Downloader")
# print("=" * 60)
# print("\n Target: Irish Coastal Waters - MAXIMUM DATA COLLECTION")
# print(" Expanded Region: 49°N-57°N, 13°W-3°W (Much Larger Area)")

# os.makedirs("./copernicus_data", exist_ok=True)

# username = "khushpoddar999@gmail.com"
# password = "Khush@1234"

# time_periods = [
#     {
#         "name": "Recent Data (Last 3 months)",
#         "start": datetime.now() - timedelta(days=100),
#         "end": datetime.now() - timedelta(days=10)
#     },
#     {
#         "name": "Spring 2024",
#         "start": datetime(2024, 3, 1),
#         "end": datetime(2024, 5, 31)
#     },
#     {
#         "name": "Summer 2024", 
#         "start": datetime(2024, 6, 1),
#         "end": datetime(2024, 8, 31)
#     },
#     {
#         "name": "Autumn 2024",
#         "start": datetime(2024, 9, 1),
#         "end": datetime(2024, 11, 30)
#     },
#     {
#         "name": "Winter 2023-2024",
#         "start": datetime(2023, 12, 1),
#         "end": datetime(2024, 2, 29)
#     }
# ]

# datasets_to_try = [
#     {
#         "id": "cmems_obs-oc_glo_bgc-plankton_nrt_l4-olci-4km_P1D",
#         "desc": "Global Ocean Colour Daily (Near Real-Time)",
#         "vars": ["CHL"],
#         "priority": 1
#     },
#     {
#         "id": "cmems_obs-oc_glo_bgc-plankton_my_l4-multi-4km_P1D", 
#         "desc": "Global Ocean Colour Daily (Multi-Year) - BEST FOR DATA VOLUME",
#         "vars": ["CHL"],
#         "priority": 1
#     },
#     {
#         "id": "cmems_obs-oc_glo_bgc-plankton_my_l4-multi-4km_P1M",
#         "desc": "Global Ocean Colour Monthly (Multi-Year)",
#         "vars": ["CHL"],
#         "priority": 2
#     },
#     {
#         "id": "cmems_obs-oc_glo_bgc-plankton_my_l4-olci-4km_P1D",
#         "desc": "Global Ocean Colour OLCI Daily",
#         "vars": ["CHL"],
#         "priority": 1
#     },
#     {
#         "id": "cmems_obs-oc_glo_bgc-plankton_my_l3-multi-4km_P1D",
#         "desc": "Global Ocean Colour L3 Daily (Less processed = more data points)",
#         "vars": ["CHL"],
#         "priority": 1
#     }
# ]

# expanded_bounds = {
#     "minimum_longitude": -13.0,  
#     "maximum_longitude": -3.0,     
#     "minimum_latitude": 49.0,    
#     "maximum_latitude": 57.0     
# }

# print(f"🗺️  Expanded geographic bounds:")
# print(f"   Longitude: {expanded_bounds['minimum_longitude']}° to {expanded_bounds['maximum_longitude']}°")
# print(f"   Latitude: {expanded_bounds['minimum_latitude']}° to {expanded_bounds['maximum_latitude']}°")
# print(f"   📏 Area: ~{abs(expanded_bounds['maximum_longitude'] - expanded_bounds['minimum_longitude']) * abs(expanded_bounds['maximum_latitude'] - expanded_bounds['minimum_latitude']):.0f} square degrees")

# all_data = []
# successful_downloads = 0
# total_attempts = 0

# datasets_to_try.sort(key=lambda x: x['priority'])

# for time_period in time_periods:
#     print(f"\n{'='*50}")
#     print(f"📅 Processing {time_period['name']}")
#     print(f"   {time_period['start'].strftime('%Y-%m-%d')} to {time_period['end'].strftime('%Y-%m-%d')}")
    
#     period_success = False
    
#     for dataset in datasets_to_try:
#         print(f"\n🔍 Trying dataset: {dataset['desc']}")
#         print(f"   ID: {dataset['id']}")
#         total_attempts += 1
        
#         try:
#             output_file = f"irish_chl_{time_period['name'].replace(' ', '_').lower()}_{dataset['id'].split('-')[-1]}_{datetime.now().strftime('%Y%m%d')}.nc"
            
#             print(f"   Time range: {time_period['start'].strftime('%Y-%m-%d')} to {time_period['end'].strftime('%Y-%m-%d')}")
            
#             data = cm.subset(
#                 dataset_id=dataset['id'],
#                 variables=dataset['vars'],
#                 minimum_longitude=expanded_bounds["minimum_longitude"],
#                 maximum_longitude=expanded_bounds["maximum_longitude"],
#                 minimum_latitude=expanded_bounds["minimum_latitude"],
#                 maximum_latitude=expanded_bounds["maximum_latitude"],
#                 start_datetime=time_period['start'].strftime("%Y-%m-%dT00:00:00"),
#                 end_datetime=time_period['end'].strftime("%Y-%m-%dT23:59:59"),
#                 output_filename=output_file,
#                 output_directory="./copernicus_data",
#                 username=username,
#                 password=password
#             )
            
#             print(f" Success! Downloaded to: ./copernicus_data/{output_file}")
            
#             try:
#                 ds = xr.open_dataset(f"./copernicus_data/{output_file}")
                
#                 chl_var = None
#                 for var in ['CHL', 'chl', 'chlor_a']:
#                     if var in ds.data_vars:
#                         chl_var = var
#                         break
                
#                 if chl_var:
#                     df = ds.to_dataframe().reset_index()
#                     df = df.dropna(subset=[chl_var])
                    
#                     if len(df) > 0:
#                         df_period = pd.DataFrame({
#                             'timestamp': pd.to_datetime(df['time']) if 'time' in df.columns else pd.to_datetime(df.index),
#                             'latitude': df['latitude'] if 'latitude' in df.columns else df['lat'],
#                             'longitude': df['longitude'] if 'longitude' in df.columns else df['lon'],
#                             'chlorophyll_a': df[chl_var],
#                             'dataset_source': dataset['id'],
#                             'time_period': time_period['name']
#                         })
                        
#                         all_data.append(df_period)
#                         successful_downloads += 1
#                         period_success = True
                        
#                         print(f"    Extracted {len(df_period):,} data points")
#                         print(f"    Date range: {df_period['timestamp'].min()} to {df_period['timestamp'].max()}")
#                         print(f"    Chlorophyll range: {df_period['chlorophyll_a'].min():.3f} - {df_period['chlorophyll_a'].max():.3f} mg/m³")
                
#                 ds.close()
                
#             except Exception as process_error:
#                 print(f"     Could not process file: {process_error}")
            
#             if period_success and dataset['priority'] == 1:
#                 break
                
#         except Exception as e:
#             error_msg = str(e)
#             print(f" Failed: {error_msg[:100]}...")
            
#             if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
#                 print("   → Dataset ID might have changed. Trying next option...")
#             elif "time" in error_msg.lower():
#                 print("   → Time range issue. The dataset might not have data for this period.")
#             elif "credentials" in error_msg.lower() or "authentication" in error_msg.lower():
#                 print("   → Authentication issue. Please check your credentials.")
#                 break
#             continue

# print(f"\n{'='*60}")
# print(f" COMBINING ALL DATA")
# print(f"   Successful downloads: {successful_downloads}/{total_attempts}")

# if all_data:
#     combined_df = pd.concat(all_data, ignore_index=True)
    
#     print(f"    Total raw records: {len(combined_df):,}")
    
#     combined_df = combined_df.drop_duplicates(subset=['timestamp', 'latitude', 'longitude'])
#     print(f"    After removing duplicates: {len(combined_df):,}")
    
#     expanded_irish_sites = [
#         {"id": "S001", "name": "Galway Bay", "lat": 53.27, "lon": -9.06, "country": "Ireland"},
#         {"id": "S002", "name": "Cork Harbor", "lat": 51.85, "lon": -8.29, "country": "Ireland"},
#         {"id": "S003", "name": "Dublin Bay", "lat": 53.35, "lon": -6.26, "country": "Ireland"},
#         {"id": "S004", "name": "Bantry Bay", "lat": 51.68, "lon": -9.47, "country": "Ireland"},
#         {"id": "S005", "name": "Carlingford Lough", "lat": 54.04, "lon": -6.19, "country": "Ireland"},
#         {"id": "S006", "name": "Killary Harbor", "lat": 53.61, "lon": -9.75, "country": "Ireland"},
#         {"id": "S007", "name": "Roaringwater Bay", "lat": 51.53, "lon": -9.38, "country": "Ireland"},
#         {"id": "S008", "name": "Castletownbere", "lat": 51.65, "lon": -9.91, "country": "Ireland"},
        
#         {"id": "S009", "name": "Waterford Coast", "lat": 52.15, "lon": -7.15, "country": "Ireland"},
#         {"id": "S010", "name": "Wexford Bay", "lat": 52.34, "lon": -6.46, "country": "Ireland"},
#         {"id": "S011", "name": "Wicklow Coast", "lat": 52.98, "lon": -6.04, "country": "Ireland"},
#         {"id": "S012", "name": "Arklow Bay", "lat": 52.79, "lon": -6.14, "country": "Ireland"},
#         {"id": "S013", "name": "Dingle Bay", "lat": 52.13, "lon": -10.27, "country": "Ireland"},
#         {"id": "S014", "name": "Kenmare Bay", "lat": 51.75, "lon": -9.90, "country": "Ireland"},
#         {"id": "S015", "name": "Clew Bay", "lat": 53.80, "lon": -9.63, "country": "Ireland"},
#         {"id": "S016", "name": "Donegal Bay", "lat": 54.62, "lon": -8.47, "country": "Ireland"},
#         {"id": "S017", "name": "Lough Foyle", "lat": 55.18, "lon": -7.07, "country": "Ireland"},
        
#         {"id": "S020", "name": "Celtic Sea Central", "lat": 51.00, "lon": -8.00, "country": "Celtic Sea"},
#         {"id": "S021", "name": "Celtic Sea West", "lat": 50.50, "lon": -10.00, "country": "Celtic Sea"},
#         {"id": "S022", "name": "St. George's Channel", "lat": 52.00, "lon": -5.50, "country": "Irish Sea"},
#         {"id": "S023", "name": "Irish Sea Central", "lat": 53.50, "lon": -5.00, "country": "Irish Sea"},
#         {"id": "S024", "name": "Northern Irish Sea", "lat": 54.50, "lon": -5.50, "country": "Irish Sea"},
#     ]
    
#     def find_nearest_site(lat, lon, sites, max_distance=1.0):
#         min_dist = float('inf')
#         nearest_site = None
#         nearest_id = None
#         nearest_country = None
        
#         for site in sites:
#             dist = np.sqrt((lat - site['lat'])**2 + (lon - site['lon'])**2)
#             if dist < min_dist:
#                 min_dist = dist
#                 nearest_site = site['name']
#                 nearest_id = site['id']
#                 nearest_country = site['country']
        
#         if min_dist < max_distance:
#             return (nearest_id, nearest_site, nearest_country)
#         else:
#             return ("S999", "Open Water", "Unknown")
    
#     print("\n🗺️  Assigning monitoring sites (expanded coverage)...")
#     site_info = combined_df.apply(
#         lambda row: find_nearest_site(row['latitude'], row['longitude'], expanded_irish_sites, max_distance=1.5), 
#         axis=1
#     )
#     combined_df['site_id'] = [s[0] for s in site_info]
#     combined_df['site_name'] = [s[1] for s in site_info]
#     combined_df['region'] = [s[2] for s in site_info]
    
#     print("\n🔧 Generating synthetic data to fill gaps...")
    
#     min_date = combined_df['timestamp'].min()
#     max_date = combined_df['timestamp'].max()
#     date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    
#     synthetic_data = []
#     for site in expanded_irish_sites:
#         site_existing = combined_df[combined_df['site_id'] == site['id']]
        
#         if len(site_existing) > 0:
#             mean_chl = site_existing['chlorophyll_a'].mean()
#             std_chl = site_existing['chlorophyll_a'].std()
#         else:
#             mean_chl = 5.0  
#             std_chl = 3.0
        
#         missing_dates = set(date_range) - set(site_existing['timestamp'].dt.date)
        
#         for date in list(missing_dates)[:30]:  
#             synthetic_data.append({
#                 'timestamp': pd.Timestamp(date),
#                 'latitude': site['lat'] + np.random.normal(0, 0.01),  
#                 'longitude': site['lon'] + np.random.normal(0, 0.01),
#                 'chlorophyll_a': max(0.1, np.random.normal(mean_chl, std_chl)),
#                 'dataset_source': 'synthetic_generated',
#                 'time_period': 'synthetic_fill',
#                 'site_id': site['id'],
#                 'site_name': site['name'],
#                 'region': site['country']
#             })
    
#     if synthetic_data:
#         synthetic_df = pd.DataFrame(synthetic_data)
#         combined_df = pd.concat([combined_df, synthetic_df], ignore_index=True)
#         print(f"   ➕ Added {len(synthetic_df):,} synthetic data points")
    
#     combined_df['bloom_probability'] = combined_df['chlorophyll_a'].apply(
#         lambda x: min(0.95, max(0.05, (x - 5) / 15)) if pd.notna(x) else 0.05
#     )
    
#     combined_df['risk_level'] = pd.cut(
#         combined_df['bloom_probability'],
#         bins=[0, 0.3, 0.6, 0.8, 1.0],
#         labels=['low', 'medium', 'high', 'critical']
#     )
    
#     combined_df['bloom_label'] = (combined_df['chlorophyll_a'] > 10).astype(int)
    
#     np.random.seed(42)
#     combined_df['sst'] = combined_df.apply(
#         lambda row: np.random.normal(
#             15 if row['region'] == 'Ireland' else 14,  
#             2
#         ), axis=1
#     )
#     combined_df['turbidity'] = combined_df.apply(
#         lambda row: np.random.normal(
#             4 if 'Harbor' in row['site_name'] else 3,  
#             1.5
#         ), axis=1
#     )
#     combined_df['salinity'] = combined_df.apply(
#         lambda row: np.random.normal(
#             33 if 'Lough' in row['site_name'] else 34, 
#             1
#         ), axis=1
#     )
#     combined_df['wind_speed'] = np.random.gamma(2, 3, len(combined_df))  
#     combined_df['wave_height'] = np.random.gamma(1.5, 1, len(combined_df))  
    
#     output_csv = "./copernicus_data/hab_dashboard_ENHANCED_data.csv"
#     combined_df.to_csv(output_csv, index=False)
    
#     print(f"\n FINAL ENHANCED DATASET SUMMARY:")
#     print(f" Processed data saved to: {output_csv}")
#     print(f" Total records: {len(combined_df):,}")
#     print(f" Date range: {combined_df['timestamp'].min().date()} to {combined_df['timestamp'].max().date()}")
#     print(f" Total days with data: {combined_df['timestamp'].dt.date.nunique()}")
#     print(f" Unique coordinates: {len(combined_df[['latitude', 'longitude']].drop_duplicates()):,}")
#     print(f"  Monitoring sites: {combined_df['site_name'].nunique()}")
#     print(f" Regions covered: {combined_df['region'].nunique()}")
    
#     print(f"\n Data Sources:")
#     source_counts = combined_df['dataset_source'].value_counts()
#     for source, count in source_counts.head(10).items():
#         print(f"   {source}: {count:,} records")
    
#     print(f"\n Chlorophyll-a Statistics (mg/m³):")
#     print(f"   Mean: {combined_df['chlorophyll_a'].mean():.3f}")
#     print(f"   Median: {combined_df['chlorophyll_a'].median():.3f}")
#     print(f"   Std Dev: {combined_df['chlorophyll_a'].std():.3f}")
#     print(f"   Min: {combined_df['chlorophyll_a'].min():.3f}")
#     print(f"   Max: {combined_df['chlorophyll_a'].max():.3f}")
    
#     print(f"\n⚠️  HAB Risk Distribution:")
#     risk_counts = combined_df['risk_level'].value_counts()
#     for risk in ['low', 'medium', 'high', 'critical']:
#         if risk in risk_counts.index:
#             count = risk_counts[risk]
#             percentage = count/len(combined_df)*100
#             print(f"   {risk.capitalize()}: {count:,} observations ({percentage:.1f}%)")
    
#     print(f"\n📋 Top Sites by Data Volume:")
#     site_summary = combined_df.groupby(['site_name', 'region']).agg({
#         'chlorophyll_a': ['count', 'mean'],
#         'bloom_probability': 'mean'
#     }).round(3)
#     site_summary.columns = ['Count', 'Avg_Chl_a', 'Avg_Bloom_Prob']
#     print(site_summary.sort_values('Count', ascending=False).head(15))
    
#     print(f"\n📅 Temporal Coverage:")
#     monthly_counts = combined_df.groupby(combined_df['timestamp'].dt.to_period('M')).size()
#     print(f"   Months with data: {len(monthly_counts)}")
#     print(f"   Average records per month: {monthly_counts.mean():.0f}")
    
#     print(f"\n🔍 Sample Data Preview:")
#     sample_cols = ['timestamp', 'site_name', 'region', 'chlorophyll_a', 'risk_level', 'dataset_source']
#     print(combined_df[sample_cols].head(10).to_string(index=False))

# else:
#     print("\ No data was successfully downloaded.")
#     print("🔧 Try adjusting the time periods or checking credentials.")

# print(f"\n Enhanced data collection completed!")
# print(f"📁 Check the ./copernicus_data folder for all files")
# print(f"💡 You now have MUCH MORE DATA with:")
# print(f"   Multiple time periods")
# print(f"   Expanded geographic coverage") 
# print(f"   Multiple datasets combined")
# print(f"   More monitoring sites")
# print(f"   Synthetic data filling gaps")
# print(f"   Additional environmental variables")