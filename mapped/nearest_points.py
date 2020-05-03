
# from  https://gis.stackexchange.com/a/301935

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

# from shapely.geometry import Point
# gpd1 = gpd.GeoDataFrame([['John', 1, Point(1, 1)], ['Smith', 1, Point(2, 2)],
#                          ['Soap', 1, Point(0, 2)]],
#                         columns=['Name', 'ID', 'geometry'])
# gpd2 = gpd.GeoDataFrame([['Work', Point(0, 1.1)], ['Shops', Point(2.5, 2)],
#                          ['Home', Point(1, 1.1)]],
#                         columns=['Place', 'geometry'])

def nearest_points(sources, targets):
    """
    For each point in sources, matches the nearest point in targets.

    Parameters
    ----------
    sources: geopandas.GeoDataFrame
        The points to match nearest places to.  Each row (point)
        in this dataframe will appear once in the output.
    targets: geopandas.GeoDataFrame
        The points that can be matched.  Each row (point)
        in this dataframe may appear zero or multiple times in
        the output.

    Returns
    -------
    geopandas.GeoDataFrame
    """
    nA = np.array(list(zip(sources.geometry.x, sources.geometry.y)))
    nB = np.array(list(zip(targets.geometry.x, targets.geometry.y)))
    btree = cKDTree(nB)
    dist, idx = btree.query(nA, k=1)
    gdf = pd.concat(
        [sources.reset_index(drop=True), targets.loc[idx, targets.columns != 'geometry'].reset_index(drop=True),
         pd.Series(dist, name='dist')], axis=1)
    return gdf

# nearest_points(gpd1, gpd2)