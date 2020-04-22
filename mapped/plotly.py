
try:
	import plotly.graph_objects as go
	import plotly
	import plotly.express as px
except ImportError:
	go = None
	plotly = None
	px = None

import pandas as pd
import geopandas as gpd
import contextily as ctx
import numpy as np
import os

_MAPBOX_TOKEN_ = None
DEFAULT_OUTPUT_TYPE = go.FigureWidget

def load_mapbox_token(mapbox_token_file=".mapbox_token"):
	global _MAPBOX_TOKEN_
	if mapbox_token_file is None:
		_MAPBOX_TOKEN_ = None
	if os.path.exists(mapbox_token_file):
		_MAPBOX_TOKEN_ = open(mapbox_token_file).read()
	else:
		mapbox_token_file = os.path.expanduser(os.path.join("~", mapbox_token_file))
		if os.path.exists(mapbox_token_file):
			_MAPBOX_TOKEN_ = open(mapbox_token_file).read()

load_mapbox_token()

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


def _get_color(name):
	mods = [
		plotly.colors.cyclical,
		plotly.colors.qualitative,
		plotly.colors.diverging,
		plotly.colors.sequential,
	]
	for module in mods:
		try:
			return getattr(module, name)
		except:
			pass
	return name

### Patch for odd error
def _perform_plotly_relayout(self, relayout_data):
	"""
	Perform a relayout operation on the figure's layout data and return
	the changes that were applied
	Parameters
	----------
	relayout_data : dict[str, any]
		See the docstring for plotly_relayout
	Returns
	-------
	relayout_changes: dict[str, any]
		Subset of relayout_data including only the keys / values that
		resulted in a change to the figure's layout data
	"""
	# Initialize relayout changes
	# ---------------------------
	# This will be a subset of the relayout_data including only the
	# keys / values that are changed in the figure's layout data
	relayout_changes = {}

	# Process each key
	# ----------------
	for key_path_str, v in relayout_data.items():

		if not plotly.basedatatypes.BaseFigure._is_key_path_compatible(key_path_str, self.layout):
			if key_path_str != 'mapbox._derived':

				raise ValueError(
					"""
Invalid property path '{key_path_str}' for layout
""".format(
						key_path_str=key_path_str
					)
				)

		# Apply set operation on the layout dict
		val_changed = plotly.basedatatypes.BaseFigure._set_in(self._layout, key_path_str, v)

		if val_changed:
			relayout_changes[key_path_str] = v

	return relayout_changes



