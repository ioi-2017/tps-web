from trader.exporters.json import *

AVAILABLE_EXPORTERS = (
    (loader.short_name, loader) for loader in [JSONExporter]
)
