
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
		crs={'init': 'epsg:4326'}
	)
