
import numpy as np
import pandas as pd
import geopandas as gpd
import warnings
from sklearn.neighbors import KernelDensity
from sklearn.base import clone
from matplotlib import pyplot as plt
from .basemap import add_basemap

class GeoMeshGrid(gpd.GeoDataFrame):
	"""
	A GeoDataFrame that contains a grid of points.

	This is a specially constructed GeoDataFrame that contains
	points arrayed in a grid, for use in plotting contours,
	heatmaps, and related visualizations.  All initialization
	arguments must be given as keyword parameters.

	Parameters
	----------
	bounds : array-like or GeoData
		This either provides boundaries of the grid in
		(left, bottom, right, top) format, or is an object
		with a `total_bounds` property that gives same.
	num : int, default 50
		The dimensionality of the grid of points to create.
	crs : any
		Something that can be interpreted successfully as
		a coordinate reference system.
	numx, numy : int, optional
		Create an explicit non-square grid by giving the
		x and y dimensionality explictly.
	resolution : int, optional
		Create a non-square grid by giving an approximate
		square root of the total number of points in the
		grid.  x and y dimensions will be selected in
		proportion to the ratio of the total range of these
		dimensions.
	xlim, ylim : 2-tuple or slice, optional
		These can be used intead of the `bounds` argument.
	"""

	_metadata = gpd.GeoDataFrame._metadata + ['gridshape',]

	def __init__(self, *args, bounds=None, num=50, crs=None, numx=None, numy=None, resolution=None, xlim=None, ylim=None):

		if len(args):
			super().__init__(*args)
		else:

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

	@property
	def _constructor(self):
		return GeoMeshGrid

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
			ax.set_aspect("equal")

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




class GeoKernelDensities(dict):

	@property
	def bandwidth(self):
		return next(iter(self.values())).bandwidth

	@property
	def crs(self):
		return next(iter(self.values())).crs

	def __call__(self, target_points, copy=True):
		if copy:
			target_points = target_points.copy()
		target = target_points.to_crs(epsg=4326)
		latlon_radians = np.radians(np.vstack([
			target.geometry.y.values,
			target.geometry.x.values,
		]).T)
		for k in self.keys():
			target_points[k] = np.exp(self[k].score_samples(latlon_radians)) * self[k].total_sample_weight
		if hasattr(self, 'agg'):
			target_points['agg'] = np.exp(self.agg.score_samples(latlon_radians)) * self.agg.total_sample_weight
		return target_points

	def meshgrid(
			self,
			bounds=None,
			resolution=50,
			ax=None,
			crs=None,
			mesh=None,
			total=None,
			add_prior=0,
	):

		if mesh is None:
			if bounds is None and ax is not None:
				x0,x1 = ax.get_xlim()
				y0,y1 = ax.get_ylim()
				bounds = x0, y0, x1, y1
				if crs is None:
					crs = getattr(ax, 'crs', None)
				if crs is None:
					raise ValueError("crs must be set if ax is given and bounds are not")

			if hasattr(self, 'agg'):
				if bounds is None:
					if crs is None:
						bounds = self.agg.points.to_crs(self.crs)
					else:
						bounds = self.agg.points.to_crs(crs)

			mesh = GeoMeshGrid(bounds=bounds, resolution=resolution, crs=crs)

		mesh = self(mesh, copy=False)

		if add_prior:
			mesh = self.add_prior(mesh, prior=add_prior, total=total)
		elif total:
			mesh[total] = mesh[list(self.keys())].sum(axis=1)

		return mesh

	def add_prior(self, mesh, prior=1, total=None, inplace=False):
		if not inplace:
			mesh = mesh.copy()
		gross_sample_weight = sum(self[k].total_sample_weight for k in self.keys())
		orig_total = mesh[list(self.keys())].values.sum()
		prior *= orig_total / gross_sample_weight
		for k in self.keys():
			mesh[k] += prior * self[k].total_sample_weight / gross_sample_weight
		if total:
			mesh[total] = mesh[list(self.keys())].sum(axis=1)
		if not inplace:
			return mesh

class GeoKernelDensity(KernelDensity):

	def __init__(
			self,
			bandwidth=1.0,
			algorithm='auto',
			kernel='gaussian',
			metric="haversine",
			atol=0,
			rtol=0,
			breadth_first=True,
			leaf_size=40,
			metric_params=None,
	):
		bw = bandwidth
		if bandwidth is None:
			bandwidth = 1.0
		super().__init__(
			bandwidth=bandwidth, algorithm=algorithm,
			kernel=kernel, metric=metric,
			atol=atol, rtol=rtol,
			breadth_first=breadth_first, leaf_size=leaf_size,
			metric_params=metric_params
		)
		self.bandwidth = bw

	def fit(self, X, y=None, sample_weight=None):
		# instantiate and fit the KDE model

		if not isinstance(X, (gpd.GeoDataFrame, gpd.GeoSeries)):
			raise TypeError('GeoKernelDensity must be fit on GeoDataFrame or GeoSeries')

		self.crs = X.crs
		self.points = X.to_crs(epsg=4326)

		latlon = np.vstack([
			self.points.geometry.y.values,
			self.points.geometry.x.values,
		]).T

		self.latlon_radians = latlon_radians = np.radians(latlon)

		if self.bandwidth is None:
			self.bandwidth = (len(self.points)**(-1/6) * latlon_radians.std(0).mean())

		if sample_weight is not None and sample_weight.min() <= 0:
			if sample_weight.max() <= 0:
				raise ValueError("sample_weight must have some positive values")
			use_sample_weight = sample_weight[sample_weight>0]
			super().fit(latlon_radians[sample_weight>0,:], sample_weight=use_sample_weight)
			self.total_sample_weight = use_sample_weight.sum()
		else:
			super().fit(latlon_radians, sample_weight=sample_weight)
			if sample_weight is not None:
				self.total_sample_weight = sample_weight.sum()
			else:
				self.total_sample_weight = latlon_radians.shape[0]
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
		target_points[name] = z * self.total_sample_weight
		return target_points

	def meshgrid(
			self,
			bounds=None,
			resolution=50,
			ax=None,
			crs=None,
			mesh=None,
			name="Z",
	):

		if mesh is None:
			if bounds is None and ax is not None:
				x0,x1 = ax.get_xlim()
				y0,y1 = ax.get_ylim()
				bounds = x0, y0, x1, y1
				if crs is None:
					crs = getattr(ax, 'crs', None)
				if crs is None:
					raise ValueError("crs must be set if ax is given and bounds are not")

			if bounds is None:
				if crs is None:
					bounds = self.points.to_crs(self.crs)
				else:
					bounds = self.points.to_crs(crs)

			mesh = GeoMeshGrid(bounds=bounds, resolution=resolution, crs=crs)

		mesh = self(mesh, name=name, copy=False)

		return mesh



	def contour(
			self,
			bounds=None,
			resolution=50,
			levels=None,
			ax=None,
			figsize=None,
			filled=False,
			basemap=None,
			crs=None,
			mesh=None,
			mask=None,
			name="Z",
			**kwargs,
	):

		if crs is None:
			crs = getattr(ax, 'crs', None)

		mesh = self.meshgrid(
			bounds=bounds,
			resolution=resolution,
			ax=ax,
			crs=crs,
			mesh=mesh,
			name=name,
		)

		return mesh.contour(
			column=name,
			ax=ax,
			levels=levels,
			filled=filled,
			basemap=basemap,
			crs=crs,
			figsize=figsize,
			mask=mask,
			column_mask=None,
			**kwargs,
		)





