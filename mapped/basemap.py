import contextily as ctx
import geopandas as gpd
from matplotlib import pyplot as plt

def make_basemap(
		xlim,
		ylim,
		figsize=(10, 10),
		axis=None,
		*,
		tiles=None,
		zoom='auto',
		max_tiles=20,
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
		See `https://github.com/darribas/contextily/blob/master/contextily/tile_providers.py`
		for other named values.
	zoom: int, or 'auto'
		The zoom level of the map tiles to download.  Note that this does
		not actually change the magnification of the rendered map, just the size
		and level of detail in the mapping tiles used to render a base map.
		Selecting a zoom level that is too high will result in a large download
		with excessive detail (and unreadably small labels, if labels are included
		in the tiles).
	max_tiles: int, default 20
		The maximum number of map tiles to download for this basemap.  Used only
		if `zoom` is 'auto', in which case `zoom` is set to the highest level that
		will result in not more than this many map tiles being loaded.
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
	if axis is not None:
		ax.axis(axis)  # don't show axis?
	ax.set_xlim(*xlim)
	ax.set_ylim(*ylim)
	if tiles is not None:
		ax = add_basemap(ax, zoom=zoom, max_tiles=max_tiles, tiles=tiles, crs=crs)
	return ax


def add_basemap(
		ax,
		zoom='auto',
		max_tiles=20,
		tiles='http://tile.stamen.com/terrain/tileZ/tileX/tileY.png',
		crs=None,
		epsg=None,
		axis='off',
		figsize=(10, 10),
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
	max_tiles: int, default 20
		The maximum number of map tiles to download for this basemap.  Used only
		if `zoom` is 'auto', in which case `zoom` is set to the highest level that
		will result in not more than this many map tiles being loaded.
	tiles: str
		The base url to use for the map tile, or a named value in
		contextily.sources, for example: OSM_A, ST_TERRAIN, ST_TONER_LITE.
		See `https://github.com/darribas/contextily/blob/master/contextily/tile_providers.py`
		for other named values.
	crs: dict, optional
		The coordinate reference system of the map being rendered.  Map tiles are
		all in web mercator (epsg:3857), so if the map is some other CRS, it must
		be given so that the correctly aligned tiles can be loaded.
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

	url = getattr(ctx.sources, tiles, tiles)

	xmin, xmax = ax.get_xlim()
	ymin, ymax = ax.get_ylim()

	if epsg is not None:
		crs = {'init': f'epsg:{epsg}'}

	if crs is not None:
		from shapely.geometry import box
		mapping_area = gpd.GeoDataFrame(geometry=[box(xmin, ymin, xmax, ymax)], crs=crs).to_crs(epsg=3857)
		xmin_, ymin_, xmax_, ymax_ = mapping_area.total_bounds # w s e n
		if zoom == 'auto':
			zoom = 1
			while ctx.howmany(xmin_, ymin_, xmax_, ymax_, zoom+1, verbose=False) <= max_tiles:
				zoom += 1
		basemap, extent_ = ctx.bounds2img(xmin_, ymin_, xmax_, ymax_, zoom=zoom, url=url)
		xmin_, xmax_, ymin_, ymax_ = extent_
		xmin_, ymin_, xmax_, ymax_ = tuple(gpd.GeoDataFrame(geometry=[box(xmin_, ymin_, xmax_, ymax_)], crs={'init': 'epsg:3857'}).to_crs(crs).total_bounds)
		extent = (xmin_, xmax_, ymin_, ymax_)
	else:
		if zoom == 'auto':
			zoom = 1
			while ctx.howmany(xmin, ymin, xmax, ymax, zoom+1, verbose=False) <= max_tiles:
				zoom += 1
		basemap, extent = ctx.bounds2img(xmin, ymin, xmax, ymax, zoom=zoom, url=url)
	ax.imshow(basemap, extent=extent, interpolation='bilinear')
	# restore original x/y limits
	ax.axis((xmin, xmax, ymin, ymax))

	if 'openstreetmap.org' in url:
		attribution_html = (
			"""Map tiles and data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under """
			"""<a href="http://www.openstreetmap.org/copyright">ODbL</a>."""
		)
		attribution_txt = (
			"""Map tiles and data by OpenStreetMap, under ODbL."""
		)
	elif 'stamen.com' in url:
		attribution_html = (
			"""Map tiles by <a href="http://stamen.com">Stamen Design</a>, """
			"""under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. """
			"""Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under """
			"""<a href="http://www.openstreetmap.org/copyright">ODbL</a>."""
		)
		attribution_txt = (
			"""Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL."""
		)
	else:
		attribution_txt = None

	if attribution_txt:
		ax.annotate(
			attribution_txt,
			xy=(1.0, 0.0), xycoords='axes fraction',
			xytext=(0, -10), textcoords='offset points',
			horizontalalignment='right',
			fontstyle='italic',
			fontsize=8,
		)

	if axis is not None:
		ax.axis(axis)  # don't show axis

	if figsize:
		ax.get_figure().set_size_inches(figsize)

	return ax




def _plot_with_basemap(self, *args, basemap=False, **kwargs, ):
	ax = gpd.geodataframe.plot_dataframe(self, *args, **kwargs)
	if isinstance(basemap, str):
		basemap = {'crs': self.crs, 'tiles':basemap}
	if basemap is True or basemap is 1:
		basemap = {'crs': self.crs}
	if basemap:
		ax = add_basemap( ax, **basemap )
	return ax

gpd.GeoDataFrame.plot = _plot_with_basemap