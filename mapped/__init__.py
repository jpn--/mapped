# Mapped
# Copyright (C) 2019 Jeffrey Newman
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
from .plotly import make_plotly_choropleth
from . import caching
from .dotdensity import generate_points_in_areas
from .simple import centroid_internal, make_points_geodataframe
from geopandas import GeoDataFrame, GeoSeries

__version__ = "20.01.0"
