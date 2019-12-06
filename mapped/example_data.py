
import numpy as np
import pandas as pd
import geopandas as gpd
import os

def mad_points():

    if os.path.exists('mad_points_3857.pkl.gz'):
        return pd.read_pickle('mad_points_3857.pkl.gz')

    np.random.seed(1)
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
    ])

    data = dict(
        number = np.hstack([
            np.random.uniform(low=50, high=60, size=160    ),
            np.random.uniform(low=50, high=60, size=50    ),
            np.random.uniform(low=30, high=50, size=40    ),
        ]),

        letter = np.hstack([
            np.random.choice(['A','B'], size=160, p=[0.7, 0.3]),
            np.random.choice(['A','B'], size= 50, p=[0.8, 0.2]),
            np.random.choice(['A','B'], size= 40, p=[0.2, 0.8]),
        ]),
    )


    mad_points = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(x[:,0], x[:,1]),
        data=data,
    )

    mad_points.crs = {'init': 'epsg:4326', 'no_defs': True}

    if os.path.exists("dane_county_land.pkl"):
        import pickle
        with open("dane_county_land.pkl", 'rb') as f:
            land = pickle.load(f)
        mad_points = mad_points[mad_points.within(land)]

    return mad_points.to_crs(epsg=3857)

