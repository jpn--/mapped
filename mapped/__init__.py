# Mapped
# Copyright (C) 2020 Jeffrey Newman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .basemap import make_basemap, add_basemap
from .plotly import plotly_choropleth, plotly_scatter, plotly_heatmap, plotly_lines
from . import caching
from .dotdensity import generate_points_in_areas
from .simple import centroid_internal, make_points_geodataframe
from .gdf_viewer import GeoDataFrameViz as Viz
from .omx_viewer import OMXViz
from geopandas import GeoDataFrame, GeoSeries

__version__ = "20.04.01"
