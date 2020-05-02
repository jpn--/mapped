
import pandas as pd
import geopandas as gpd
import plotly.express as px
from ..basemap import add_basemap
from .. import plotly

DPI = 72

def _choropleth_matplotlib(
		gdf,
		*args,
		basemap='CartoDB.Positron',
		zoom='auto',
		annot=None,
		legend=True,
		**kwargs,
):
	"""
	Plot a GeoDataFrame.

	Generate a plot of a GeoDataFrame with matplotlib.  If a
	column is specified, the plot coloring will be based on values
	in that column.

	Parameters
	----------
	df : GeoDataFrame
		The GeoDataFrame to be plotted.  Currently Polygon,
		MultiPolygon, LineString, MultiLineString and Point
		geometries can be plotted.
	column : str, np.array, pd.Series (default None)
		The name of the dataframe column, np.array, or pd.Series to be plotted.
		If np.array or pd.Series are used then it must have same length as
		dataframe. Values are used to color the plot. Ignored if `color` is
		also set.
	cmap : str (default None)
		The name of a colormap recognized by matplotlib.
	color : str (default None)
		If specified, all objects will be colored uniformly.
	ax : matplotlib.pyplot.Artist (default None)
		axes on which to draw the plot
	cax : matplotlib.pyplot Artist (default None)
		axes on which to draw the legend in case of color map.
	categorical : bool (default False)
		If False, cmap will reflect numerical values of the
		column being plotted.  For non-numerical columns, this
		will be set to True.
	legend : bool (default False)
		Plot a legend. Ignored if no `column` is given, or if `color` is given.
	scheme : str (default None)
		Name of a choropleth classification scheme (requires mapclassify).
		A mapclassify.MapClassifier object will be used
		under the hood. Supported are all schemes provided by mapclassify (e.g.
		'BoxPlot', 'EqualInterval', 'FisherJenks', 'FisherJenksSampled',
		'HeadTailBreaks', 'JenksCaspall', 'JenksCaspallForced',
		'JenksCaspallSampled', 'MaxP', 'MaximumBreaks',
		'NaturalBreaks', 'Quantiles', 'Percentiles', 'StdMean',
		'UserDefined'). Arguments can be passed in classification_kwds.
	k : int (default 5)
		Number of classes (ignored if scheme is None)
	vmin : None or float (default None)
		Minimum value of cmap. If None, the minimum data value
		in the column to be plotted is used.
	vmax : None or float (default None)
		Maximum value of cmap. If None, the maximum data value
		in the column to be plotted is used.
	markersize : str or float or sequence (default None)
		Only applies to point geometries within a frame.
		If a str, will use the values in the column of the frame specified
		by markersize to set the size of markers. Otherwise can be a value
		to apply to all points, or a sequence of the same length as the
		number of points.
	figsize : tuple of integers (default None)
		Size of the resulting matplotlib.figure.Figure. If the argument
		axes is given explicitly, figsize is ignored.
	legend_kwds : dict (default None)
		Keyword arguments to pass to ax.legend()
	classification_kwds : dict (default None)
		Keyword arguments to pass to mapclassify
	basemap : dict or bool, default False
		Whether to render a basemap behind the plot.
	annot : str, np.array, pd.Series (default None)
		The name of the dataframe column, np.array, or pd.Series used to
		annotate areas in the plot.
		If np.array or pd.Series are used then it must have same length as
		dataframe. Values are used to color the plot. Ignored if `color` is
		also set.

	**style_kwds : dict
		Color options to be passed on to the actual plot function, such
		as ``edgecolor``, ``facecolor``, ``linewidth``, ``markersize``,
		``alpha``.

	Returns
	-------
	ax : matplotlib axes instance

	"""
	from matplotlib import pyplot as plt

	ax = kwargs.pop('ax', None)
	if ax is not None:
		crs = getattr(ax, 'crs', None)
		if crs is not None:
			try:
				gdf = gdf.to_crs(crs)
			except:
				pass
	crs = getattr(gdf, 'crs', None)

	figsize = kwargs.pop('figsize', None)
	if ax is None:
		fig, ax = plt.subplots(figsize=figsize)
	ax.set_aspect("equal")

	legend_kwds = kwargs.pop('legend_kwds', {})
	if 'column' in kwargs:
		if isinstance(kwargs['column'], str):
			legend_kwds['label'] = kwargs['column']
		elif hasattr(kwargs['column'], 'name'):
			legend_kwds['label'] = kwargs['column'].name
	elif len(args)>0:
		if isinstance(args[0], str):
			legend_kwds['label'] = args[0]
		elif hasattr(args[0], 'name'):
			legend_kwds['label'] = args[0].name
	if isinstance(legend, str):
		legend_kwds['label'] = legend
		legend = True

	try:
		ax = gpd.geodataframe.plot_dataframe(
			gdf, *args, ax=ax, legend=legend, legend_kwds=legend_kwds,
			**kwargs
		)
	except KeyError:
		if len(args) > 0:
			ax = gpd.geodataframe.plot_dataframe(
				gdf, gdf.eval(args[0]), *args[1:], ax=ax,
				legend=legend, legend_kwds=legend_kwds, **kwargs
			)
		else:
			column = kwargs.pop('column')
			ax = gpd.geodataframe.plot_dataframe(
				gdf, column=gdf.eval(column), ax=ax, legend=legend,
				legend_kwds=legend_kwds, **kwargs
			)
	if isinstance(basemap, str):
		basemap = {'crs': crs, 'tiles':basemap}
	if basemap is True or basemap is 1:
		basemap = {'crs': crs}
	if basemap:
		ax = add_basemap( ax, zoom=zoom, **basemap )
	if not hasattr(ax, 'crs') and crs is not None:
		ax.crs = crs
	if annot is not None:
		if annot in gdf.columns:
			annot = "{"+annot+"}"
		from ..simple import annotate_map
		annotate_map(ax, gdf, annot, row_slice=slice(None))
	return ax