def plotly_choropleth(
		gdf,
		color=None,
		*,
		zoom='auto',
		mapbox_style=None,
		margins=0,
		figuretype=None,
		fig=None,
		center=None,
		opacity=0.5,
		text=None,
		**kwargs,
):
	"""
	Make a choropleth point map in a plotly FigureWidget.

	Parameters
	----------
	gdf: geopandas.GeoDataFrame
		The areas to plot.
	zoom: 'auto' or int or float
		Sets the initial zoom level for the map, up to 20.
	mapbox_style: str, optional
		Sets the style for the basemap tiles.  Totally free options
		include "carto-positron", "stamen-terrain", "stamen-toner",
		"open-street-map", possibly others.  Options from the set
		{'basic','streets','outdoors','light','dark','satellite',
		'satellite-streets'} will load vector tiles from MapBox,
		which requires a token to be set.  This defaults to
		"carto-positron" if no mapbox token is set, or 'basic'
		if a token is available.
	margins: int, optional
		Set margins on the figure.
	figuretype: class, optional
		Which plotly figure class to use, defaults to
		plotly.go.FigureWidget.
	fig: plotly.go.Figure or plotly.go.FigureWidget
		An existing figure, to which the new trace(s) will be
		appended.
	color: str or int or Series or array-like
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object. Values are used to assign color to markers.
	hover_name: str or int or Series or array-like
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object. Values appear in bold
		in the hover tooltip.
	hover_data: list of str or int, or Series or array-like
		Either names of columns in `gdf`, or pandas Series, or
		array_like objects Values appear as extra data in
		the hover tooltip.
	opacity: float, default 0.5
		Value between 0 and 1. Sets the opacity for markers.
	color_discrete_sequence: list of str
		Strings should define valid CSS-colors. When `color` is set and the
		values in the corresponding column are not numeric, values in that
		column are assigned colors by cycling through `color_discrete_sequence`
		in the order described in `category_orders`, unless the value of
		`color` is a key in `color_discrete_map`. Various useful color
		sequences are available in the `plotly.express.colors` submodules,
		specifically `plotly.express.colors.qualitative`.
	color_discrete_map: dict with str keys and str values (default `{}`)
		String values should define valid CSS-colors Used to override
		`color_discrete_sequence` to assign a specific colors to marks
		corresponding with specific values. Keys in `color_discrete_map` should
		be values in the column denoted by `color`.
	color_continuous_scale: list of str
		Strings should define valid CSS-colors This list is used to build a
		continuous color scale when the column denoted by `color` contains
		numeric data. Various useful color scales are available in the
		`plotly.express.colors` submodules, specifically
		`plotly.express.colors.sequential`, `plotly.express.colors.diverging`
		and `plotly.express.colors.cyclical`.
	range_color: list of two numbers
		If provided, overrides auto-scaling on the continuous color scale.
	color_continuous_midpoint: number (default `None`)
		If set, computes the bounds of the continuous color scale to have the
		desired midpoint. Setting this value is recommended when using
		`plotly.express.colors.diverging` color scales as the inputs to
		`color_continuous_scale`.
	width: int (default `None`)
		The figure width in pixels.
	height: int (default `600`)
		The figure height in pixels.
	**kwargs:
		Other keyword arguments are passed through to the
		plotly.express.choropleth_mapbox constructor, allowing substantial
		further customization of the resulting figure.

	Returns
	-------
	plotly.go.FigureWidget
	"""

	if mapbox_style is None:
		if _MAPBOX_TOKEN_ is None:
			mapbox_style = "carto-positron"
		else:
			mapbox_style = "light"

	if mapbox_style in {'basic','streets','outdoors','light','dark','satellite','satellite-streets'}:
		if _MAPBOX_TOKEN_ is None:
			raise ValueError(f'missing mapbox_token, required for mapbox_style={mapbox_style}\n'
							 'use mapped.plotly.load_mapbox_token to set this token'
							 )
		else:
			px.set_mapbox_access_token(_MAPBOX_TOKEN_)

	if figuretype is None:
		figuretype = DEFAULT_OUTPUT_TYPE

	gdf = gdf.to_crs(epsg=4326)

	plottable = pd.Series(data=True, index=gdf.index)

	gdf_p = gdf.loc[plottable]

	try:
		if zoom == 'auto':
			zoom = good_zoom(gdf_p)
	except:
		zoom = None

	if center is None:
		total_bounds = gdf.total_bounds
		center = dict(
			lon=(total_bounds[0] + total_bounds[2]) / 2,
			lat=(total_bounds[1] + total_bounds[3]) / 2,
		)

	if isinstance(color, str) and color not in gdf_p.columns:
		color = gdf_p.eval(color)

	px_choropleth = px.choropleth_mapbox(
		gdf_p,
		geojson=gdf.__geo_interface__,
		locations=gdf.index,
		color=color,
		zoom=zoom,
		mapbox_style=mapbox_style,
		hover_name=gdf_p.index,
		center=center,
		opacity=opacity,
		**kwargs,
	)
	if fig is None:
		fig = figuretype(px_choropleth)
		if isinstance(margins, int):
			fig.update_layout(margin={"r": margins, "t": margins, "l": margins, "b": margins})
		elif margins is not None:
			fig.update_layout(margin=margins)
		fig._perform_plotly_relayout = lambda y: _perform_plotly_relayout(fig, y)
	else:
		fig.add_traces(px_choropleth.data)

	if text is not None:
		if isinstance(text, str):
			if text in gdf:
				text = gdf[text].astype(str)
			elif text in gdf.index.names:
				text = gdf.index.get_level_values(text).astype(str)
			else:
				text = gdf.eval(text).astype(str)
		plotly_scatter(
			gdf,
			text=text,
			mapbox_style=mapbox_style,
			fig=fig,
			suppress_hover=True,
			mode='text',
		)
	return fig



