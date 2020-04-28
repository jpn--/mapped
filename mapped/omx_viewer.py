
import pandas as pd
import geopandas as gpd
from .plotly import plotly_choropleth

import logging
from .widget_logging import handler
logger = logging.getLogger("mapped.omx_viewer")
log = handler.out

try:
    from larch import OMX
except:
    OMX = None
from ipywidgets import HBox, VBox, Dropdown, Label, HTML, FloatRangeSlider, Layout


class OMXBunch(dict):

    def __init__(self, *args, mode='r'):
        if OMX is None:
            raise ModuleNotFoundError('larch.omx')
        super().__init__()
        for a in args:
            self._add_something(a, mode=mode)

    def _add_something(self, s, mode='r', key=''):
        if isinstance(s, str): # filename
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

    def __init__(self, omx, shapefile):

        self._initializing = True
        if OMX is None:
            raise ModuleNotFoundError('larch.omx')

        self.omx_bunch = OMXBunch(omx)
        self.omx_name, self.omx = next(iter(self.omx_bunch.items()))

        self.omx_taz_ids_rows = pd.RangeIndex(1, self.omx.shape[0]+1)
        self.omx_taz_ids_cols = pd.RangeIndex(1, self.omx.shape[1]+1)

        self.shapefile = shapefile

        self.fig = plotly_choropleth(shapefile, color=range(len(shapefile)))

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

        self.otaz_dropdown = Dropdown(
            options=list(self.omx_taz_ids_rows),
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
        self.color_range_data = {}

        self.panel = VBox([
            HTML(
                value="<hr>",
            ),
            Label("Matrix Table"),
            self.matrix_dropdown,
            Label("Origin TAZ"),
            self.otaz_dropdown,
            Label("Color Range"),
            self.color_range,
        ], layout=Layout(max_width='220px'))

        self.matrix_dropdown.observe(self._change_matrix, names='value')
        self.otaz_dropdown.observe(self._change_otaz, names='value')
        self.color_range.observe(self.change_color_range, names='value')
        self.file_dropdown.observe(self.change_omx_file, names='value')
        self.fig.data[0].on_click(self._set_otaz_by_click)

        self.matrix_name = None
        self.otaz = None

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

    def change_view(self, matrix_name=None, otaz=None, force=False):

        try:
            logger.critical(f"change_view matrix_name={matrix_name}, otaz={otaz}")
            do_update = force

            if matrix_name is not None and matrix_name != self.matrix_name:
                self.matrix_name = matrix_name
                do_update = True
            if otaz is not None and otaz != self.otaz:
                self.otaz = otaz
                do_update = True

            if do_update:
                skim_data = pd.DataFrame(
                    data=self.omx.data[self.matrix_name][:],
                    columns=self.omx_taz_ids_cols,
                    index=self.omx_taz_ids_rows,
                )

                uid = "uid_____"

                skim_pull = pd.merge(
                    self.shapefile, skim_data.loc[self.otaz].rename(uid),
                    left_index=True, right_index=True, how='left'
                )

                with self.fig.batch_update():
                    self.fig.data[0].z = skim_pull[uid]
                    self.fig.layout.coloraxis.colorbar.title.text = self.matrix_name
                    if len(self.matrix_name) > 12:
                        self.fig.layout.coloraxis.colorbar.title.side = 'right'
                    else:
                        self.fig.layout.coloraxis.colorbar.title.side = 'top'
                    self.fig.layout.coloraxis.showscale = True


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