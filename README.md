# A tool for exporting private messages from VK.COM social network

Exports dialogs to HTML file. Downloads attached images, stickers, handles and stores titles of audio that users have sent to each other (audio files itself are not downloaded), saves titles and VK-generated descriptions of external links that are accessible in dialogs, thumbnails of videos, links to documents uploaded to VK.COM servers and their names (documents itself are not downloaded), images of gifts users sent to each other, contents and attachments of posts shared by users in dialogs. Its purpose is to save as much information as possible, so you could save your messages and fully understand context and meaning of a dialog with another person.

You need to have Python > 3.4 to be installed on your computer in order to use the script.

To use it, you should edit `config.ini` file and enter login and password for your account. Now you can start the export by running

```
python vk-dialog-export.py
```

This script does not send nor stores your personal information or passwords elsewhere. Be careful not to expose sensitive information to third parties!

By default, the script exports all available dialogs, but you can export a single dialog too by providing one of the following options:

```
--person=PERSON_ID (to export dialog with this person)
--chat=CHAT_ID (to export a chat)
--group=GROUP_ID (to export dialog with a public group)
```

## Notes

This script is based on [vk-dialogue-export.py](https://github.com/coldmind/vk-dialogue-export.py), and [this pull request](https://github.com/coldmind/vk-dialogue-export.py/pull/7) but is completely rewritten.

Both scripts use [https://github.com/dzhioev/vk_api_auth](https://github.com/dzhioev/vk_api_auth) for OAuth authorization.