gpd.GeoDataFrame.plotly_choropleth = plotly_choropleth
gpd.GeoSeries.plotly_choropleth = plotly_choropleth


def plotly_heatmap(
		gdf,
		z=None,
		*,
		radius=30,
		zoom='auto',
		mapbox_style=None,
		margins=0,
		figuretype=None,
		fig=None,
		**kwargs,
):
	"""
	Make a scatter point map in a plotly FigureWidget.

	Parameters
	----------
	gdf: geopandas.GeoDataFrame
		The areas to plot.
	zoom: 'auto' or int or float
		Sets the initial zoom level for the map, up to 20.
	mapbox_style: str, optional
		Sets the style for the basemap tiles.  Totally free options
		include "carto-positron", "stamen-terrain", "stamen-toner",
		"open-street-map", possibly others.  Options from the set
		{'basic','streets','outdoors','light','dark','satellite',
		'satellite-streets'} will load vector tiles from MapBox,
		which requires a token to be set.  This defaults to
		"carto-positron" if no mapbox token is set, or 'basic'
		if a token is available.
	margins: int, optional
		Set margins on the figure.
	figuretype: class, optional
		Which plotly figure class to use, defaults to
		plotly.go.FigureWidget.
	fig: plotly.go.Figure or plotly.go.FigureWidget
		An existing figure, to which the new trace(s) will be
		appended.
	radius: int (default is 30)
		Sets the radius of influence of each point.
	color: str or int or Series or array-like
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object. Values are used to assign color to markers.
	text: str or int or Series or array-like
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object. Values appear in the figure as text labels.
	hover_name: str or int or Series or array-like
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object. Values appear in bold
		in the hover tooltip.
	hover_data: list of str or int, or Series or array-like
		Either names of columns in `gdf`, or pandas Series, or
		array_like objects Values appear as extra data in
		the hover tooltip.
	opacity: float
		Value between 0 and 1. Sets the opacity for markers.
	size_max: int (default `20`)
		Set the maximum mark size when using `size`.
	title: str
		The figure title.
	width: int (default `None`)
		The figure width in pixels.
	height: int (default `600`)
		The figure height in pixels.
	**kwargs:
		Other keyword arguments are passed through to the
		plotly.express.scatter_mapbox constructor, allowing substantial
		further customization of the resulting figure.

	Returns
	-------
	plotly.go.FigureWidget
	"""

	if mapbox_style is None:
		if _MAPBOX_TOKEN_ is None:
			mapbox_style = "carto-positron"
		else:
			mapbox_style = "light"

	if mapbox_style in {'basic','streets','outdoors','light','dark','satellite','satellite-streets'}:
		if _MAPBOX_TOKEN_ is None:
			raise ValueError(f'missing mapbox_token, required for mapbox_style={mapbox_style}\n'
							 'use mapped.plotly.load_mapbox_token to set this token'
							 )
		else:
			px.set_mapbox_access_token(_MAPBOX_TOKEN_)

	if figuretype is None:
		figuretype = DEFAULT_OUTPUT_TYPE

	gdf = gdf.to_crs(epsg=4326)

	plottable = pd.Series(data=True, index=gdf.index)

	if isinstance(z, str):
		if z in gdf:
			z = gdf[z]
		else:
			z = gdf.eval(z)
	if z is not None:
		plottable &= ~pd.isna(z)

	gdf_p = gdf.loc[plottable]

	z_p = z
	if z is not None:
		try:
			z_p = z.loc[plottable]
		except AttributeError:
			pass

	try:
		if zoom == 'auto':
			zoom = good_zoom(gdf_p)
	except:
		zoom = None

	px_density = px.density_mapbox(
		gdf_p,
		lat=gdf_p.centroid.y,
		lon=gdf_p.centroid.x,
		z=z_p,
		radius=radius,
		zoom=zoom,
		mapbox_style=mapbox_style,
		hover_name=gdf_p.index,
		**kwargs,
	)

	if fig is None:
		fig = figuretype(px_density)
		if isinstance(margins, int):
			fig.update_layout(margin={"r": margins, "t": margins, "l": margins, "b": margins})
		elif margins is not None:
			fig.update_layout(margin=margins)
		fig._perform_plotly_relayout = lambda y: _perform_plotly_relayout(fig, y)
	else:
		fig.add_traces(px_density.data)
	return fig



