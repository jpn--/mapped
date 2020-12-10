import ast
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from .plotly import plotly_choropleth, good_zoom
from plotly import graph_objects as go

import logging
from .widget_logging import handler
logger = logging.getLogger("mapped.omx_viewer")
log = handler.out

try:
    from larch import OMX
except:
    OMX = None
from ipywidgets import HBox, VBox, Dropdown, Label, HTML, FloatRangeSlider, Layout, Text, FloatSlider, RadioButtons


class OMXBunch(dict):

    def __init__(self, *args, mode='r'):
        if OMX is None:
            raise ModuleNotFoundError('larch.omx')
        super().__init__()
        for a in args:
            self._add_something(a, mode=mode)

    def _add_something(self, s, mode='r', key=''):
        if isinstance(s, str): # possible filename
            if os.path.exists(s):
                self[s] = OMX(s, mode=mode)
        elif isinstance(s, OMX):
            self[s.filename] = s
        elif isinstance(s, dict):
            for k,i in s.items():
                self._add_something(i, mode=mode, key=f"{key}.{k}")
        elif isinstance(s, (tuple,list)):
            for k,i in enumerate(s):
                self._add_something(i, mode=mode, key=f"{key}[{k}]")
        else:
            raise TypeError(key + ":" + str(type(s)))

