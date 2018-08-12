import argparse
import os
import sys


FORMAT_EXPORTERS = ['html', 'json']


class Options:
    def __init__(self):
        parser = argparse.ArgumentParser(description="Exports VK.COM messages into HTML files. "
                                                     "Login and password should be specified in config.ini file")
        parser.add_argument('--person', type=int, dest="person", help="ID of person whose dialog you want to export")
        parser.add_argument('--chat', type=int, dest="chat", help="ID of group chat which you want to export")
        parser.add_argument('--group', type=int, dest="group", help="ID of public group whose dialog you want to export")
        parser.add_argument('--docs', dest="docs", default=False, action="store_true", help="Do we need to download documents?")
        parser.add_argument('--docs-depth', dest="docs_depth", default=100, type=int,
                            help="If set to 0, only documents attached to the message itself will be downloaded. If set "
                            "to 1, documents from attached posts are going to be downloaded too, and so on. Default is 100")
        parser.add_argument('--audio', dest="audio", default=False, action="store_true", help="Do we need to download audio?")
        parser.add_argument('--audio-depth', dest="audio_depth", default=100, type=int,
                            help="If set to 0, only audio files attached to the message itself will be downloaded. If set "
                            "to 1, audio file from attached posts are going to be downloaded too, and so on. Default is 100")
        parser.add_argument('--no-voice', dest="no_voice", default=False, action="store_true",
                            help="Do not download voice messages")
        parser.add_argument('--out', dest="out", default="out", type=str, help="Directory for output files")
        parser.add_argument('--format', dest='format', default="html", type=str, help="Output format (html, json)")
        parser.add_argument('--save-raw', dest="save_raw", default=False, action='store_true', help="Save raw API responses in json")
        parser.add_argument('--save-json-in-html', dest="save_json_in_html", default=False, action='store_true', help="Store messages JSON in HTML output")
        parser.add_argument('--embed-resources', dest='embed_resources', default=False, action='store_true', help="Embed styles and scripts in generated HTML file")

        self.arguments = parser.parse_args()

        self.output_dir = self.arguments.out
        self.output_dir = os.path.abspath(os.path.expandvars(self.output_dir))
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        if not os.path.isdir(self.output_dir):
            sys.stderr.write("Failed to create output directory %s" % self.output_dir)
            sys.exit(-1)

        self.output_format = self.arguments.format.lower()

        if self.arguments.embed_resources and self.output_format != 'html':
            sys.stderr.write("--embed-resources is not allowed when output format is not HTML")

        if not (self.output_format in FORMAT_EXPORTERS):
            sys.stderr.write("Unknown format: %s" % self.output_format)

        sys.stdout.write('Output directory is %s\n' % self.output_dir)