gpd.GeoDataFrame.plotly_heatmap = plotly_heatmap



def plotly_scatter(
		gdf,
		*,
		zoom='auto',
		mapbox_style=None,
		margins=0,
		figuretype=None,
		fig=None,
		size=None,
		color=None,
		suppress_hover=False,
		mode=None,
		**kwargs,
):
	"""
	Make a scatter point map in a plotly FigureWidget.

	Parameters
	----------
	gdf: geopandas.GeoDataFrame
		The areas to plot.
	zoom: 'auto' or int or float
		Sets the initial zoom level for the map, up to 20.
	mapbox_style: str, optional
		Sets the style for the basemap tiles.  Totally free options
		include "carto-positron", "stamen-terrain", "stamen-toner",
		"open-street-map", possibly others.  Options from the set
		{'basic','streets','outdoors','light','dark','satellite',
		'satellite-streets'} will load vector tiles from MapBox,
		which requires a token to be set.  This defaults to
		"carto-positron" if no mapbox token is set, or 'basic'
		if a token is available.
	margins: int, optional
		Set margins on the figure.
	figuretype: class, optional
		Which plotly figure class to use, defaults to
		plotly.go.FigureWidget.
	fig: plotly.go.Figure or plotly.go.FigureWidget
		An existing figure, to which the new trace(s) will be
		appended.
	size: numeric
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object. Values from this column or array_like
		are used to assign marker sizes.  Missing values will not
		be plotted at all.
	color: str or int or Series or array-like
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object. Values are used to assign color to markers.
	text: str or int or Series or array-like
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object. Values appear in the figure as text labels.
	hover_name: str or int or Series or array-like
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object. Values appear in bold
		in the hover tooltip.
	hover_data: list of str or int, or Series or array-like
		Either names of columns in `gdf`, or pandas Series, or
		array_like objects Values appear as extra data in
		the hover tooltip.
	opacity: float
		Value between 0 and 1. Sets the opacity for markers.
	size_max: int (default `20`)
		Set the maximum mark size when using `size`.
	title: str
		The figure title.
	width: int (default `None`)
		The figure width in pixels.
	height: int (default `600`)
		The figure height in pixels.
	**kwargs:
		Other keyword arguments are passed through to the
		plotly.express.scatter_mapbox constructor, allowing substantial
		further customization of the resulting figure.

	Returns
	-------
	plotly.go.FigureWidget
	"""

	if mapbox_style is None:
		if _MAPBOX_TOKEN_ is None:
			mapbox_style = "carto-positron"
		else:
			mapbox_style = "light"

	if mapbox_style in {'basic','streets','outdoors','light','dark','satellite','satellite-streets'}:
		if _MAPBOX_TOKEN_ is None:
			raise ValueError(f'missing mapbox_token, required for mapbox_style={mapbox_style}\n'
							 'use mapped.plotly.load_mapbox_token to set this token'
							 )
		else:
			px.set_mapbox_access_token(_MAPBOX_TOKEN_)

	if figuretype is None:
		figuretype = DEFAULT_OUTPUT_TYPE

	gdf = gdf.to_crs(epsg=4326)

	plottable = pd.Series(data=True, index=gdf.index)

	if isinstance(size, str):
		if size in gdf:
			size = gdf[size]
		else:
			size = gdf.eval(size)
	if size is not None:
		plottable &= ~pd.isna(size)

	gdf_p = gdf.loc[plottable]

	size_p = size
	if size is not None:
		try:
			size_p = size.loc[plottable]
		except AttributeError:
			pass

	try:
		if zoom == 'auto':
			zoom = good_zoom(gdf_p)
	except:
		zoom = None

	if isinstance(color, str) and color not in gdf_p.columns:
		color = gdf_p.eval(color)

	px_scatter = px.scatter_mapbox(
		gdf_p,
		lat=gdf_p.centroid.y,
		lon=gdf_p.centroid.x,
		size=size_p,
		zoom=zoom,
		mapbox_style=mapbox_style,
		hover_name=gdf_p.index,
		color=color,
		**kwargs,
	)
	if mode is not None:
		for trace in px_scatter.data:
			trace.mode = mode
	if suppress_hover:
		for trace in px_scatter.data:
			trace.hoverinfo = 'skip'
			trace.hovertemplate = None

	if fig is None:
		fig = figuretype(px_scatter)
		if isinstance(margins, int):
			fig.update_layout(margin={"r": margins, "t": margins, "l": margins, "b": margins})
		elif margins is not None:
			fig.update_layout(margin=margins)
		fig._perform_plotly_relayout = lambda y: _perform_plotly_relayout(fig, y)
	else:
		fig.add_traces(px_scatter.data)
	return fig



