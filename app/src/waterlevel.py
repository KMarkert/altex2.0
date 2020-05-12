import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans

SEED = 0

def iqrFilter(series):
    q1 = np.percentile(series, 25)
    q3 = np.percentile(series, 75)

    iqr = stats.iqr(series)

    lowerBound = q1 - (iqr * 1.5)
    upperBound = q3 + (iqr * 1.5)

    mask = ((series >= lowerBound) & (series <= upperBound))

    return series[mask]

def outlierFilter(series):

    diff = np.ptp(series, axis=0)
    labels = None

    if series.size > 4:
        print('running filter...')
        i = 0
        while (diff > 5) & (series.size>=2):
            kmeans = KMeans(init='k-means++', n_clusters=2, n_init=10,
                max_iter=100, algorithm="elkan", random_state=SEED)

            X = np.vstack([series, series]).T

            kmeans.fit(X)
            clusters = kmeans.cluster_centers_.squeeze()[:, 0]
            labels = kmeans.labels_

            class1 = labels == 0
            class2 = labels == 1

            if sum(class1) > sum(class2):
                idx = class1
            else:
                idx = class2

            series = series[idx]
            diff = np.abs(clusters[0] - clusters[1])

            i+=1

            if i > 50:
                break

        print(f'n iterations: {i}')

        kmeans = None

        clusterMean = series.mean()
        std = series.std()

        print('filtering cluster')
        while std > 0.3:
            dist = np.abs(series - clusterMean)
            mask = series != np.argmax(dist)
            series = series[mask]

            std = series.std()

        print('applying iqr filter')
        heights = iqrFilter(series)

    else:
        heights = series

    return heights.mean()

def calcWaterLevel(df,applyFilter=False):
    # set the index to time to make it a time series table
    df = df.set_index('time')

    # get the corretion factor for jason satellite series
    sensorCorr = [0.7 if 'jason' in i else 0. for i in df['sensor']]

    # calculate the media correction factor and scale units to meters
    mediaCorr = (df['model_dry_tropo_corr'] + df['model_wet_tropo_corr']\
        + df['iono_corr_gim'] + df['solid_earth_tide'] + df['pole_tide']) *1e-5

    # calculate geoid correction factor and scale units to meters
    geoidCorr = df['geoid']*1e-5

    # calculate difference between satellite altitude and range with correction factors
    df['waterLevel'] = df['alt'] - (mediaCorr + df['ice_range']) - geoidCorr  - sensorCorr

    # get only the water level series
    series = df['waterLevel']

    # group by distinct date
    # all observations within one day will be aggregated
    grouped = series.groupby(series.index.date)

    if applyFilter:
        wl = grouped.apply(outlierFilter)

    else:
        wl = grouped.mean()

    return wl
