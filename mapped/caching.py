# -*- coding: utf-8 -*-

import appdirs
import joblib
import requests

cache_dir = None
memory = None


def set_cache_dir(location=None, compress=True, verbose=0, **kwargs):
	"""
	Set up a cache directory.

	Parameter
	---------
	location : Path-like or False, optional
		A path for the cache files.  Set to False to disable caching.
		If not given, a default location is used based on
		`appdirs.user_cache_dir`.
	compress : bool, default True
		see `joblib.Memory`.
	verbose : int, default 0
		see `joblib.Memory`.
	"""
	global memory, cache_dir

	if location is None:
		location = appdirs.user_cache_dir('mapped')

	if location is False:
		location = None

	memory = joblib.Memory(location, compress=compress, verbose=verbose, **kwargs)

	make_cache = (
		(requests, 'get'),
		(requests, 'post'),
	)

	for module, func_name in make_cache:
		try:
			func = getattr(module, f"_{func_name}_orig")
		except AttributeError:
			func = getattr(module, func_name)
			setattr(module, f"_{func_name}_orig", func)
		setattr(module, func_name, memory.cache(func))

set_cache_dir()


