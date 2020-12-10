
import geopandas as gpd

def centroid_internal(gdf):
	"""
	Get centroids if they are within polygons, otherwise a representative internal point.

	Parameters
	----------
	gdf : GeoDataFrame

	Returns
	-------
	GeoSeries

	"""
	points = gdf.centroid
	fails = ~points.within(gdf)
	points[fails] = gdf[fails].representative_point()
	points.crs = gdf.crs
	return points

def make_points_geodataframe(df, lat, lon):

	"""
	Create a GeoDataFrame from a regular DataFrame that has lat and lon columns.

	Parameters
	----------
	df : DataFrame
	lat, lon : str
		The column names containing latitude and longitude.
	"""
	return gpd.GeoDataFrame(
		geometry=gpd.points_from_xy(
			df[lon],
			df[lat],
		),
		data=df,
		crs='EPSG:4326',
	)

def make_pointpairs_geodataframe(df, olat, olon, dlat, dlon):

	"""
	Create a GeoDataFrame from a DataFrame that has two pairs of lat and lon columns.

	Parameters
	----------
	df : DataFrame
	olat, olon, dlat, dlon : str
		The column names containing latitude and longitude of origin and destination.
	"""
	from shapely.geometry.multipoint import MultiPoint
	vectors = [
		MultiPoint([p0, p1])
		for p0, p1 in zip(
			gpd.points_from_xy(
				df[olon],
				df[olat],
			),
			gpd.points_from_xy(
				df[dlon],
				df[dlat],
			)
		)
	]
	return gpd.GeoDataFrame(
		geometry=vectors,
		data=df,
		crs='EPSG:4326',
	)


def annotate_map(ax, gdf, annot, row_slice=slice(None), **kwargs):
	"""
	Add annotations to a map.

	Parameters
	----------
	ax : Axes
	gdf : GeoDataFrame
	annot : str
		This is a format string, which will be populated
		using each row of `gdf`.
	row_slice : Slice, optional
		The slice of rows from `gdf` to use for annotation.
		This slice is passed to the `.loc` indexer.
	**kwargs
		Other keyword arguments are passed through to the
		`ax.annotate` command.
	"""
	gdf.loc[row_slice].apply(
		lambda x: ax.annotate(
			s=annot.format(**x),
			xy=x.geometry.centroid.coords[0],
			horizontalalignment='center',
			**kwargs,
		),
		axis=1,
	)