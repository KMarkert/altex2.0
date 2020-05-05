import fire
import datetime
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
from scipy import interpolate
import json
import geojson
# import requests
import glob
import subprocess
import warnings
import aioftp
import asyncio
import logging
import zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from geoalchemy2 import Geometry, WKTElement
import sqlalchemy


warnings.filterwarnings("ignore", category=FutureWarning)

def unpack(fileList):
    outlist = []
    for f in fileList:
        extracted = f.with_suffix('.CNES.nc')
        if extracted.exists() is False or overwrite is True:
            with zipfile.ZipFile(f, 'r') as zip_ref:
                zip_ref.extractall(outDir)
        outlist.append(extracted)
    return outlist

def extract(sensor, outDir, startTime=None, endTime=None, overwrite=False):
    """
    Function to fetch Jason altimetry data from providers

    Args:
        sensor (str): string of the sensor name, accepts jason[1-3]
        outDir (str|pathlib.Path): path to save downloaded files to
    Kwargs:
        startTime ():
        endTime ():
        overwrite ():
    """
    async def _ftp_fetch(sensor, outDir, startTime=None, endTime=None, overwrite=False):
        start = datetime.datetime.strptime(startTime, "%Y-%m-%d")
        end = datetime.datetime.strptime(endTime, "%Y-%m-%d")
        outDir = Path(outDir).resolve()
        flist = []
        async with aioftp.ClientSession('ftp-access.aviso.altimetry.fr',user='km0033@uah.edu',password='1PWZjs') as client:
            await client.change_directory(path=f'geophysical-data-record/{sensor}/gdr_t')
            for path, info in (await client.list(recursive=True)):
                if info["type"] == "file":
                    fdate = datetime.datetime.strptime(
                        str(path).split('/')[-1].split('_')[4], '%Y%m%d')
                    if start <= fdate <= end:
                        outPath = outDir / path.name
                        if outPath.exists() is False or overwrite is True:
                            await client.download(path, destination=outDir)
                        print(f'{path} -> {outPath}')
                        flist.append(outPath)
            return flist

    if sensor in ['saral']:
        tasks = (_ftp_fetch(sensor, outDir,
                            startTime=startTime, endTime=endTime),)

    loop = asyncio.new_event_loop()
    done, _ = loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

    templist = next(tuple(x.result()) for x in done)

    outlist = unpack(templist)

    return outlist


def interpDim(oldArr, newDim, type='nearest'):
    """
    Helper function to perform 1-d interpolation of values
    """
    oldx = np.arange(oldArr.size)
    newx = np.linspace(0, oldx.max(), newDim)
    fInterp = interpolate.interp1d(
        oldx, oldArr, kind=type, fill_value='extrapolate')
    return fInterp(newx)


