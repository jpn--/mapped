
import numpy as np
import pandas as pd
import geopandas as gpd
import warnings
from sklearn.neighbors import KernelDensity
from sklearn.base import clone
from matplotlib import pyplot as plt
from .basemap import add_basemap


class GeoMeshGrid(gpd.GeoDataFrame):
	"""A GeoDataFrame that contains a grid of points."""

	def __init__(self, bounds=None, num=50, crs=None, numx=None, numy=None, resolution=None, xlim=None, ylim=None):

		if bounds is None:
			if isinstance(xlim, slice):
				x0, x1 = xlim.start, xlim.stop
			else:
				x0, x1 = xlim
			if isinstance(ylim, slice):
				y0, y1 = ylim.start, ylim.stop
			else:
				y0, y1 = ylim
		elif isinstance(bounds, (np.ndarray, list, tuple)) and len(bounds) == 4:
			x0, y0, x1, y1 = bounds
		else:
			x0, y0, x1, y1 = bounds.total_bounds

		if crs is None and hasattr(bounds, 'crs'):
			crs = bounds.crs

		if resolution is not None:
			xy_ratio = (x1 - x0) / (y1 - y0)
			numy = int(np.sqrt((resolution ** 2) / xy_ratio))
			numx = int((resolution ** 2) / numy)

		if numx is None:
			numx = num
		if numy is None:
			numy = num

		gX, gY = np.meshgrid(
			np.linspace(x0, x1, numx),
			np.linspace(y0, y1, numy),
		)

		super().__init__(
			geometry=gpd.points_from_xy(gX.ravel(), gY.ravel()),
			crs=crs,
			index=pd.DataFrame(gX).stack().index,
		)

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			self.gridshape = (numy, numx)

	def contour(
			self,
			column,
			ax=None,
			levels=None,
			filled=False,
			basemap=None,
			crs=None,
			figsize=None,
			mask=None,
			column_mask=None,
			**kwargs,
	):
		shape = self.gridshape

		if ax is None:
			fig, ax = plt.subplots(figsize=figsize)

		func = ax.contourf if filled else ax.contour

		try:
			z = self[column]
		except KeyError:
			z = self.eval(column)

		if column_mask is not None:
			z[~(self.eval(column_mask))] = np.nan

		if mask is not None:
			if isinstance(mask, (gpd.GeoSeries, gpd.GeoDataFrame)):
				mask = self.within(mask.unary_union)

			z = z.copy()
			z[~mask] = np.nan

		func(
			self.geometry.x.values.reshape(shape),
			self.geometry.y.values.reshape(shape),
			z.values.reshape(shape),
			levels=levels,
			**kwargs,
		)

		if crs is None:
			crs = getattr(self, 'crs', crs)

		if isinstance(basemap, str):
			basemap = {'crs': crs, 'tiles': basemap}
		if basemap is True or basemap is 1:
			basemap = {'crs': crs}
		if basemap:
			ax = add_basemap(ax, **basemap)

		return ax

def meshgrid(bounds, num=50, crs=None, numx=None, numy=None, resolution=None):
	"""Create a grid of points as a GeoDataFrame."""

	if isinstance(bounds, (np.ndarray, list, tuple)) and len(bounds)==4:
		x0 ,y0 ,x1 ,y1 = bounds
	else:
		x0 ,y0 ,x1 ,y1 = bounds.total_bounds

	if crs is None and hasattr(bounds, 'crs'):
		crs = bounds.crs

	if resolution is not None:
		xy_ratio = (x1-x0)/(y1-y0)
		numy = int(np.sqrt((resolution**2)/xy_ratio))
		numx = int((resolution**2)/numy)

	if numx is None:
		numx = num
	if numy is None:
		numy = num

	gX ,gY = np.meshgrid(
		np.linspace(x0, x1, numx),
		np.linspace(y0, y1, numy),
	)

	points = gpd.GeoDataFrame(
		geometry=gpd.points_from_xy(gX.ravel(), gY.ravel()),
		crs=crs,
		index=pd.DataFrame(gX).stack().index,
	)

	if resolution is not None:
		return points, (numy, numx)

	return points

def mesh_shape(mesh):
	return (mesh.index.levels[0].max() + 1, mesh.index.levels[1].max() + 1)

def plot_mesh_contour(
		mesh,
		column,
		ax=None,
		levels=None,
		filled=False,
		basemap=None,
		crs=None,
		figsize=None,
		mask=None,
		column_mask=None,
		**kwargs,
):
	shape = mesh_shape(mesh)

	if ax is None:
		fig, ax = plt.subplots(figsize=figsize)

	func = ax.contourf if filled else ax.contour

	try:
		z = mesh[column]
	except KeyError:
		z = mesh.eval(column)

	if column_mask is not None:
		z[~(mesh.eval(column_mask))] = np.nan

	if mask is not None:
		if isinstance(mask, (gpd.GeoSeries, gpd.GeoDataFrame)):
			mask = mesh.within(mask.unary_union)

		z = z.copy()
		z[~mask] = np.nan

	func(
		mesh.geometry.x.values.reshape(shape),
		mesh.geometry.y.values.reshape(shape),
		z.values.reshape(shape),
		levels=levels,
		**kwargs,
	)

	if crs is None:
		crs = getattr(mesh, 'crs', crs)

	if isinstance(basemap, str):
		basemap = {'crs': crs, 'tiles': basemap}
	if basemap is True or basemap is 1:
		basemap = {'crs': crs}
	if basemap:
		ax = add_basemap(ax, **basemap)

	return ax


