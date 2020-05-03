

def what(filename, geopandas='geopandas'):
	"""
	Search a file or directory and report how to load any geo data found.

	This function doesn't do anything itself, it just tells a user
	(via `print`) how to import whatever geo data it finds.

	Parameters
	----------
	filename: Path-like
		The file or directory to search.
	geopandas: str, default 'geopandas'
		The name of the geopandas library in the current namespace,
		used to give the import commands needed to get the data.
	"""
	import os
	import fiona
	if os.path.isfile(filename):
		if os.path.splitext(filename)[1].lower() == '.zip':
			from zipfile import ZipFile, BadZipFile
			try:
				zf = ZipFile(filename)
			except BadZipFile:
				print(f"BadZipFile:{filename}")
			else:
				for name in zf.namelist():
					if name[-5:].lower() == '.gdb/':
						print(f"GeoDataBase:{filename}!{name}")
						layers = fiona.listlayers(f"zip://{filename}!{name}")
						if layers:
							print("  layers:")
							for layer in layers:
								loader = f"{geopandas}.read_file('zip://{filename}!{name}', driver='FileGDB', layer='{layer}')"
								print(f"    - {layer}")
								print(f"      `{loader}`")
					if name[-4:].lower() == '.shp':
						loader = f"{geopandas}.read_file('zip://{filename}!{name}')"
						print(f"Shapefile:{filename}!{name}")
						print(f"  `{loader}`")
		if os.path.splitext(filename)[1].lower() == '.shp':
			loader = f"{geopandas}.read_file('{filename}')"
			print(f"Shapefile:{filename}")
			print(f"  `{loader}`")
	elif os.path.isdir(filename):
		if os.path.splitext(filename)[1].lower() == '.gdb':
			try:
				layers = fiona.listlayers(filename)
			except:
				pass
			else:
				if layers:
					print(f"GeoDataBase:{filename}")
					print("  layers:")
					for layer in layers:
						loader = f"{geopandas}.read_file('{filename}', driver='FileGDB', layer='{layer}')"
						print(f"    - {layer}")
						print(f"      `{loader}`")
		for dirpath, dirnames, filenames in os.walk(filename):
			for subfilename in filenames:
				what(os.path.join(dirpath, subfilename), geopandas=geopandas)
