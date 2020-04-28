import logging
import ipywidgets as widgets

class OutputWidgetHandler(logging.Handler):
	""" Custom logging handler sending logs to an output widget """

	def __init__(self, *args, **kwargs):
		super(OutputWidgetHandler, self).__init__(*args, **kwargs)
		layout = {
			'border': '1px solid red',
		}
		self.out = widgets.Output(layout=layout)

	def emit(self, record):
		""" Overload of logging.Handler method """
		formatted_record = self.format(record)
		with self.out:
			print(formatted_record)

	def clear_logs(self):
		""" Clear the current logs """
		self.out.clear_output()


logger = logging.getLogger("mapped")
handler = OutputWidgetHandler()
handler.setFormatter(logging.Formatter('%(asctime)s  - [%(levelname)s] %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
