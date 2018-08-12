# -*- coding: utf-8 -*-


from exporter import *
from api import *
from options import *
from html_exporter import *
from json_exporter import *


def fetch_all_dialogs(api):
    offset = 0
    while True:
        dialogs = api.call("messages.getDialogs", [("offset", offset), ("count", 200)])
        if len(dialogs['items']) == 0:
            return
        for dialog in dialogs['items']:
            yield dialog
        offset += len(dialogs['items'])


api = VkApi()
if not api.initialize():
    sys.exit(-1)


options = Options()


exporters = []

if options.arguments.person is not None:
    exporters = [DialogExporter(api, 'user', options.arguments.person, options)]
elif options.arguments.chat is not None:
    exporters = [DialogExporter(api, 'chat', options.arguments.chat, options)]
elif options.arguments.group is not None:
    exporters = [DialogExporter(api, 'group', options.arguments.group, options)]
else:
    sys.stdout.write('You have not provided any specific dialogs to export, assuming you want to export them all...\n')
    sys.stdout.write('Enumerating your dialogs...\n')
    for dialog in fetch_all_dialogs(api):
        exporter = None

        last_msg = dialog['message']

        if 'chat_id' in last_msg:
            # this is a group chat
            exporter = DialogExporter(api, 'chat', last_msg['chat_id'], options)
        else:
            exporter = DialogExporter(api, 'user', last_msg['user_id'], options)

        exporters.append(exporter)

if not options.arguments.docs:
    sys.stdout.write('Attached documents are not downloaded by default. Restart the script with --docs to enable downloading documents\n')

sys.stdout.write('Exporting {0} dialog{1}\n'.format(len(exporters), 's' if len(exporters) > 1 else ''))
progress.total_stages = len(exporters)
for exp in exporters:
    exported_json = exp.export()

    format_exporter = None
    if options.output_format == 'json':
        format_exporter = JSONExporter(options)
    elif options.output_format == 'html':
        format_exporter = HTMLExporter(options)
    else:
        raise RuntimeError("Unknown format")

    exported_data = format_exporter.export(exported_json, progress)
    with codecs.open(os.path.join(options.output_dir, str(exp.id) + "." + format_exporter.extension), "w", encoding="utf-8") as f:
        f.write(exported_data['text'])

    if 'files' in exported_data:
        for filename, content in exported_data['files'].items():
            with codecs.open(os.path.join(options.output_dir, filename), 'w', encoding='utf-8') as f:
                f.write(content)

    progress.next_stage()
