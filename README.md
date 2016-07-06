# A tool for exporting private messages from VK.COM social network

To use it, you should edit `config.ini` file and enter login and password for your account. Now you can start export by running

```
python vk-dialogue-export.py
```

By default, script exports all available dialogs, but you can export single dialog too by providing one of the following options:

```
--person=PERSON_ID (to export dialog with this person)
--chat=CHAT_ID (to export a chat)
--group=GROUP_ID (to export dialog with a public group)
```

## Notes

This script is based on [vk-dialogue-export.py](https://github.com/coldmind/vk-dialogue-export.py), and [this pull request](https://github.com/coldmind/vk-dialogue-export.py/pull/7) but is completely rewritten.

Both scripts use [https://github.com/dzhioev/vk_api_auth](https://github.com/dzhioev/vk_api_auth) for OAuth authorization.
