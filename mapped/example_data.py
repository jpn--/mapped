
import numpy as np
import pandas as pd
import geopandas as gpd
from .caching import memory

_lakes = None

@memory.cache
def mad_lakes():
    global _lakes
    if _lakes is not None:
        return _lakes

    try:
        import osmnx as ox
    except ImportError:
        return None

    _lakes = ox.gdf_from_places([
        'Lake Mendota, Dane County, WI',
        'Lake Monona, Dane County, WI',
        'Lake Wingra, Dane County, WI',
        'Second Lake, Dane County, WI',
        'Lower Mud Lake, Dane County, WI',
        'Upper Mud Lake, Dane County, WI',
    ])
    _lakes = _lakes.append(
        ox.gdf_from_place('Yahara River, Dane County, WI', which_result=5),
    )

    _lakes = _lakes.to_crs(epsg=3857)

    return _lakes


@memory.cache
def mad_points(seed=42):

    np.random.seed(seed)
    x = np.vstack([
        np.random.multivariate_normal(
            [-89.384984, 43.074273,  ],
            [[.005,0],[0,.002]],
            160,
        ),
        np.random.multivariate_normal(
            [-89.384984, 43.074273,  ],
            [[.00001,0],[0,.000005]],
            50,
        ),
        np.random.multivariate_normal(
            [-89.423827, 43.072005,   ],
            [[.0001,0],[0,.000025]],
            40,
        ),
        np.random.multivariate_normal(
            [-89.524942, 43.091881, ],
            [[.00003, 0], [0, .000095]],
            40,
        ),

    ])

    data = dict(
        number = np.hstack([
            np.random.uniform(low=10, high=90, size=160),
            np.random.uniform(low=50, high=90, size=50),
            np.random.uniform(low=10, high=50, size=40),
            np.random.uniform(low=60, high=80, size=40),
        ]),

        letter = np.hstack([
            np.random.choice(['A','B'], size=160, p=[0.8, 0.2]),
            np.random.choice(['A','B'], size= 50, p=[0.9, 0.1]),
            np.random.choice(['A','B'], size= 40, p=[0.2, 0.8]),
            np.random.choice(['A','B'], size= 40, p=[0.9, 0.1]),
        ]),
    )

    mad_points = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(x[:,0], x[:,1]),
        data=data,
    ).cx[-89.612122:-89.223902,42.965257:43.194947].copy()

    mad_points.crs = {'init': 'epsg:4326', 'no_defs': True}
    mad_points = mad_points.to_crs(epsg=3857)

    lakes = mad_lakes()
    if lakes is not None:
        mask = np.ones(len(mad_points), dtype=bool)
        for lake in lakes.geometry:
            mask &= ~mad_points.within(lake)
        mad_points = mad_points[mask].copy()

    return mad_points