def _plotly_choropleth(
		gdf,
		color=None,
		*,
		zoom='auto',
		mapbox_style=None,
		margins=0,
		figuretype=None,
		fig=None,
		center=None,
		opacity=1.0,
		text=None,
		figsize=None,
		legend=True,
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
	legend: bool (default True)
		Whether to show a legend.
	**kwargs:
		Other keyword arguments are passed through to the
		plotly.express.choropleth_mapbox constructor, allowing substantial
		further customization of the resulting figure.

	Returns
	-------
	plotly.go.FigureWidget
	"""

	if mapbox_style is None:
		if plotly._MAPBOX_TOKEN_ is None:
			mapbox_style = "carto-positron"
		else:
			mapbox_style = "light"

	if mapbox_style in {'basic','streets','outdoors','light','dark','satellite','satellite-streets'}:
		if plotly._MAPBOX_TOKEN_ is None:
			raise ValueError(f'missing mapbox_token, required for mapbox_style={mapbox_style}\n'
							 'use mapped.plotly.load_mapbox_token to set this token'
							 )
		else:
			px.set_mapbox_access_token(plotly._MAPBOX_TOKEN_)

	if figuretype is None:
		figuretype = plotly.DEFAULT_OUTPUT_TYPE

	gdf = gdf.to_crs(epsg=4326)

	plottable = pd.Series(data=True, index=gdf.index)

	gdf_p = gdf.loc[plottable]

	try:
		if zoom == 'auto':
			zoom = plotly.good_zoom(gdf_p)
	except:
		zoom = None

	if center is None:
		total_bounds = gdf.total_bounds
		center = dict(
			lon=(total_bounds[0] + total_bounds[2]) / 2,
			lat=(total_bounds[1] + total_bounds[3]) / 2,
		)

	if isinstance(color, str) and color not in gdf_p.columns:
		color_str = color
		color = gdf_p.eval(color).rename(color_str)

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
		if figsize is not None:
			fig.update_layout(
				autosize=False,
				width=figsize[0]*DPI,
				height=figsize[1]*DPI,
			)

		fig._perform_plotly_relayout = lambda y: plotly._perform_plotly_relayout(fig, y)
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
		plotly.plotly_scatter(
			gdf,
			text=text,
			mapbox_style=mapbox_style,
			fig=fig,
			suppress_hover=True,
			mode='text',
		)
	if not legend:
		fig.layout.coloraxis.showscale = False
	return fig

_plotly_mapbox_styles = {
	'CartoDB.Positron':'carto-positron',
	'CartoDB.DarkMatter': 'carto-darkmatter',
	'Stamen.Terrain': 'stamen-terrain',
	'Stamen.Toner': 'stamen-toner',
	'Stamen.Watercolor': 'stamen-watercolor',
	True: None,
	False: 'white-bg',
}

_folium_tiles = {
	'CartoDB.Positron': 'CartoDB Positron',
	'CartoDB.DarkMatter': 'CartoDB dark_matter',
	'Stamen.Terrain': 'Stamen Terrain',
	'Stamen.Toner': 'Stamen Toner',
	'Stamen.Watercolor': 'Stamen Watercolor',
	'OpenStreetMap': 'OpenStreetMap',
	True: 'CartoDB Positron',
}

def _folium_choropleth(
		gdf,
		color,
		fill_opacity=1.0,
		line_opacity=0.3,
		line_width=1,
		legend_name=None,
		zoom='auto',
		tiles='CartoDB Positron',
		ax=None,
		nan_color="#faded1",
		line_color='black',
		hover_line_color='blue',
		tooltip_fields = None,
):
	import folium

	if isinstance(color, str) and legend_name is None:
		legend_name = color

	try:
		if zoom == 'auto':
			zoom = plotly.good_zoom(gdf)+1
	except:
		zoom = 8

	gdf = gdf.to_crs(epsg=4326)

	if isinstance(color, str) and color not in gdf.columns:
		color_str = color
		color = gdf.eval(color).rename(color_str)
		color.index = color.index.astype(str)
	elif color in gdf.columns:
		color = gdf[color]
		color.index = color.index.astype(str)

	total_bounds = gdf.total_bounds
	center = (
		(total_bounds[1] + total_bounds[3]) / 2,
		(total_bounds[0] + total_bounds[2]) / 2,
	)

	tiles = _folium_tiles.get(tiles, tiles)

	if ax is None:
		ax = folium.Map(center, zoom_start=zoom, tiles=tiles)

	from branca import colormap

	colormapper = colormap.linear.viridis.scale(
		color.min(),
		color.max(),
	)
	if legend_name:
		colormapper.caption = legend_name

	def colormapper_with_nan(x):
		if nan_color and pd.isna(x):
			return nan_color
		else:
			return colormapper(x)


	_tooltip_fields = [color.name]
	if tooltip_fields is not None:
		for tt in tooltip_fields:
			if tt not in _tooltip_fields:
				_tooltip_fields.append(tt)

	gdf_j = gpd.GeoDataFrame(
		color.values,
		index=gdf.index,
		geometry=gdf.geometry,
		columns=[color.name],
	)

	for ttf in _tooltip_fields[1:]:
		if ttf in gdf.columns:
			gdf_j[ttf] = gdf[ttf]
		else:
			gdf_j[ttf] = gdf.eval(ttf)


	folium.GeoJson(
		gdf_j,
		style_function=lambda feature: {
			'fillColor': colormapper_with_nan(feature['properties'][color.name]),
			'color': line_color,
			'weight': line_width,
			'opacity': line_opacity,
			'fillOpacity': fill_opacity,
		},
		highlight_function=lambda feature: {
			'color': hover_line_color,
			'weight': line_width+2,
		},
		tooltip=folium.GeoJsonTooltip(
			fields=_tooltip_fields,
		),
	).add_to(ax)
	colormapper.add_to(ax)

	# folium.Choropleth(
	# 	geo_data=gdf.__geo_interface__,
	# 	data=color,
	# 	key_on='feature.id',
	# 	fill_color='YlGn',
	# 	fill_opacity=fill_opacity,
	# 	line_opacity=line_opacity,
	# 	line_width=line_width,
	# 	legend_name=legend_name,
	# ).add_to(ax)

	return ax

def choropleth(
		gdf,
		*,
		engine='matplotlib',
		ax=None,
		fig=None,
		color=None,
		opacity=1.0,
		text=None,
		basemap=True,
		zoom='auto',
		figsize=None,
		missing_value=None,
		**kwargs
):
	"""
	Make a choropleth point map in a plotly FigureWidget.

	Parameters
	----------
	gdf: geopandas.GeoDataFrame
		The areas to plot.
	engine: {'matplotlib', 'plotly'}
		Which data visualization engine to use.  Matplotlib
		generates static images.  Plotly is slower but
		generates dynamic maps that you can pan and zoom.
	ax: matplotlib.Axes or plotly.Figure, optional
		Add this choropleth to an existing figure. Aliased
		as `fig` also.
	color: str or int or Series or array-like, optional
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object, or a string that can be evaluated on `gdf`.
		Values are used to assign color to areas on the map.
	opacity: float, default 1.0
		The opacity of the fill areas.
	text: str or int or Series or array-like, optional
		Either a name of a column in `gdf`, or a pandas Series or
		array_like object, or a string that can be evaluated on `gdf`.
		Values are used to assign text labels to areas on the map.
	basemap: str or bool, default True
		The name of the map tiles used to generate the basemap for this
		choropleth.  Set to `True` to get the default tiles,
		or `False` to not use background tiles at all.
	legend: bool (default True)
		Plot a legend.
	zoom: 'auto' or int or float
		Sets the initial zoom level for the map, up to 20.
	figsize: tuple of numbers (default None)
		Size of the resulting Figure. If the argument `ax` is given
		explicitly, figsize is ignored.
	**kwargs:
		Other keyword arguments are forwarded to the engine's drawing
		command.
	"""
	if ax is None:
		ax = fig
	if ax is not None:
		if 'matplotlib' in repr(type(ax)):
			engine = 'matplotlib'
		elif 'plotly' in repr(type(ax)):
			engine = 'plotly'
		elif 'folium' in repr(type(ax)):
			engine = 'folium'

	if isinstance(color, str) and color not in gdf.columns:
		color_str = color
		color = gdf.eval(color).rename(color_str)
	elif isinstance(color, str) and color in gdf.columns:
		color = gdf[color].copy()

	if missing_value is not None:
		try:
			color = color.fillna(missing_value)
		except:
			pass

	# Make infinite values in range.
	lo = color[np.isfinite(color)].min()
	hi = color[np.isfinite(color)].max()
	color[np.isposinf(color)] = hi + (hi-lo)*0.05
	color[np.isneginf(color)] = lo - (hi-lo)*0.05

	if engine == 'matplotlib':
		return _choropleth_matplotlib(
			gdf,
			column=color,
			basemap=basemap,
			zoom=zoom,
			figsize=figsize,
			annot=text,
			ax=ax,
			alpha=opacity,
			**kwargs,
		)
	elif engine == 'plotly':
		return _plotly_choropleth(
			gdf,
			color=color,
			mapbox_style=_plotly_mapbox_styles.get(basemap, basemap),
			zoom=zoom,
			figsize=figsize,
			text=text,
			fig=ax,
			opacity=opacity,
			**kwargs,
		)
	elif engine == 'folium':
		return _folium_choropleth(
			gdf,
			color=color,
			fill_opacity=opacity,
			line_opacity=max(opacity,0.3),
			legend_name=None,
			zoom=zoom,
			tiles=basemap,
			ax=ax,
		)
	else:
		raise ValueError(f"mapping engine '{engine}' not found")