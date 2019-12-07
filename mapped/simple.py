

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

