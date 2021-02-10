import fire
from pathlib import Path
import pandas as pd
import sqlalchemy
from geoalchemy2 import Geometry, WKTElement

def ingest_file(filepath, dbname, username='postgres',host='127.0.0.1', port=5432):
    engine = sqlalchemy.create_engine(f"postgresql://{username}@{host}:{port}/{dbname}", echo=False)
    

def ingest_dir(directory, dbname, username='postgres',host='127.0.0.1', port=5432):
    engine = sqlalchemy.create_engine(f"postgresql://{username}@{host}:{port}/{dbname}", echo=False)
    
    dirpath = Path(directory)
    files = sorted(list(dirpath.glob('*.gz')))

    columnTypes = { 
        "time": sqlalchemy.TIMESTAMP(),
        "lon": sqlalchemy.Numeric(9,6),
        "lat": sqlalchemy.Numeric(8,6),
        "alt": sqlalchemy.Numeric(12,5),
        "range": sqlalchemy.Numeric(12,5),
        "model_dry_tropo_corr": sqlalchemy.Integer(),
        "model_wet_tropo_corr": sqlalchemy.Integer(),
        "iono_corr_gim": sqlalchemy.SmallInteger(),
        "solid_earth_tide": sqlalchemy.SmallInteger(),
        "pole_tide": sqlalchemy.SmallInteger(),
        "geoid": sqlalchemy.Integer(),
        "geom": Geometry('POINT', srid=4326, from_text='ST_GeomFromGeoJSON')
    }

    for file in files:
        table_name = file.stem.split('.')[0]
        sensor = table_name.split('_')[0]
        df = pd.read_parquet(file)
        df.to_sql(table_name, con=engine,if_exists='fail', index=False,dtype=columnTypes)
        index_df = pd.DataFrame(
            {'table_name':table_name,
             'sensor':sensor.lower(),
             'start_time':df.time.min(),
             'end_time':df.time.max()
            },
            index=[0]
        )

if __name__ == "__main__":
    fire.Fire()