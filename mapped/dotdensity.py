import numpy as np
import pandas as pd
import geopandas as gpd
import shapely.geometry
from shapely.geometry import Point
from numpy.random import RandomState, uniform


def _gridded_polygon(poly, n, crs=None):
	"""
	Slice a polygon with a grid.

	Parameters
	----------
	poly : Polygon
	n : int or (int,int)
		Dimension of grid

	Returns
	-------
	chopped : GeoDataFrame
	"""

	if isinstance(n, int):
		n = (n,n)

	poly_df = gpd.GeoDataFrame(geometry=[poly], crs=crs)

	minx, miny, maxx, maxy = poly.bounds

	x_ = np.linspace(minx, maxx, n[0]+1)
	y_ = np.linspace(miny, maxy, n[1]+1)

	boxes = []
	for (y1, y2) in zip(y_[:-1], y_[1:]):
		for (x1, x2) in zip(x_[:-1], x_[1:]):
			boxes.append(shapely.geometry.box(x1, y1, x2, y2))

	grid = gpd.GeoDataFrame(geometry=gpd.GeoSeries(boxes, crs=poly_df.crs))

	chopped = gpd.overlay(poly_df, grid, how='identity')
	return chopped


def _generate_random_points_in_gridded_polygons(polys, num_points, seed=None):
	quant = (polys.area.cumsum() / polys.area.sum()) * num_points
	quant = quant.astype(int)
	quant.values[1:] = quant.values[1:] - quant.values[:-1]
	points = []
	for (poly, q) in zip(polys.geometry, quant):
		points.extend(generate_random_points_in_polygon(poly, q, seed=seed))
	return points


def _generate_random_points_in_polygon_grid(poly, num_points, n, seed=None, crs=None):
	g = _gridded_polygon(poly, n, crs=crs)
	points = _generate_random_points_in_gridded_polygons(g, num_points, seed=seed)
	return points


def generate_random_points_in_polygon(poly, num_points, seed=None):
	"""
	Create a list of randomly generated points within a polygon.

	Parameters
	----------
	poly : Polygon
	num_points : int
		The number of random points to create within the polygon
	seed : int, optional
		A random seed

	Returns
	-------
	List
	"""
	min_x, min_y, max_x, max_y = poly.bounds

	if poly.area < (max_x-min_x) * (max_y-min_y) * 0.25 and num_points > 5:
		return _generate_random_points_in_polygon_grid(poly, num_points, 4, seed=seed)

	points = []
	i = 0
	while len(points) < num_points:
		s = RandomState(seed + i) if seed else RandomState(seed)
		while True:
			random_point = Point([s.uniform(min_x, max_x), s.uniform(min_y, max_y)])
			if random_point.within(poly):
				break
		points.append(random_point)
		i += 1
	return points


def generate_points_in_areas(gdf, values, units_per_point=1, seed=None):
	"""
	Create a GeoSeries of random points in polygons.

	Parameters
	----------
	gdf : GeoDataFrame
		The areas in which to create points
	values : str or Series
		The [possibly scaled] number of points to create in each area
	units_per_point : numeric, optional
		The rate to scale the values in point generation.
	seed : int, optional
		A random seed

	Returns
	-------
	GeoSeries
	"""
	geometry = gdf.geometry
	if isinstance(values, str) and values in gdf.columns:
		values = gdf[values]
	new_values = (values / units_per_point).astype(int)
	g = gpd.GeoDataFrame(data={'vals': new_values}, geometry=geometry)
	a = g.apply(lambda row: tuple(generate_random_points_in_polygon(row['geometry'], row['vals'], seed)), 1)
	b = gpd.GeoSeries(a.apply(pd.Series).stack(), crs=geometry.crs)
	b.name = 'geometry'
	return b

gpd.GeoDataFrame.dotdensity = generate_points_in_areas
