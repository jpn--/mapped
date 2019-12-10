# -*- coding: utf-8 -*-

import appdirs
import joblib
import requests
import re
import contextily as ctx

cache_dir = None
memory = None

ctx.tile.USER_AGENT = "contextily-mapped-py"

def _get_tile_urls(providers):
	urls = []
	for k in providers.keys():
		if isinstance(providers[k], dict):
			urls.extend(_get_tile_urls(providers[k]))
			url = providers[k].get('url', None)
			if url is not None:
				subdomains = providers[k].get("subdomains", "abc")
				if not isinstance(subdomains, str):
					subdomains = "".join(subdomains)
				s = "["+subdomains+"]"
				fmt = dict(
					x="[0-9]*",
					y="[0-9]*",
					z="[0-9]*",
					s=s,
					r = providers[k].get("r", ""),
				)
				url = url.format(**fmt, **providers[k])
				url = url.split("?")[0]
				url = "(^"+url+")"
				urls.append(url)
	return urls

_tile_urls = _get_tile_urls(ctx.providers)
_nominatim = [
	"(^https://nominatim.openstreetmap.org/search)",
	"(^http://overpass-api.de/api)",
]
_map_url_filter = re.compile("|".join(_tile_urls+_nominatim))


def get_with_cache(url, *args, **kwrags):
	global _map_url_filter
	if _map_url_filter.match(url):
		return requests._get_cached(url, *args, **kwrags)
	else:
		return requests._get_orig(url, *args, **kwrags)

def post_with_cache(url, *args, **kwrags):
	global _map_url_filter
	if _map_url_filter.match(url):
		return requests._post_cached(url, *args, **kwrags)
	else:
		return requests._post_orig(url, *args, **kwrags)



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
		(requests, 'get', get_with_cache),
		(requests, 'post', post_with_cache),
	)

	for module, func_name, replace_func in make_cache:
		try:
			func = getattr(module, f"_{func_name}_orig")
		except AttributeError:
			func = getattr(module, func_name)
			setattr(module, f"_{func_name}_orig", func)
		setattr(module, f"_{func_name}_cached", memory.cache(func))
		setattr(module, func_name, replace_func)

set_cache_dir()


