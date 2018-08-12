[По-русски](https://github.com/zenwarr/vk-dialogue-export/blob/master/README-ru.md)

# A tool for exporting private messages from VK.COM social network

Exports dialogs to HTML file.
It downloads:
- Attached images
- Stickers
- Information about audio files (audio files are not downloaded by default, but you can turn it on)
- Titles and VK-generated descriptions of external links
- Video thumbnails
- Links to documents uploaded to VK servers and their names (document files are not downloaded by default, but you can turn it on)
- Images of gifts send to each other
- Contents and attachments of posts shared in dialogs
- Voice messages

Its purpose is to save as much information as possible, so you could save your messages and fully understand context and meaning of a dialog with another person.

You need to have Python > 3.4 to be installed on your computer in order to use the script.

To use it, you should give the script access to your account first.
There are several authentication methods supported.

1. Open `config.ini` file and enter your login and password instead of `YOUR_LOGIN` and `YOUR_PASSWORD`.

2. Just start the script and it will give you an url.
Open it in browser (or just press Enter in console) and give access to the application.
You will be redirected to an almost blank page.
Copy access_token and user_id parameters from URL and copy them into config.ini instead of `YOUR_ACCESS_TOKEN` and `YOUR_USER_ID`.

Now you can start the script with the following command:

```
python vk-dialog-export.py
```

This script does not send nor stores your personal information or passwords elsewhere except `config.ini` file.
Be careful not to expose sensitive information to third parties!

By default, output will be written inside `./out` directory.
You can set output directory with `--out=/home/user/out` option.

By default, the script exports all available dialogs, but you can export a single dialog too by providing one of the following options:

```
--person=PERSON_ID (to export dialog with this person)
--chat=CHAT_ID (to export a chat)
--group=GROUP_ID (to export dialog with a public group)
```

Also, the script does NOT download most of documents or audio files by default.
The only documents that are downloaded by default are voice messages.
You can use the following options to control what should be downloaded:

```
--docs (to download all documents)
--audio (to download all audio files)
--no-voice (to NOT download voice messages)
```

If you want to download only documents and audio files that are directly attached to the messages (not the ones attached to shared post), use the following options:

```
--docs-depth=0
--audio-depth=0
```

If `--docs-depth=1` or `--audio-depth=1`, documents and audio files attached to shared posts will be downloaded too.

Note: you still will not be able to download most audio files because vk.com has disabled its audio API for legal reasons.

By default dialogs are exported in HTML format, but you can export it in JSON as well.

```
--format=json (to export in json files)
--format=html (to export in html files, default)
```

Extra options for output format:

```
--embed-resources (to embed all styles or scripts in generated HTML, by default they are stored in separate files)
--save-raw (to save raw API resposes in JSON)
--save-json-in-html (to save messages in JSON format inside HTML export (JSON is going to be saved in `data-json` attribute on each message element)
```

## Notes

This script is based on [vk-dialogue-export.py](https://github.com/coldmind/vk-dialogue-export.py), and [this pull request](https://github.com/coldmind/vk-dialogue-export.py/pull/7) but is completely rewritten.

Both scripts use [https://github.com/dzhioev/vk_api_auth](https://github.com/dzhioev/vk_api_auth) for OAuth authorization.
