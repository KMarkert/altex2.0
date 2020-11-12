import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from functools import lru_cache

SEED = 0

def iqrFilter(series):
    heights = series.copy()
    q1 = np.percentile(heights, 25)
    q3 = np.percentile(heights, 75)

    iqr = stats.iqr(heights)

    lowerBound = q1 - (iqr * 1.5)
    upperBound = q3 + (iqr * 1.5)

    mask = ((heights >= lowerBound) & (heights <= upperBound))

    return heights[mask]

def outlierFilter(series):
    heights = series.copy()

    diff = np.ptp(heights, axis=0)
    labels = None

    if heights.size > 4:
        i = 0
        while (diff > 5) & (heights.size>=3):
            kmeans = KMeans(init='k-means++', n_clusters=2, n_init=20,
                max_iter=100, algorithm="elkan", random_state=SEED)

            X = np.vstack([heights, heights]).T

            kmeans.fit(X)
            clusters = kmeans.cluster_centers_.squeeze()[:, 0]
            labels = kmeans.labels_

            class1 = labels == 0
            class2 = labels == 1

            if sum(class1) > sum(class2):
                idx = class1
            else:
                idx = class2

            heights = heights[idx]
            diff = np.abs(clusters[0] - clusters[1])

            i+=1

            # if i > 50:
            #     break

        kmeans = None

        clusterMean = heights.mean()
        std = heights.std()

        while (std > 0.3) and (heights.size >=3):
            dist = np.abs(heights - clusterMean)
            mask = np.arange(heights.size) != np.argmax(dist)
            heights = heights[mask]

            std = heights.std()

        if heights.size >= 3:
            heights = iqrFilter(heights)

    return heights.mean()

def calcWaterLevel(df,applyFilter=True):
    # set the index to time to make it a time series table
    df = df.set_index('time')

    # get the corretion factor for jason satellite series
    df['sensor_corr'] = [0.7 if 'jason' in i else 0. for i in df['sensor']]

    # calculate the media correction factor and scale units to meters
    mediaCorr = (df['model_dry_tropo_corr'] + df['model_wet_tropo_corr']\
        + df['iono_corr_gim'] + df['solid_earth_tide'] + df['pole_tide']) * 0.00001

    # calculate geoid correction factor and scale units to meters
    geoidCorr = df['geoid']* 0.00001

    # calculate difference between satellite altitude and range with correction factors
    df['waterLevel'] = df['alt'] - (mediaCorr + df['range'] + geoidCorr +  df['sensor_corr'])

    # get only the water level series
    series = iqrFilter(df['waterLevel'])

    # group by distinct date
    # all observations within one day will be aggregated
    grouped = series.groupby(series.index.date)

    if applyFilter:
        wl = grouped.apply(outlierFilter)

    else:
        wl = grouped.mean()

    return wl
