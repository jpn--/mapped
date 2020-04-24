import contextily as ctx
import geopandas as gpd
from matplotlib import pyplot as plt
from pyproj import CRS
from rasterio.errors import CRSError

def make_basemap(
		xlim,
		ylim,
		figsize=(10, 10),
		axis=None,
		*,
		tiles=None,
		zoom='auto',
		crs=None,
		epsg=None,
):
	"""
	Initialize a map plot with a basemap.

	Parameters
	----------
	xlim, ylim: 2-tuple
		The extent of the map on the X and Y axis, respectively.
	figsize: tuple
		The size of the map to render.  This argument is passed to
		plt.subplots.
	axis: str, optional
		Set to "off" to remove the axis and axis labels.
	tiles: str
		The base url to use for the map tile, or a named value in
		contextily.sources, for example: OSM_A, ST_TERRAIN, ST_TONER_LITE.
		See `https://github.com/geopandas/contextily/blob/master/contextily/_providers.py`
		for other named values.
	zoom: int, or 'auto'
		The zoom level of the map tiles to download.  Note that this does
		not actually change the magnification of the rendered map, just the size
		and level of detail in the mapping tiles used to render a base map.
		Selecting a zoom level that is too high will result in a large download
		with excessive detail (and unreadably small labels, if labels are included
		in the tiles).
	crs: dict, optional
		The coordinate reference system of the map being rendered.  Map tiles are
		all in web mercator (epsg:3857), so if the map is some other CRS, it must
		be given so that the correctly aligned tiles can be loaded.
	epsg: int, optional
		You may specify a crs as an epsg integer here instead of using the `crs`
		argument.

	Returns
	-------
	AxesSubplot
	"""

	if epsg is not None:
		crs = {'init': f'epsg:{epsg}'}
	if crs is None:
		crs = {'init': f'epsg:3857'}

	fig, ax = plt.subplots(figsize=figsize)
	ax.set_aspect("equal")
	if axis is not None:
		ax.axis(axis)  # don't show axis?
	ax.set_xlim(*xlim)
	ax.set_ylim(*ylim)
	if tiles is not None:
		ax = add_basemap(ax, zoom=zoom, tiles=tiles, crs=crs)
	return ax



def add_basemap(
		ax,
		zoom='auto',
		tiles='CartoDB.Positron',
		crs=None,
		epsg=None,
		axis='off',
		figsize=None,
		**kwargs,
):
	"""
	Add a basemap to a matplotlib map plot.

	Parameters
	----------
	ax: AxesSubplot
		The extent of the map is inferred from the axes, and the tiles are
		then rendered onto these axes.
	zoom: int, or 'auto'
		The zoom level of the map tiles to download.  Note that this does
		not actually change the magnification of the rendered map, just the size
		and level of detail in the mapping tiles used to render a base map.
		Selecting a zoom level that is too high will result in a large download
		with excessive detail (and unreadably small labels, if labels are included
		in the tiles).
	tiles: str
		The base url to use for the map tile, or a named value in
		contextily.sources, for example: "OpenStreetMap", "Stamen.Terrain", "Stamen.TonerLite".
		See `https://github.com/geopandas/contextily/blob/master/contextily/_providers.py`
		for other possible values.
	crs: dict, optional
		The coordinate reference system of the map being rendered.  Map tiles are
		all in web mercator (epsg:3857), so if the map is some other CRS, it must
		be given so that the correctly aligned tiles can be loaded.  This function
		will also look for a `crs` attribute on `ax`, and it will prefer to use any
		crs defined there over a crs given here.
	epsg: int, optional
		You may specify a crs as an epsg integer here instead of using the `crs`
		argument.
	axis: str or None, default "off"
		Set to "off" to remove the axis and axis labels, or "on" to draw axis labels.
		Set to None to leave the axis settings unchanged.
	figsize: tuple
		The size of the map to render.  This argument is passed to
		fig.set_size_inches.

	Returns
	-------
	AxesSubplot
	"""
	providers = None
	if isinstance(tiles, str):
		providers = ctx.providers
		tiles_dots = tiles.split('.')
		while len(tiles_dots):
			if tiles_dots[0] in providers:
				providers = providers[tiles_dots[0]]
				try:
					tiles_dots = tiles_dots[1:]
				except IndexError:
					tiles_dots = []
			else:
				providers = None
				break
		while isinstance(providers, dict) and 'url' not in providers and len(providers):
			providers = next(iter(providers.values()))
		if not isinstance(providers, dict) or len(providers) == 0:
			providers = None
	elif isinstance(tiles, dict):
		providers = tiles

	if providers is not None:
		url = providers
		attribution_txt = providers.get('attribution', None)
	else:
		url = getattr(ctx.sources, tiles, tiles)
		attribution_txt = None

	if epsg is not None:
		crs = {'init': f'epsg:{epsg}'}
	crs = getattr(ax, 'crs', crs)

	try:
		ctx.add_basemap(
			ax,
			zoom=zoom,
			source=url,
			crs=crs,
			**kwargs,
		)
	except CRSError as err:
		epsg = crs.to_epsg()
		if epsg:
			ctx.add_basemap(
				ax,
				zoom=zoom,
				source=url,
				crs=CRS(f"epsg:{epsg}"),
				**kwargs,
			)
		else:
			raise

	if axis is not None:
		ax.axis(axis)  # don't show axis

	if figsize:
		ax.get_figure().set_size_inches(figsize)

	# if default crs was used, attach it to ax
	ax.crs = crs if crs is not None else {'init': f'epsg:3897'}

	return ax

