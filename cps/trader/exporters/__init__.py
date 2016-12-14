from trader.exporters.json import *

AVAILABLE_EXPORTERS = [
    (loader, loader.short_name) for loader in [JSONExporter]
]
