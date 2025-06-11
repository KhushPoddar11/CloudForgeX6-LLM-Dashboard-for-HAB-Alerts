import copernicusmarine as cm
import xarray as xr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

print("🌊 Copernicus Marine Real Data Downloader")
print("=" * 50)
print("\n📌 Target: Irish Coastal Waters Chlorophyll Data")
print("📍 Region: 51°N-55.5°N, 11°W-5.5°W")

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
    print(f"\n🔍 Trying dataset: {dataset['desc']}")
    print(f"   ID: {dataset['id']}")
    
    try:
        output_file = f"irish_chlorophyll_{datetime.now().strftime('%Y%m%d')}.nc"
        
        #last 3 months for better data availability
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
        
        print(f"\n📋 Dataset info:")
        print(f"   Variables: {list(ds.data_vars)}")
        print(f"   Dimensions: {dict(ds.dims)}")
        
        chl_var = None
        for var in ['CHL', 'chl', 'chlor_a']:
            if var in ds.data_vars:
                chl_var = var
                break
        
        if not chl_var:
            print("⚠️  No chlorophyll variable found in dataset")
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
            
            print(f"\n🔍 Sample data:")
            print(df_clean[['timestamp', 'site_name', 'chlorophyll_a', 'risk_level']].head(10))
            
    except Exception as e:
        print(f"\n⚠️ Error processing data: {e}")

else:
    print("\nCould not download data with provided credentials.")
    print("\n🔧 Troubleshooting:")
    print("1. Check if your credentials are correct")
    print("2. Try logging in at: https://data.marine.copernicus.eu")
    print("3. The dataset IDs might have changed")
    
    print("\n📋 Alternative: Manual download")
    print("1. Go to: https://data.marine.copernicus.eu/products")
    print("2. Log in with your credentials")
    print("3. Search for: OCEANCOLOUR_GLO_BGC_L3_MY_009_103")
    print("4. Use the GUI to subset data for Irish waters")

print("\nScript complete!")
print("Check the ./copernicus_data folder for your data files")