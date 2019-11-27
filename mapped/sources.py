

from contextily import providers as _providers

def list_sources(providers=None):
	sources = []
	if providers is None:
		providers = _providers
	for k,v in providers:
		if 'url' in v:
			sources.append(k)
		elif isinstance(v,dict):
			sources.extend([f'{k}.{i}' for i in list_sources(v)])
	return sources

