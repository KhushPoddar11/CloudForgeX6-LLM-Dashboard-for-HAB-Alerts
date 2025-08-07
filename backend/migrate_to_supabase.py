
"""
Simplified HAB Data Migration Script for Supabase
No module-level initialization issues
"""

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import os
from datetime import datetime
import logging
import sys


logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


MEASUREMENTS_FILE = '../Data/copernicus_data/hab_dashboard_ENHANCED_data.csv'
EVENTS_FILE = '../Data/haedat_search.csv'

def get_database_url():
    """Get database URL from environment"""
    database_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
    
    if not database_url:
        logger.error("❌ DATABASE_URL not found!")
        logger.error("Please run: export DATABASE_URL='postgres://postgres.eogpjiswiddjcatekvoj:...'")
        return None
    
    return database_url

def validate_setup():
    """Validate environment and files before starting"""
    logger.info("🔍 Validating setup for Supabase...")
    
    database_url = get_database_url()
    if not database_url:
        return False, None
    
    if not os.path.exists(MEASUREMENTS_FILE):
        logger.error(f"❌ Measurements file not found: {MEASUREMENTS_FILE}")
        return False, None
    

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Supabase connection successful")
        return True, engine
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")
        return False, None

def create_tables(engine):
    """Create Supabase tables"""
    
    logger.info("🏗️ Creating Supabase tables...")
    

    drop_sql = """
    DROP TABLE IF EXISTS hab_events CASCADE;
    DROP TABLE IF EXISTS measurements CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS site_summaries CASCADE;
    """
    

    create_measurements_sql = """
    CREATE TABLE measurements (
        id BIGSERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITHOUT TIME ZONE,
        latitude DECIMAL(10, 8),
        longitude DECIMAL(11, 8),
        chlorophyll_a DECIMAL(10, 6),
        sst DECIMAL(6, 3),
        turbidity DECIMAL(8, 4),
        salinity DECIMAL(6, 3),
        wind_speed DECIMAL(6, 3),
        wave_height DECIMAL(6, 3),
        site_id VARCHAR(20),
        site_name VARCHAR(100) NOT NULL,
        region VARCHAR(50),
        bloom_probability DECIMAL(5, 4),
        risk_level VARCHAR(20),
        bloom_label SMALLINT,
        dataset_source VARCHAR(150),
        time_period VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Enable Row Level Security (Supabase)
    ALTER TABLE measurements ENABLE ROW LEVEL SECURITY;
    CREATE POLICY "Enable read access for all users" ON measurements FOR SELECT USING (true);

    -- Create indexes
    CREATE INDEX idx_measurements_site_name ON measurements(site_name);
    CREATE INDEX idx_measurements_timestamp ON measurements(timestamp DESC);
    CREATE INDEX idx_measurements_region ON measurements(region);
    """

    try:
        with engine.connect() as conn:
            conn.execute(text(drop_sql))
            conn.execute(text(create_measurements_sql))
            conn.commit()
            logger.info("✅ Tables created successfully")
            
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise

def migrate_data(engine):
    """Migrate the data to Supabase"""
    
    logger.info("📊 Starting data migration...")
    
    chunk_size = 20000
    total_rows = 0
    chunk_number = 0
    
    try:

        logger.info("📏 Counting total rows...")
        with open(MEASUREMENTS_FILE, 'r') as f:
            total_file_rows = sum(1 for _ in f) - 1
        logger.info(f"📊 Total rows to migrate: {total_file_rows:,}")
        
        start_time = datetime.now()
        

        for chunk in pd.read_csv(MEASUREMENTS_FILE, chunksize=chunk_size):
            chunk_number += 1
            

            chunk['timestamp'] = pd.to_datetime(chunk['timestamp'], errors='coerce')
            chunk = chunk.dropna(subset=['timestamp', 'site_name'])
            

            chunk = chunk.fillna({
                'salinity': 34.0,
                'wind_speed': 5.0,
                'wave_height': 1.0,
                'region': 'Unknown',
                'risk_level': 'low',
                'bloom_label': 0,
                'site_id': 'S999',
                'dataset_source': 'copernicus_satellite',
                'time_period': 'enhanced_dataset'
            })
            

            try:
                chunk.to_sql(
                    'measurements', 
                    engine, 
                    if_exists='append', 
                    index=False,
                    method='multi',
                    chunksize=5000
                )
                
                total_rows += len(chunk)
                progress = (total_rows / total_file_rows) * 100
                elapsed = (datetime.now() - start_time).total_seconds()
                
                logger.info(
                    f"✅ Chunk {chunk_number}: {len(chunk):,} rows | "
                    f"Total: {total_rows:,} ({progress:.1f}%) | "
                    f"Elapsed: {elapsed:.0f}s"
                )
                

                if chunk_number % 20 == 0:
                    logger.info(f"🎯 Checkpoint: {chunk_number} chunks, {total_rows:,} rows migrated")
                    
            except Exception as e:
                logger.error(f"❌ Error uploading chunk {chunk_number}: {e}")
                continue
        
        total_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"🎉 Migration complete! {total_rows:,} records in {total_time:.0f}s")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