class OMXViz(VBox):
    """
    Visualize OMX data on an interactive map.

    Parameters
    ----------
    omx : str or larch.OMX
        Either the path to an OMX file, which will be opened in
        read-only mode, or an existing larch.OMX object.
        It is currently assumed that the TAZ id's will be sequential
        beginning with 1, future versions of this package may
        allow you to select a lookup from the file.
    shapefile : geopandas.GeoDataFrame
        The index of this GeoDataFrame should be the TAZ id's as
        mentioned above.  If it is not, set it as such before
        giving it here.
    """

    def __init__(self, omx, shapefile, nan_values='', alpha=1.0, ranges=None):

        self._initializing = True
        if OMX is None:
            raise ModuleNotFoundError('larch.omx')

        self.omx_bunch = OMXBunch(omx)
        self.omx_name, self.omx = next(iter(self.omx_bunch.items()))

        self.omx_taz_ids_rows = pd.RangeIndex(1, self.omx.shape[0]+1)
        self.omx_taz_ids_cols = pd.RangeIndex(1, self.omx.shape[1]+1)

        self.shapefile = shapefile

        self.fig = plotly_choropleth(shapefile, color=range(len(shapefile)))
        plotly_choropleth(shapefile, color=range(len(shapefile)), fig=self.fig, coloraxis='coloraxis2')
        self.fig.data[-1]['showscale'] = False
        self.fig.data[-1]['colorscale']=[
            [0.0, f'rgba(0, 0, 0, 0.15)'],
            [1.0, f'rgba(0, 0, 0, 0.15)'],
        ]
        self.fig.data[-1]['hovertemplate'] = "TAZ %{location}<extra>Not Valid</extra>"

        self.fig.add_trace(go.Scattermapbox(
            mode = "markers",
            lon = [],
            lat = [],
            marker = {'size': 10, 'color':'black', 'symbol':'star'},
        ))

        self.file_dropdown = Dropdown(
            options=list(self.omx_bunch.keys()),
            value=self.omx_name,
            # description="File:",
            layout=Layout(width="100%"),
        )

        self.matrix_dropdown = Dropdown(
            # label='Matrix Table',
            options=list(self.omx.data._v_children),
            layout=Layout(max_width='180px'),
        )

        zone_list = list(self.omx_taz_ids_rows)

        self.otaz_dropdown = Dropdown(
            options=zone_list,
            layout=Layout(max_width='180px'),
        )

        self.color_range = FloatRangeSlider(
            value=[0, 100],
            min=0,
            max=100.0,
            step=1.0,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='.1f',
            layout=Layout(max_width='180px'),
        )
        self.color_range_data = ranges or {}

        self.nan_values = Text(
            value=nan_values,
            placeholder='Enter NaN Placeholder Values, if any',
            disabled=False,
            layout=Layout(max_width='180px'),
        )

        self.opacity = FloatSlider(
            value=alpha,
            min=0,
            max=1.0,
            step=0.05,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='.2f',
            layout=Layout(max_width='180px'),
        )
        self.alpha = alpha

        self.taz_highlight = Dropdown(
            options=[None,]+zone_list,
            layout=Layout(max_width='180px'),
        )

        self.direction_mode_radio = RadioButtons(
            options=['Origin TAZ', 'Destination TAZ'],
            value='Origin TAZ',
            layout=Layout(max_width='180px'),
        )

        self.panel = VBox([
            HTML(
                value="<hr>",
            ),
            Label("Matrix Table"),
            self.matrix_dropdown,
            self.direction_mode_radio,
            self.otaz_dropdown,
            Label("Color Range"),
            self.color_range,
            Label("Exclude Values"),
            self.nan_values,
            Label("Opacity"),
            self.opacity,
            Label("Find TAZ"),
            self.taz_highlight,
        ], layout=Layout(max_width='220px'))

        self.matrix_dropdown.observe(self._change_matrix, names='value')
        self.otaz_dropdown.observe(self._change_otaz, names='value')
        self.direction_mode_radio.observe(self._change_direction_mode, names='value')
        self.taz_highlight.observe(self._change_highlight_taz, names='value')
        self.nan_values.observe(self._change_nan_values, names='value')
        self.opacity.observe(self._change_alpha_value, names='value')
        self.color_range.observe(self.change_color_range, names='value')
        self.file_dropdown.observe(self.change_omx_file, names='value')
        self.fig.data[0].on_click(self._set_otaz_by_click)
        self.fig.data[1].on_click(self._set_otaz_by_click)

        self.matrix_name = None
        self.otaz = None
        self.nan_values_str = nan_values
        self.direction_mode = self.direction_mode_radio.value

        with self.fig.batch_update():
            self.change_view(
                matrix_name=self.matrix_dropdown.value,
                otaz=self.otaz_dropdown.value,
            )
            self.reset_color_range()

        self.body = HBox(children=(
            self.fig,
            self.panel,
        ))

        self.header = VBox([
            self.file_dropdown,
            # Label(f"File: {self.omx.filename}"),
        ])

        self.footer = VBox([
            Label(f"OMX Viewer Log"),
            log,
        ])

        super().__init__(children=(
            self.header,
            self.body,
            self.footer,
        ))
        self._initializing = False
        self._change_highlight_taz({'new':None})
        self.fig._send_relayout_msg({})
        self.fig._dispatch_layout_change_callbacks({})
        self.change_view(force=True)


    def _set_otaz_by_click(self, trace, points, selector):
        try:
            otaz = self.shapefile.index[points.point_inds[0]]
        except:
            pass
        else:
            self.otaz_dropdown.value = otaz

    def _change_matrix(self, payload):
        with self.fig.batch_update():
            self.change_view(matrix_name=payload['new'])
            self.reset_color_range()

    def _change_otaz(self, payload):
        self.change_view(otaz=payload['new'])
        self._change_highlight_taz({'new':self.taz_highlight.value})

    def _change_direction_mode(self, payload):
        self.change_view(direction_mode=payload['new'])

    def _change_highlight_taz(self, payload):
        just_otaz = self.shapefile.loc[[self.otaz]].to_crs(epsg=4326)
        c = just_otaz['geometry'].representative_point()
        lat, lon = [float(c.y)], [float(c.x)]

        if payload['new'] is None:
            zoom = None
        else:
            just_this_taz = self.shapefile.loc[[payload['new']]].to_crs(epsg=4326)
            c = just_this_taz['geometry'].representative_point()
            zoom = good_zoom(just_this_taz)-3
            lat.append(float(c.y))
            lon.append(float(c.x))

        with self.fig.batch_update():
            self.fig.data[2]['lat'] = lat
            self.fig.data[2]['lon'] = lon
            self.fig.data[2]['hoverinfo'] = "text"

            if len(lat) == 1:
                self.fig.data[2]['hovertext'] = f"TAZ {self.otaz}"
                self.fig.data[2]['marker'] = {
                    'size': 10, 'color': 'black',
                    'symbol': 'star'
                }
            else:
                self.fig.data[2]['hovertext'] = [
                    f"TAZ {self.otaz} (Origin)",
                    f"TAZ {payload['new']}",
                ]
                self.fig.data[2]['marker'] = {
                    'size': 10, 'color': 'black',
                    'symbol': ['star','circle'],
                }
                self.fig.update_layout(
                    mapbox_center_lat=lat[-1],
                    mapbox_center_lon=lon[-1],
                )
                if zoom is not None:
                    self.fig.update_layout(
                        mapbox_zoom=zoom,
                    )

    def _change_nan_values(self, payload):
        self.change_view(nan_values=payload['new'])

    def _change_alpha_value(self, payload):
        self.change_view(alpha=payload['new'])

    def change_view(
            self,
            matrix_name=None,
            otaz=None,
            nan_values=None,
            alpha=None,
            direction_mode=None,
            force=False,
    ):

        try:
            logger.debug(f"change_view matrix_name={matrix_name}, otaz={otaz}")
            do_update = force

            if matrix_name is not None and matrix_name != self.matrix_name:
                self.matrix_name = matrix_name
                do_update = True
            if otaz is not None and otaz != self.otaz:
                self.otaz = otaz
                do_update = True
            if nan_values is not None and nan_values != self.nan_values_str:
                self.nan_values_str = nan_values
                do_update = True
            if alpha is not None and alpha != self.alpha:
                self.alpha = alpha
                do_update = True
            if direction_mode is not None and direction_mode != self.direction_mode:
                self.direction_mode = direction_mode
                do_update = True

            if do_update:
                skim_data = pd.DataFrame(
                    data=self.omx.data[self.matrix_name][:],
                    columns=self.omx_taz_ids_cols,
                    index=self.omx_taz_ids_rows,
                )

                uid = "uid_____"

                if self.direction_mode == 'Origin TAZ':
                    skim_pull = pd.merge(
                        self.shapefile, skim_data.loc[self.otaz].rename(uid),
                        left_index=True, right_index=True, how='left'
                    )
                else:
                    skim_pull = pd.merge(
                        self.shapefile, skim_data.loc[:,self.otaz].rename(uid),
                        left_index=True, right_index=True, how='left'
                    )

                nans_str = self.nan_values_str
                if nans_str:
                    if nans_str[:2] == ">=":
                        nans = ast.literal_eval(nans_str[2:])
                        is_nans = skim_pull[uid] >= nans
                        skim_pull.loc[is_nans, uid] = np.nan
                    elif nans_str[:2] == "<=":
                        nans = ast.literal_eval(nans_str[2:])
                        is_nans = skim_pull[uid] <= nans
                        skim_pull.loc[is_nans, uid] = np.nan
                    elif nans_str[0] == ">":
                        nans = ast.literal_eval(nans_str[1:])
                        is_nans = skim_pull[uid] > nans
                        skim_pull.loc[is_nans, uid] = np.nan
                    elif nans_str[0] == "<":
                        nans = ast.literal_eval(nans_str[1:])
                        is_nans = skim_pull[uid] < nans
                        skim_pull.loc[is_nans, uid] = np.nan
                    else:
                        if "," in nans_str:
                            nans = ast.literal_eval(nans_str)
                        else:
                            nans = [ast.literal_eval(nans_str)]
                        is_nans = skim_pull[uid].isin(nans)
                        skim_pull.loc[is_nans, uid] = np.nan

                with self.fig.batch_update():
                    self.fig.layout.coloraxis.colorscale = [
                        [0.0,                f'rgba(13 , 8  , 135, {self.alpha:0.2f})'],
                        [0.1111111111111111, f'rgba(70 , 3  , 159, {self.alpha:0.2f})'],
                        [0.2222222222222222, f'rgba(114, 1  , 168, {self.alpha:0.2f})'],
                        [0.3333333333333333, f'rgba(156, 23 , 158, {self.alpha:0.2f})'],
                        [0.4444444444444444, f'rgba(189, 55 , 134, {self.alpha:0.2f})'],
                        [0.5555555555555556, f'rgba(216, 87 , 107, {self.alpha:0.2f})'],
                        [0.6666666666666666, f'rgba(237, 121, 83 , {self.alpha:0.2f})'],
                        [0.7777777777777778, f'rgba(251, 159, 58 , {self.alpha:0.2f})'],
                        [0.8888888888888888, f'rgba(253, 202, 38 , {self.alpha:0.2f})'],
                        [1.0,                f'rgba(240, 249, 33 , {self.alpha:0.2f})'],
                    ]
                    self.fig.data[0].z = skim_pull[uid]
                    na = skim_pull[uid].isna()
                    na[~na] = np.nan
                    self.fig.data[1].z = na
                    self.fig.data[1]['hovertemplate'] = "TAZ %{location}<extra>Not Valid</extra>"
                    self.fig.layout.coloraxis.colorbar.title.text = self.matrix_name
                    if len(self.matrix_name) > 12:
                        self.fig.layout.coloraxis.colorbar.title.side = 'right'
                    else:
                        self.fig.layout.coloraxis.colorbar.title.side = 'top'
                    self.fig.layout.coloraxis.showscale = True
                    try:
                        self.fig.layout.coloraxis2.colorscale = [
                            [0.0, f'rgba(0, 0, 0, 0.15)'],
                            [1.0, f'rgba(0, 0, 0, 0.15)'],
                        ]
                        self.fig.layout.coloraxis2.showscale = False
                    except AttributeError:
                        pass

        except:
            logger.exception("error in change_view")
            raise

    def reset_color_range(self):
        skim_data = self.omx.data[self.matrix_name][:]
        lo_ = skim_data.min()
        hi_ = skim_data.max()
        if self.matrix_name not in self.color_range_data:
            logger.debug(f"init color_range_data {self.matrix_name}")
            self.color_range_data[self.matrix_name] = (lo_, hi_)

        lo,hi = self.color_range_data[self.matrix_name]
        lo = max(lo, lo_)
        hi = min(hi, hi_)
        self.color_range.min = lo_
        self.color_range.max = hi_
        self.color_range.value = lo,hi

    def change_color_range(self, payload=None):
        logger.debug(f"       change_color_range payload=[{payload}]")
        col = self.matrix_dropdown.value
        lo,hi = self.color_range.value
        if not self._initializing:
            self.color_range_data[col] = (lo,hi)
        with self.fig.batch_update():
            self.fig.layout.coloraxis.cauto = False
            self.fig.layout.coloraxis.cmin = lo
            self.fig.layout.coloraxis.cmax = hi

    def change_omx_file(self, payload=None):
        logger.debug(f"change_omx_file payload=[{payload}]")
        if payload['name'] == 'value':
            if 'new' in payload:
                self.omx_name = payload['new']
            else:
                self.omx_name = self.file_dropdown.value
            self.omx = self.omx_bunch[self.omx_name]
            old_matrix_name = self.matrix_dropdown.value
            self.matrix_dropdown.options = list(self.omx.data._v_children)
            if old_matrix_name in self.matrix_dropdown.options:
                self.matrix_dropdown.value = old_matrix_name
            else:
                self.matrix_dropdown.value = next(iter(self.omx.data._v_children))
            self.change_view(force=True)