class GeoKernelDensities(dict):

	def __call__(self, target_points, copy=True):
		if copy:
			target_points = target_points.copy()
		target = target_points.to_crs(epsg=4326)
		latlon_radians = np.radians(np.vstack([
			target.geometry.y.values,
			target.geometry.x.values,
		]).T)
		for k in self.keys():
			target_points[k] = np.exp(self[k].score_samples(latlon_radians))
		if hasattr(self, 'agg'):
			target_points['agg'] = np.exp(self.agg.score_samples(latlon_radians))
		return target_points

	def point_grid(
			self,
			bounds=None,
			resolution=50,
			ax=None,
			crs=None,
			mesh=None,
			total=None,
	):

		if bounds is None and ax is not None:
			x0,x1 = ax.get_xlim()
			y0,y1 = ax.get_ylim()
			bounds = x0, y0, x1, y1
			if crs is None:
				raise ValueError("crs must be set if ax is given and bounds are not")

		if mesh is None:
			mesh = GeoMeshGrid(bounds, resolution=resolution, crs=crs)

		mesh = self(mesh, copy=False)

		if total:
			mesh[total] = mesh[list(self.keys())].sum(axis=1)

		return mesh

class GeoKernelDensity(KernelDensity):

	def __init__(self, bandwidth=1.0, algorithm='auto',
                 kernel='gaussian', metric="haversine", atol=0, rtol=0,
                 breadth_first=True, leaf_size=40, metric_params=None):
		bw = bandwidth
		if bandwidth is None:
			bandwidth = 1.0
		super().__init__(
			bandwidth=bandwidth, algorithm=algorithm,
			kernel=kernel, metric=metric,
			atol=atol, rtol=rtol,
			breadth_first=breadth_first, leaf_size=leaf_size, metric_params=metric_params
		)
		self.bandwidth = bw

	def fit(self, X, y=None, sample_weight=None):
		# instantiate and fit the KDE model

		if not isinstance(X, (gpd.GeoDataFrame, gpd.GeoSeries)):
			raise TypeError('GeoKernelDensity must be fit on GeoDataFrame or GeoSeries')

		self.source_crs = X.crs
		self.points = X.to_crs(epsg=4326)

		latlon = np.vstack([
			self.points.geometry.y.values,
			self.points.geometry.x.values,
		]).T

		self.latlon_radians = latlon_radians = np.radians(latlon)

		if self.bandwidth is None:
			self.bandwidth = (len(self.points)**(-1/6) * latlon_radians.std(0).mean())

		super().fit(latlon_radians)
		return self

	def multifit(self, X, column, agg=False):

		if not isinstance(X, (gpd.GeoDataFrame, )):
			raise TypeError('GeoKernelDensity must be multifit on GeoDataFrame')

		kernels = GeoKernelDensities()
		for c, cdata in X.groupby(column):
			kernels[c] = clone(self).fit(cdata)

		if agg:
			kernels.agg = clone(self).fit(X)

		return kernels

	def __call__(self, target_points, name="Z", copy=True):
		if copy:
			target_points = target_points.copy()
		target = target_points.to_crs(epsg=4326)
		latlon = np.vstack([
			target.geometry.y.values,
			target.geometry.x.values,
		]).T
		z = np.exp(self.score_samples(np.radians(latlon)))
		target_points[name] = z
		return target_points

	def point_grid(
			self,
			bounds=None,
			resolution=50,
			ax=None,
			crs=None,
			mesh=None,
			name="Z",
	):

		if bounds is None and ax is not None:
			x0,x1 = ax.get_xlim()
			y0,y1 = ax.get_ylim()
			bounds = x0, y0, x1, y1
			if crs is None:
				raise ValueError("crs must be set if ax is given and bounds are not")

		if bounds is None:
			if crs is None:
				bounds = self.points.to_crs(self.source_crs)
			else:
				bounds = self.points.to_crs(crs)

		if mesh is None:
			mesh, shape = meshgrid(bounds, resolution=resolution, crs=crs)
		else:
			shape = None
		mesh = self(mesh, name=name, copy=False)

		return mesh, shape



	def contour(self, bounds=None, resolution=50, levels=None,
				ax=None, figsize=None, filled=False,
				basemap=None, crs=None, **kwargs
				):

		if crs is None:
			crs = getattr(ax, 'crs', None)

		if bounds is None and ax is not None:
			x0,x1 = ax.get_xlim()
			y0,y1 = ax.get_ylim()
			bounds = x0, y0, x1, y1
			if crs is None:
				raise ValueError("crs must be set if ax is given and bounds are not")

		if bounds is None:
			if crs is None:
				bounds = self.points.to_crs(self.source_crs)
			else:
				bounds = self.points.to_crs(crs)

		if ax is None:
			fig, ax = plt.subplots(figsize=figsize)

		mesh, shape = meshgrid(bounds, resolution=resolution, crs=crs)
		mesh = self(mesh, name="Z", copy=False)

		func = ax.contourf if filled else ax.contour
		func(
			mesh.geometry.x.values.reshape(shape),
			mesh.geometry.y.values.reshape(shape),
			mesh["Z"].values.reshape(shape),
			levels=levels,
			**kwargs,
		)

		if crs is None:
			crs = getattr(bounds, 'crs', crs)

		if isinstance(basemap, str):
			basemap = {'crs': crs, 'tiles': basemap}
		if basemap is True or basemap is 1:
			basemap = {'crs': crs}
		if basemap:
			ax = add_basemap(ax, **basemap)

		return ax




