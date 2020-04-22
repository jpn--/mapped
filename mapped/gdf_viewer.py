
import pandas as pd
import geopandas as gpd
from pandas.api.types import is_numeric_dtype
from .plotly import plotly_choropleth
from ipywidgets import HBox, VBox, Dropdown, Label, HTML

import plotly.express.colors
def get_color(name):
    if name.lower() in plotly.express.colors.named_colorscales():
        return name
    return getattr(plotly.express.colors.qualitative, name)



class GeoDataFrameViz(VBox):
    """
    Visualize geo data on an interactive map.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
    """

    def __init__(self, gdf, color=None, color_continuous_scale='Cividis', color_discrete_sequence='Plotly'):

        self.gdf = gdf
        if color is not None and color not in self.gdf.columns:
            raise KeyError(color)

        self.fig = plotly_choropleth(gdf, color=color, color_continuous_scale='Cividis')

        self.color_continuous_scale = color_continuous_scale
        self.color_discrete_sequence = color_discrete_sequence

        self.col_dropdown = Dropdown(
            options=[i for i in self.gdf.columns if i!='geometry'],
            value=color,
        )

        self.panel = HBox([
            Label("Color"),
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
                if is_numeric_dtype(self.gdf[self.col_name]):
                    self.fig.data[0].colorscale = get_color(self.color_continuous_scale)
                    self.fig.layout.showlegend = False
                    self.fig.layout.coloraxis.colorbar.title.text = self.col_name
                    if len(self.col_name) > 12:
                        self.fig.layout.coloraxis.colorbar.title.side = 'right'
                    else:
                        self.fig.layout.coloraxis.colorbar.title.side = 'top'
                    self.fig.layout.coloraxis.showscale = True
                else:
                    self.fig.data[0].colorscale = get_color(self.color_discrete_sequence)
                    self.fig.layout.showlegend = True
                    self.fig.layout.coloraxis.colorbar.title.text = self.col_name
                    self.fig.layout.coloraxis.showscale = False




