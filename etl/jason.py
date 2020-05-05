import os
import fire
import datetime
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
from scipy import interpolate
import glob
# import requests
import subprocess
import warnings
import aioftp
import asyncio
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sqlalchemy
from geoalchemy2 import Geometry, WKTElement

warnings.filterwarnings("ignore", category=FutureWarning)


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
        async with aioftp.ClientSession('ftp.nodc.noaa.gov') as client:
            await client.change_directory(path=f'pub/data.nodc/{sensor}/gdr/gdr/')
            for path, info in (await client.list(recursive=True)):
                if info["type"] == "file":
                    fdate = datetime.datetime.strptime(
                        str(path).split('_')[4], '%Y%m%d')
                    if start <= fdate <= end:
                        outPath = outDir / path.name
                        if outPath.exists() is False or overwrite is True:
                            await client.download(path, destination=outDir)
                        print(f'{path} -> {outPath}')
                        flist.append(outPath)
            return flist

    if sensor in ['jason2', 'jason3']:
        tasks = (_ftp_fetch(sensor, outDir,
                            startTime=startTime, endTime=endTime),)

    loop = asyncio.new_event_loop()
    done, _ = loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

    outlist = next(tuple(x.result()) for x in done)

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


def parseFile(altimetryPath, spatialFilter=None, geoidDataset=None):
    path = Path(altimetryPath).resolve()
    ds = xr.open_dataset(path)
    geoid = xr.open_dataset(geoidDataset).load()
    # landArea = gpd.read_file(spatialFilter)

    vars20hz = [
        'time_20hz',
        'lon_20hz',
        'lat_20hz',
        'alt_20hz',
        'ice_range_20hz_ku',
        'ice_qual_flag_20hz_ku'
    ]

    vars1hz = [
        'alt_state_flag_ku_band_status',
        'model_dry_tropo_corr',
        'model_wet_tropo_corr',
        'iono_corr_gim_ku',
        'solid_earth_tide',
        'pole_tide'
    ]

    interpMethods = ['nearest'] + ['linear' for i in range(len(vars1hz) - 1)]

    # df = pd.DataFrame()
    dfDict = {}
    for var in vars20hz:
        values = ds[var].values.ravel()
        dfDict[var.replace('_20hz', '').replace('_ku','')] = values

    dim20Hz = values.size

    for i, var in enumerate(vars1hz):
        values = interpDim(
            ds[var].values, dim20Hz, interpMethods[i])
        dfDict[var.replace('_ku','')] = values

    df = pd.DataFrame(dfDict)
    df.dropna(inplace=True)
    # print(df.columns)

    scaleFactor = 10000

    # do some altering of data including data typing
    df['time'] = df['time'].values.astype('datetime64[us]')
    df['lon'] = df['lon'].where(df['lon'] < 180, df['lon'] - 360)
    df['fid'] = range(df.shape[0])
    df['ice_qual_flag'] = df['ice_qual_flag'].astype(np.uint8)
    df['alt_state_flag_band_status'] = df['alt_state_flag_band_status'].astype(np.uint8)

    # scale values to prevent unnecessarily large dtypes
    df["model_dry_tropo_corr"] = (df["model_dry_tropo_corr"] * scaleFactor).astype(np.int32)
    df["model_wet_tropo_corr"] = (df["model_wet_tropo_corr"] * scaleFactor).astype(np.int32)
    df["iono_corr_gim"] = (df["iono_corr_gim"] * scaleFactor).astype(np.int32)
    df["solid_earth_tide"] = (df["solid_earth_tide"] * scaleFactor).astype(np.int32)
    df["pole_tide"] = (df["pole_tide"] * scaleFactor).astype(np.int32)


    mask = (df['alt_state_flag_band_status'] == 0) & (df['ice_qual_flag'] == 0)
    df = df.loc[mask]
    df.drop(['alt_state_flag_band_status','ice_qual_flag'],axis=1,inplace=True)

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

    x,y = outGdf['lon'].where(outGdf['lon'] > 0, outGdf['lon'] + 360).values, outGdf.lat.values
    xLookup = geoid.lon.interp(lon=x,method='nearest').compute().values
    yLookup = geoid.lat.interp(lat=y,method='nearest').compute().values
    geoidVals = (geoid.geoid.sel(lon=xLookup,lat=yLookup).compute().values * scaleFactor).astype(np.int32)
    # print(x.size, x.min(),x.max())

    outGdf['geoid'] =  geoidVals.diagonal()

    return outGdf

def transform(flist, maxWorkers=5,geoidDataset=None):

    with ThreadPoolExecutor(max_workers=maxWorkers) as executor:
        gdfs = list(executor.map(lambda x: parseFile(x,geoidDataset=geoidDataset), flist))
    # gdf = []
    # for f in flist:
    #     gdfs = parseFile(f,geoidDataset=geoidDataset)

    return gdfs


def load(dfs, dbname, table, username='postgres', host='127.0.0.1',port=5432):
    engine = sqlalchemy.create_engine(f"postgresql://{username}@{host}:{port}/{dbname}", echo=False)
    columnTypes = {
        "time": sqlalchemy.TIMESTAMP(),
        "lon": sqlalchemy.Numeric(9,6),
        "lat": sqlalchemy.Numeric(8,6),
        "alt": sqlalchemy.Numeric(12,5),
        "ice_range": sqlalchemy.Numeric(12,5),
        "model_dry_tropo_corr": sqlalchemy.Integer(),
        "model_wet_tropo_corr": sqlalchemy.Integer(),
        "iono_corr_gim": sqlalchemy.SmallInteger(),
        "solid_earth_tide": sqlalchemy.SmallInteger(),
        "pole_tide": sqlalchemy.SmallInteger(),
        "geoid": sqlalchemy.Integer(),
        "geom": Geometry('POINT', srid=4326)
    }

    for df in dfs:
        df.to_sql(table, con=engine,if_exists='append', index=False,dtype=columnTypes)

    return



def etl(sensor, workingDir, dbname, startTime=None, endTime=None, overwrite=False, maxWorkers=5,
        username='postgres',host='127.0.0.1', port=5432, geoidDataset=None,spatialFilter=None
        cleanup=False):
    raw = extract(sensor, workingDir, startTime=startTime,
                  endTime=endTime, overwrite=False)
    # raw = glob.glob(workingDir+'JA3*.nc')
    gdfs = transform(raw, maxWorkers=maxWorkers,geoidDataset=geoidDataset)
    load(gdfs, dbname=dbname,table=sensor,username=username,host=host,port=port)

    if cleanup:
        trash = glob.glob(workingDir+'*.*')
        for file in trash:
            os.remove(file)

    return


if __name__ == "__main__":
    fire.Fire()
