import json


class JSONExporter:
    def __init__(self, options):
        self.options = options

    @property
    def extension(self):
        return "json"

    def export(self, json_input, progress):
        return {
            'text': json.dumps(json_input, ensure_ascii=False, indent=2)
        }