gpd.GeoDataFrame.plotly_scatter = plotly_scatter


def _line_xy(line, buffer=1, xy=0):
	x = np.empty(len(line.xy[xy])+buffer, dtype=float)
	x[:-buffer] = line.xy[xy]
	x[-buffer:] = np.nan
	return x

def _line_x(line, buffer=1):
	return _line_xy(line, buffer=buffer, xy=0)

def _line_y(line, buffer=1):
	return _line_xy(line, buffer=buffer, xy=1)

def _add_lines_to_mapbox_figure(
		fig,
		gdf,
		name=None,
		suppress_hover=True,
		line=None,
		showlegend=True,
		opacity=None,
):
	if line is None:
		line = dict()
	fig.add_scattermapbox(
		mode="lines",
		lon=np.concatenate(gdf.geometry.apply(_line_x).values),
		lat=np.concatenate(gdf.geometry.apply(_line_y).values),
		name=name,
		line=line,
		showlegend=showlegend,
		opacity=opacity,
	)
	if suppress_hover:
		fig.data[-1].hoverinfo = 'skip'
		fig.data[-1].hovertemplate = None


def plotly_lines(
		gdf,
		*,
		zoom='auto',
		mapbox_style=None,
		margins=0,
		figuretype=None,
		fig=None,
		color=None,
		width=None,
		suppress_hover=False,
		opacity=None,
		color_discrete_sequence=None,
		color_discrete_map=None,
		**kwargs,
):
	"""
	Make a line map in a plotly FigureWidget.

	Parameters
	----------
	gdf: geopandas.GeoDataFrame
		The lines to plot.
	zoom: 'auto' or int or float
		Sets the initial zoom level for the map, up to 20.
	mapbox_style: str, optional
		Sets the style for the basemap tiles.  Totally free options
		include "carto-positron", "stamen-terrain", "stamen-toner",
		"open-street-map", possibly others.  Options from the set
		{'basic','streets','outdoors','light','dark','satellite',
		'satellite-streets'} will load vector tiles from MapBox,
		which requires a token to be set.  This defaults to
		"carto-positron" if no mapbox token is set, or 'basic'
		if a token is available.
	margins: int, optional
		Set margins on the figure.
	figuretype: class, optional
		Which plotly figure class to use, defaults to
		plotly.go.FigureWidget.
	fig: plotly.go.Figure or plotly.go.FigureWidget
		An existing figure, to which the new trace(s) will be
		appended.
	color: str or int or Series or array-like
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object. Values are used to assign color to lines.
	width: str or int or Series or array-like
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object. Values are used to assign widths to lines.
	opacity: float
		Value between 0 and 1. Sets the opacity for lines.
	title: str
		The figure title.
	width: int (default `None`)
		The figure width in pixels.
	height: int (default `600`)
		The figure height in pixels.
	**kwargs:
		Other keyword arguments are passed through to the
		plotly.express.scatter_mapbox constructor, allowing substantial
		further customization of the resulting figure.

	Notes
	-----
	A separate trace is generated for every unique combination of
	color and width, which can create a lot of traces and slow down
	the responsiveness of the figure.  It is better to use categorical
	values in these places.

	Returns
	-------
	plotly.go.FigureWidget
	"""

	if mapbox_style is None:
		if _MAPBOX_TOKEN_ is None:
			mapbox_style = "carto-positron"
		else:
			mapbox_style = "light"

	if mapbox_style in {'basic','streets','outdoors','light','dark','satellite','satellite-streets'}:
		if _MAPBOX_TOKEN_ is None:
			raise ValueError(f'missing mapbox_token, required for mapbox_style={mapbox_style}\n'
							 'use mapped.plotly.load_mapbox_token to set this token'
							 )
		else:
			px.set_mapbox_access_token(_MAPBOX_TOKEN_)

	if figuretype is None:
		figuretype = DEFAULT_OUTPUT_TYPE

	gdf = gdf.to_crs(epsg=4326)

	try:
		if zoom == 'auto':
			zoom = good_zoom(gdf)
	except:
		zoom = None

	if isinstance(color, str) and color not in gdf.columns:
		color = gdf.eval(color)
	elif color is not None and color in gdf.columns:
		color = gdf[color]

	if isinstance(width, str) and width not in gdf.columns:
		width = gdf.eval(width)
	elif width is not None and width in gdf.columns:
		width = gdf[width]

	grouping = []
	grouping_def = []

	if color is not None:
		grouping.append(color)
		grouping_def.append('color')

	if width is not None:
		grouping.append(width)
		grouping_def.append('width')

	if len(grouping) == 0:
		gdfs = [(None, gdf)]
	else:
		gdfs = gdf.groupby(grouping)

	extra_layer = False
	if fig is None:
		fig = plotly_scatter(gdf, zoom=zoom, figuretype=figuretype, margins=margins, **kwargs)
		extra_layer = True

	if color_discrete_map is not None:
		color_mapping = color_discrete_map.copy()
	else:
		color_mapping = {}

	if color_discrete_sequence is None:
		color_discrete_sequence = plotly.colors.DEFAULT_PLOTLY_COLORS
	color_discrete_sequence = _get_color(color_discrete_sequence)

	colors_in_legend = set()

	for def_n, gdf_n in gdfs:
		if len(grouping_def)<=1:
			def_n = [def_n]
		def_n_ = dict(zip(grouping_def, def_n))
		color_name = def_n_.get('color',None)
		if color_mapping.get(color_name) is None:
			color_mapping[color_name] = color_discrete_sequence[
				len(color_mapping) % len(color_discrete_sequence)
			]
		_add_lines_to_mapbox_figure(
			fig, gdf_n, name=color_name,
			suppress_hover=suppress_hover,
			line=dict(
				color=color_mapping[color_name],
				width=def_n_.get('width',None),
			),
			showlegend=(color_name not in colors_in_legend and color is not None),
			opacity=opacity,
		)
		colors_in_legend.add(color_name)
	if extra_layer:
		fig.data = fig.data[1:]
	fig.update_layout(legend_itemsizing='constant')
	return fig


gpd.GeoDataFrame.plotly_lines = plotly_lines








def make_plotly(gdf):
	"""
	A quick and dirty dynamic map to review data.

	Parameters
	----------
	gdf : GeoDataFrame or GeoSeries

	Returns
	-------
	plotly.go.FigureWidget

	"""
	if len(gdf):
		import shapely.geometry.point
		if isinstance(gdf.iloc[0].geometry, shapely.geometry.point.Point):
			m = plotly_heatmap(
				gdf
			)
		else:
			m = plotly_choropleth(
				gdf,
				line_width=2,
			)
		return m

gpd.GeoDataFrame.plotly = make_plotly
gpd.GeoSeries.plotly = make_plotly
