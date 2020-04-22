
import pandas as pd
import geopandas as gpd
try:
    from larch import OMX
except:
    OMX = None
from ipywidgets import HBox, VBox, Dropdown, Label, HTML

class OMXViz(HBox):
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

        if OMX is None:
            raise ModuleNotFoundError('larch.omx')
        if isinstance(omx, str):
            omx = OMX(omx, mode='r')
        self.omx = omx

        self.omx_taz_ids_rows = pd.RangeIndex(1, self.omx.shape[0]+1)
        self.omx_taz_ids_cols = pd.RangeIndex(1, self.omx.shape[1]+1)

        self.shapefile = shapefile

        self.fig = shapefile.plotly_choropleth(show_colorbar=True)

        self.matrix_dropdown = Dropdown(
            # label='Matrix Table',
            options=list(self.omx.data._v_children),
        )

        self.otaz_dropdown = Dropdown(
            options=list(self.omx_taz_ids_rows),
        )

        self.panel = VBox([
            Label(f"File: {self.omx.filename}"),
            HTML(
                value="<hr>",
            ),
            Label("Matrix Table"),
            self.matrix_dropdown,
            Label("Origin TAZ"),
            self.otaz_dropdown,
        ])

        self.matrix_dropdown.observe(self._change_matrix, names='value')
        self.otaz_dropdown.observe(self._change_otaz, names='value')
        self.fig.data[0].on_click(self._set_otaz_by_click)

        self.matrix_name = None
        self.otaz = None

        self.change_view(
            matrix_name=self.matrix_dropdown.value,
            otaz=self.otaz_dropdown.value,
        )

        super().__init__(children=(
            self.fig,
            self.panel,
        ))


    def _set_otaz_by_click(self, trace, points, selector):
        try:
            otaz = self.shapefile.index[points.point_inds[0]]
        except:
            pass
        else:
            self.otaz_dropdown.value = otaz

    def _change_matrix(self, payload):
        self.change_view(matrix_name=payload['new'])

    def _change_otaz(self, payload):
        self.change_view(otaz=payload['new'])

    def change_view(self, matrix_name=None, otaz=None):

        do_update = False

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




