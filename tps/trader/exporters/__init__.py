from trader.exporters.json import *

AVAILABLE_EXPORTER_CLASSES = [
    JSONExporter,
]

AVAILABLE_EXPORTERS = [
    (loader, loader.short_name) for loader in AVAILABLE_EXPORTER_CLASSES
]
