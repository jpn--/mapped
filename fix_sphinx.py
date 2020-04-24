

def nth_repl(s, sub, repl, nth):
	find = s.find(sub)
	# if find is not p1 we have found at least one match for the substring
	i = find != -1
	# loop util we find the nth or we find no match
	while find != -1 and i != nth:
		# find + 1 means we start at the last match start index + 1
		find = s.find(sub, find + 1)
		i += 1
	# if i  is equal to nth we found nth matches so replace
	if i == nth:
		return s[:find]+repl+s[find + len(sub):]
	return s


if __name__ == '__main__':

	html_files = [
		'../mapped-docs/example-plotly-scatter.html',
		'../mapped-docs/example-plotly-lines.html',
		'../mapped-docs/example-plotly-density-heatmap.html',
		'../mapped-docs/example-plotly-choropleth.html',
		'../mapped-docs/example-basemap.html',
	]

	dupe_str = """        <script src="https://unpkg.com/@jupyter-widgets/html-manager@^0.18.0/dist/embed-amd.js"></script>
"""

	for html in html_files:
		print("repairing",html)
		with open(html, 'rt') as f:
			content = f.read()

		content = nth_repl(content, dupe_str, "", 2)

		with open(html, 'wt') as f:
			f.write(content)
