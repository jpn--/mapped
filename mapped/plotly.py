
try:
	import plotly.graph_objects as go
except ImportError:
	go = None

import geopandas as gpd
import contextily as ctx
import numpy as np


def good_zoom(gdf, low_tiles=1, high_tiles=3):
	"Find a good initial zoom level."
	crs = gdf.crs
	total_bounds = gdf.total_bounds
	if crs is None:
		raise ValueError
	from shapely.geometry import box
	mapping_area = gpd.GeoDataFrame(geometry=[box(*total_bounds)], crs=crs).to_crs(epsg=3857)
	xmin_, ymin_, xmax_, ymax_ = mapping_area.total_bounds  # w s e n
	zoom = 1
	low_zoom = 1
	tiles = {}
	tiles[zoom] = howmany = ctx.howmany(xmin_, ymin_, xmax_, ymax_, zoom, verbose=False)
	while howmany <= high_tiles:
		zoom += 1
		if howmany <= low_tiles:
			low_zoom += 1
		tiles[zoom] = howmany = ctx.howmany(xmin_, ymin_, xmax_, ymax_, zoom, verbose=False)
	return zoom - 1 + ((high_tiles - tiles[zoom - 1]) / (howmany - tiles[zoom - 1]))


def make_plotly_choropleth(
		gdf,
		column=None,
		colorscale="Viridis",
		zmin=None,
		zmax=None,
		opacity=0.5,
		line_width=0,
		center=None,
		zoom='auto',
		mapbox_style="carto-positron",
		margins=0,
		figuretype=None,
		show_colorbar=None,
		**kwargs,
):
	"""
	Make a choropleth in a plotly FigureWidget.

	Parameters
	----------
	gdf: geopandas.GeoDataFrame
		The areas to plot.
	column: Any or pandas.Series, optional
		The name of the column in `gdf` that contains the data to
		colorize the areas, or a Series of values to use that is
		indexed-alike with `gdf`.  If not given, all-zero data
		will be used.
	colorscale: str, default "Viridis"
		A plotly-compatible colorscale.
	zmin, zmax: float, optional
		Min and max for the colorbar range.
	marker_opacity: float, default 0.5
		Opacity of the choropleth areas.
	marker_line_width: float, default 0
		Thickness of the lines around the choropleth areas.  Zero
		results in a hairline border, not no border.
	center: dict, optional
		The initial centerpoint of the map.  If not given, the center
		of the gdf is used by default.  Give in {'lat':0, 'lon':0}
		format.
	zoom: 'auto' or int or float
		Sets the initial zoom level for the map.
	mapbox_style: str, default "carto-positron"
		Sets the style for the basemap tiles.  Options include
		"carto-positron", "stamen-terrain", "stamen-toner",
		"open-street-map", possibly others.
	margins: int, optional
		Set margins on the figure.
	figuretype: class, optional
		Which plotly figure class to use, defaults to
		plotly.go.FigureWidget.
	show_colorbar: bool, optional
		Whether to show the colorbar legend.  If not given explicitly,
		this will be set to True unless there is no `column`, in which
		case it will be False.

	Other keyword arguments are passed through to the
	plotly Choroplethmapbox constructor, allowing substantial customization
	of the resulting figure.

	Returns
	-------
	plotly.go.FigureWidget
	"""

	if figuretype is None:
		figuretype = go.FigureWidget

	gdf = gdf.to_crs(epsg=4326)
	hovertemplate = f"%{{z}}<extra>%{{location}}</extra>"

	if column is None:
		column = np.zeros_like(gdf.index)
		if show_colorbar is None:
			show_colorbar = False

	z = column
	try:
		if column in gdf:
			z = gdf[column]
	except:
		pass

	try:
		locations = z.index
	except:
		locations = gdf.index

	index_name = None
	try:
		index_name = locations.name
	except:
		pass
	if index_name is not None:
		index_name = f"{index_name} "
	else:
		index_name = ""

	try:
		name = z.name
	except:
		pass
	else:
		if name:
			hovertemplate = f"{name}: %{{z}}<extra>{index_name}%{{location}}</extra>"

	if show_colorbar is None:
		show_colorbar = True

	fig = figuretype(
		go.Choroplethmapbox(
			geojson=gdf.__geo_interface__,
			locations=locations,
			z=z,
			colorscale=colorscale,
			zmin=zmin,
			zmax=zmax,
			marker_opacity=opacity,
			marker_line_width=line_width,
			hovertemplate=hovertemplate,
			showscale=show_colorbar,
			**kwargs,
		)
	)

	if center is None:
		total_bounds = gdf.total_bounds
		center = dict(
			lon=(total_bounds[0] + total_bounds[2]) / 2,
			lat=(total_bounds[1] + total_bounds[3]) / 2,
		)

	if zoom == 'auto':
		zoom = good_zoom(gdf)

	fig.update_layout(
		mapbox_style=mapbox_style,
		mapbox_zoom=zoom,
		mapbox_center=center,
	)
	if isinstance(margins, int):
		fig.update_layout(margin={"r": margins, "t": margins, "l": margins, "b": margins})
	elif margins is not None:
		fig.update_layout(margin=margins)
	return fig



gpd.GeoDataFrame.plotly_choropleth = make_plotly_choropleth