def create_views(engine):
    """Create materialized views"""
    
    logger.info("🏗️ Creating views...")
    
    view_sql = """
    CREATE MATERIALIZED VIEW site_summaries AS
    SELECT 
        site_name,
        region,
        MIN(timestamp)::date as start_date,
        MAX(timestamp)::date as end_date,
        COUNT(*) as total_records,
        ROUND(AVG(chlorophyll_a)::numeric, 4) as avg_chlorophyll,
        ROUND(AVG(bloom_probability)::numeric, 4) as avg_bloom_probability,
        ROUND(AVG(latitude)::numeric, 6) as center_lat,
        ROUND(AVG(longitude)::numeric, 6) as center_lon,
        MODE() WITHIN GROUP (ORDER BY risk_level) as dominant_risk_level,
        MODE() WITHIN GROUP (ORDER BY dataset_source) as primary_data_source,
        COUNT(*) FILTER (WHERE bloom_label = 1) as bloom_events
    FROM measurements 
    WHERE site_name != 'Open Water' AND site_name IS NOT NULL
    GROUP BY site_name, region
    ORDER BY total_records DESC;

    CREATE UNIQUE INDEX idx_site_summaries_site ON site_summaries(site_name);

    CREATE OR REPLACE VIEW dashboard_stats AS
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT site_name) as unique_sites,
        MIN(timestamp) as earliest_data,
        MAX(timestamp) as latest_data,
        ROUND(AVG(chlorophyll_a)::numeric, 4) as avg_chlorophyll,
        COUNT(DISTINCT region) as regions_count,
        COUNT(*) FILTER (WHERE bloom_label = 1) as total_bloom_events,
        ROUND(AVG(bloom_probability)::numeric, 4) as avg_bloom_probability
    FROM measurements WHERE site_name IS NOT NULL;
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(view_sql))
            conn.commit()
            logger.info("✅ Views created successfully")
            
    except Exception as e:
        logger.error(f"❌ Error creating views: {e}")
        raise

def verify_migration(engine):
    """Verify migration success"""
    
    logger.info("🔍 Verifying migration...")
    
    queries = [
        ("Total measurements", "SELECT COUNT(*) FROM measurements"),
        ("Unique sites", "SELECT COUNT(DISTINCT site_name) FROM measurements WHERE site_name != 'Open Water'"),
        ("Site summaries", "SELECT COUNT(*) FROM site_summaries"),
        ("Database size", "SELECT pg_size_pretty(pg_database_size(current_database()))"),
    ]
    
    try:
        with engine.connect() as conn:
            for description, query in queries:
                result = conn.execute(text(query)).fetchall()
                logger.info(f"✅ {description}: {result}")
        
        logger.info("🎉 Verification complete!")
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")

def main():
    """Main migration workflow"""
    
    print("🌊 Simplified HAB Data Migration to Supabase")
    print("=" * 50)
    
    start_time = datetime.now()
    

    is_valid, engine = validate_setup()
    if not is_valid:
        logger.error("❌ Setup validation failed")
        return 1
    
    try:
        create_tables(engine)
        migrate_data(engine)
        create_views(engine)
        verify_migration(engine)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        logger.info("🎉🎉 SUPABASE MIGRATION COMPLETED! 🎉🎉")
        logger.info(f"⏱️ Total time: {total_time:.0f} seconds ({total_time/60:.1f} minutes)")
        logger.info("🚀 Ready for Vercel deployment!")
        
        return 0
        
    except Exception as e:
        logger.error(f"💥 Migration failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)