def parseFile(altimetryPath,spatialFilter=None, geoidDataset=None):
    path = Path(altimetryPath).resolve()
    ds = xr.open_dataset(path)
    geoid = xr.open_dataset(geoidDataset)

    vars20hz = [
        'time_40hz',
        'lon_40hz',
        'lat_40hz',
        'alt_40hz',
        'ice1_range_40hz',
        'ice1_qual_flag_40hz'
    ]

    vars1hz = [
        'qual_rad_1hz_tb_ka',
        'model_dry_tropo_corr',
        'model_wet_tropo_corr',
        'iono_corr_gim',
        'solid_earth_tide',
        'pole_tide'
    ]

    interpMethods = ['nearest'] + ['linear' for i in range(len(vars1hz) - 1)]

    # df = pd.DataFrame()
    dfDict = {}
    for var in vars20hz:
        values = ds[var].values.ravel()
        dfDict[var.replace('_40hz', '').replace('1','')] = values

    dim20Hz = values.size

    for i, var in enumerate(vars1hz):
        values = interpDim(
            ds[var].values, dim20Hz, interpMethods[i])
        dfDict[var] = values

    df = pd.DataFrame(dfDict)
    df.dropna(inplace=True)
    # print(df.columns)

    # do some altering of data including data typing
    df['time'] = df['time'].values.astype('datetime64[us]')
    df['lon'] = df['lon'].where(df['lon'] < 180, df['lon'] - 360)
    df['ice_qual_flag'] = df['ice_qual_flag'].astype(np.uint8)
    df['qual_rad_1hz_tb_ka'] = df['qual_rad_1hz_tb_ka'].astype(np.uint8)

    mask = (df['ice_qual_flag'] == 0)
    df = df.loc[mask]
    df.drop(['qual_rad_1hz_tb_ka','ice_qual_flag'],axis=1,inplace=True)

    # scale values to prevent unnecessarily large dtypes
    df["model_dry_tropo_corr"] = df["model_dry_tropo_corr"] * 10000
    df["model_wet_tropo_corr"] = df["model_wet_tropo_corr"] * 10000
    df["iono_corr_gim"] = df["iono_corr_gim"] * 10000
    df["solid_earth_tide"] = df["solid_earth_tide"] * 10000
    df["pole_tide"] = df["pole_tide"] * 10000

    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.lon, df.lat))
    gdf.crs = {'init': 'epsg:4326'}

    land = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    land['code'] = 1
    clipRegion = gpd.GeoDataFrame(land.dissolve(by='code').buffer(0.05))
    clipRegion.columns = ['geometry']
    clipRegion.crs = {'init': 'epsg:4326'}

    keepPts = gpd.overlay(gdf,clipRegion,how='intersection')
    keepPts['geom'] = keepPts['geometry'].apply(lambda x: WKTElement(x.wkt, srid=4326))
    outGdf = keepPts.drop('geometry', axis=1)

    geoidVals = []
    for row in outGdf.itertuples():
        x,y = row.lon,row.lat
        g = np.int32(geoid.interp(lon=x,lat=y).geoid.values * 10000)
        geoidVals.append(g)

    outGdf['geoid'] = geoidVals

    return outGdf


def transform(flist, maxWorkers=5,geoidDataset=None):
    with ThreadPoolExecutor(max_workers=maxWorkers) as executor:
        gdfs = list(executor.map(lambda x: parseFile(x,geoidDataset=geoidDataset), flist))

    return gdfs


def load(dfs, dbname, table, username='postgres', host='127.0.0.1',port=5432):
    engine = sqlalchemy.create_engine(f"postgresql://{username}@{host}:{port}/{dbname}", echo=False)
    columnTypes = {
        "time": sqlalchemy.TIMESTAMP(),
        "lon": sqlalchemy.Numeric(9,6),
        "lat": sqlalchemy.Numeric(8,6),
        "alt": sqlalchemy.Numeric(8,2),
        "ice_range": sqlalchemy.Numeric(8,2),
        "model_dry_tropo_corr": sqlalchemy.SmallInteger(),
        "model_wet_tropo_corr": sqlalchemy.SmallInteger(),
        "iono_corr_gim": sqlalchemy.SmallInteger(),
        "solid_earth_tide": sqlalchemy.SmallInteger(),
        "pole_tide": sqlalchemy.SmallInteger(),
        "geoid": sqlalchemy.SmallInteger(),
        "geom": Geometry('POINT', srid=4326)
    }

    for df in dfs:
        df.to_sql(table, con=engine,if_exists='append', index=False,dtype=columnTypes)

    return


def etl(sensor, workingDir, dbname, startTime=None, endTime=None, overwrite=False, maxWorkers=5,
        username='postgres',host='127.0.0.1', port=5432, geoidDataset=None, spatialFilter=None):
    raw = extract(sensor, workingDir, startTime=startTime,
                  endTime=endTime, overwrite=False)
    gdfs = transform(raw, maxWorkers=maxWorkers,geoidDataset=geoidDataset)
    load(gdfs, dbname=dbname,table=sensor,username=username,host=host,port=port)

    return


if __name__ == "__main__":
    fire.Fire()
