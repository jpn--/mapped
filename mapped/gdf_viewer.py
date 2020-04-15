
import pandas as pd
import geopandas as gpd
from ipywidgets import HBox, VBox, Dropdown, Label, HTML

class GeoDataFrameViz(HBox):
    """
    Visualize geo data on an interactive map.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
    """

    def __init__(self, gdf):

        self.gdf = gdf

        self.fig = gdf.plotly_choropleth(show_colorbar=True)

        self.col_dropdown = Dropdown(
            options=list(self.gdf.columns),
        )

        self.panel = VBox([
            Label("Column"),
            self.col_dropdown,
        ])

        self.col_dropdown.observe(self._change_column, names='value')

        self.col_name = None

        self.change_view(
            col_name=self.col_dropdown.value,
        )

        super().__init__(children=(
            self.fig,
            self.panel,
        ))


    def _change_column(self, payload):
        self.change_view(col_name=payload['new'])

    def change_view(self, col_name=None):

        do_update = False

        if col_name is not None and col_name != self.col_name:
            self.col_name = col_name
            do_update = True

        if do_update:
            with self.fig.batch_update():
                self.fig.data[0].z = self.gdf[self.col_name]




