import datetime
from pathlib import Path
import dask.dataframe as dd
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
from shapely import wkt
import json
import geojson
from functools import partial,lru_cache

@lru_cache()
def filterFileDate(file,startTime,endTime):
    """
    """
    s = datetime.datetime.strptime(startTime,"%Y-%m-%d")
    e = datetime.datetime.strptime(endTime,"%Y-%m-%d")
    dstr = str(file).split('_')[-1].split('.')[0]
    d = datetime.datetime.strptime(dstr,"%Y%m%d")
    if d >= s and d <= e:
        return file
    else:
        return


@lru_cache()
def getDataFrame(datadir,sensor=None,startTime=None,endTime=None,region=None,columns=None):
    """

    """

    datadir = Path(datadir) / sensor

    files = datadir.glob('*.gz')

    filter_func = partial(filterFileDate,startTime=startTime,endTime=endTime)

    filteredfiles = list(filter(lambda x: x is not None , map(filter_func,files)))

    # df = dd.read_parquet(filteredfiles,engine="pyarrow")

    # df= df.set_index(["lat","lon"],sorted=True)

    # need to add in spatial filter...
    xy = tuple(map(lambda x: tuple(map(float, x.split(" "))), region.split(",")))
    region = gpd.GeoDataFrame({'geometry':shape(geojson.Polygon([xy]))},index=[0])
    bbox = tuple(region.bounds.iloc[0])

    df = dd.read_parquet(filteredfiles,engine="pyarrow")

    # get location of where points are in bounding box
    xMask = (df.lon >= bbox[0]) & (df.lon <= bbox[2])
    yMask = (df.lat >= bbox[1]) & (df.lat <= bbox[3])
    boxMask = xMask & yMask

    # filter by bounding box
    dfFiltered = df.loc[boxMask].compute()

    gdf = gpd.GeoDataFrame(
        dfFiltered, geometry=gpd.points_from_xy(dfFiltered.lon, dfFiltered.lat)
    )

    final = pd.DataFrame(
        gpd.overlay(gdf, region,how='intersection')
        .drop('geometry', axis=1)
    )

    final['sensor'] = [sensor for i in range(final.shape[0])]
    final['time'] = pd.to_datetime(final['time'])

    if columns is not None:
        final = dfFiltered[columns]
    else:
        final.drop(['geom'],axis=1,inplace=True)

    return final