def _plot_with_basemap(self, *args, basemap=False, **kwargs, ):
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

	if 'ax' in kwargs:
		crs = getattr(kwargs['ax'], 'crs', None)
		if crs is not None:
			try:
				self = self.to_crs(crs)
			except:
				pass
	crs = getattr(self, 'crs', None)
	ax = gpd.geodataframe.plot_dataframe(self, *args, **kwargs)
	if isinstance(basemap, str):
		basemap = {'crs': crs, 'tiles':basemap}
	if basemap is True or basemap is 1:
		basemap = {'crs': crs}
	if basemap:
		ax = add_basemap( ax, **basemap )
	if not hasattr(ax, 'crs') and crs is not None:
		ax.crs = crs
	return ax

gpd.GeoDataFrame.plot = _plot_with_basemap

def _plot_series_with_basemap(self, *args, basemap=False, **kwargs, ):
	"""
	Plot a GeoSeries.

	Generate a plot of a GeoSeries geometry with matplotlib.

	Parameters
	----------
	s : Series
	    The GeoSeries to be plotted. Currently Polygon,
	    MultiPolygon, LineString, MultiLineString and Point
	    geometries can be plotted.
	cmap : str (default None)
	    The name of a colormap recognized by matplotlib. Any
	    colormap will work, but categorical colormaps are
	    generally recommended. Examples of useful discrete
	    colormaps include:

	        tab10, tab20, Accent, Dark2, Paired, Pastel1, Set1, Set2

	color : str (default None)
	    If specified, all objects will be colored uniformly.
	ax : matplotlib.pyplot.Artist (default None)
	    axes on which to draw the plot
	figsize : pair of floats (default None)
	    Size of the resulting matplotlib.figure.Figure. If the argument
	    ax is given explicitly, figsize is ignored.
	basemap : dict or bool, default False
		Whether to render a basemap behind the plot.
	**style_kwds : dict
	    Color options to be passed on to the actual plot function, such
	    as ``edgecolor``, ``facecolor``, ``linewidth``, ``markersize``,
	    ``alpha``.

	Returns
	-------
	ax : matplotlib axes instance
	"""
	if 'ax' in kwargs:
		crs = getattr(kwargs['ax'], 'crs', None)
		if crs is not None:
			try:
				self = self.to_crs(crs)
			except:
				pass
	crs = getattr(self, 'crs', None)
	ax = gpd.geoseries.plot_series(self, *args, **kwargs)
	if isinstance(basemap, str):
		basemap = {'crs': crs, 'tiles':basemap}
	if basemap is True or basemap is 1:
		basemap = {'crs': crs}
	if basemap:
		if 'crs' not in basemap:
			basemap['crs'] = crs
		ax = add_basemap( ax, **basemap )
	if not hasattr(ax, 'crs') and crs is not None:
		ax.crs = crs
	return ax

gpd.GeoSeries.plot = _plot_series_with_basemap