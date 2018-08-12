import os
import urllib
from progress import *
from utils import *


class ExportContext:
    def __init__(self, user_fetcher, depth=0, users=None):
        self.depth = depth
        self.user_fetcher = user_fetcher
        self.users = users if users is not None else dict()

    def add_user(self, user_id, exporter=None):
        if user_id not in self.users:
            self.users[user_id] = self.user_fetcher.get_data(user_id, exporter)

    def next_level(self):
        return ExportContext(self.user_fetcher, self.depth, self.users)


class UserFetcher:
    def __init__(self, api):
        self.api = api
        self.cache = dict()

    def get_data(self, user_id, exporter=None):
        if not (user_id in self.cache):
            if user_id < 0:
                groups = self.api.call("groups.getById", [("group_id", str(-user_id))])
                data = groups[0]

                downloaded = None
                if exporter is not None:
                    downloaded = exporter.download_image(data)

                self.cache[user_id] = {
                    'name': data['name'],
                    'first_name': data['name'],
                    'last_name': '',
                    'link': 'https://vk.com/%s' % data['screen_name'],
                    'filename': downloaded
                }
            else:
                users = self.api.call("users.get", [("user_ids", str(user_id)), ("fields", "photo_50")])
                data = users[0]

                downloaded = None
                if exporter is not None:
                    downloaded = exporter.download_image(data)

                self.cache[user_id] = {
                    'name': '%s %s' % (data['first_name'], data['last_name']),
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'link': 'https://vk.com/id%s' % data['id'],
                    'filename': downloaded
                }
        return self.cache[user_id]


progress = Progress()


class DialogExporter:
    def __init__(self, api, dlg_type, dlg_id, options):
        self.api = api
        self.type = dlg_type
        self.id = dlg_id
        self.attach_dir = str(self.id)
        self.output_dir = options.output_dir
        self.options = options
        self.user_fetcher = UserFetcher(api)

        self.json_out = {
            'messages': []
        }

    def find_largest(self, obj, key_override='photo_'):
        def get_photo_keys():
            for k, v in iter(obj.items()):
                if k.startswith(key_override):
                    yield k[len(key_override):]

        return "%s%s" % (key_override, max(map(lambda k: int(k), get_photo_keys())))

    def download_file(self, url, out_filename, auto_image_ext=False, size=-1):
        if not url:
            # blocked documents or audio files go here
            return None

        abs_attach_dir = os.path.join(self.output_dir, self.attach_dir)
        if not os.path.exists(abs_attach_dir):
            os.makedirs(abs_attach_dir)
        elif not os.path.isdir(abs_attach_dir):
            raise OSError("Unable to create attachments directory %s" % abs_attach_dir)

        rel_out_path = esc("%s/%s" % (self.attach_dir, out_filename))
        abs_out_path = os.path.join(self.output_dir, rel_out_path)
        has_ext = len(os.path.splitext(rel_out_path)[1]) > 0
        if has_ext and os.path.exists(abs_out_path) and os.stat(abs_out_path).st_size > 0:
            return rel_out_path  # file was already downloaded?
        elif not has_ext and auto_image_ext:
            downloaded_image = has_downloaded_image(abs_attach_dir, out_filename)
            if downloaded_image is not None:
                return os.path.join(self.attach_dir, downloaded_image)

        def update_progress():
            display_filename = out_filename
            if auto_image_ext and not has_ext:
                display_filename = out_filename + '.jpg'  # we cannot determine it right now, but jpg is common, so...
            if size > 0:
                display_filename += ', ' + fmt_size(size)
            progress.step_msg('%s -> %s' % (url, display_filename))

        def try_download(src_url):
            nonlocal out_filename
            nonlocal rel_out_path
            nonlocal abs_out_path
            nonlocal has_ext

            try:
                request = urllib.request.urlopen(src_url, timeout=20)
                if not has_ext and auto_image_ext and 'Content-Type' in request.info():
                    ext = '.' + guess_image_ext(request.info()['Content-Type'])
                    out_filename = out_filename + ext
                    rel_out_path = rel_out_path + ext
                    abs_out_path = abs_out_path + ext
                    has_ext = True
                    update_progress()
                with open(abs_out_path, 'wb') as f:
                    f.write(request.read())
                    return True
            except Exception:
                return None

        update_progress()
        try:
            try_count = 0
            while try_count < 3:
                # sys.stdout.write("Downloading photo %s\n" % (message["id"]))
                if try_download(url):
                    return rel_out_path
                try_count += 1
        finally:
            progress.clear_step_msg()

        progress.error("Failed to retrieve file (%s) after 3 attempts, skipping\n" % url)
        return None

    def download_image(self, attachment, key_override="photo_"):
        filename = str(attachment['id'])
        url = attachment[self.find_largest(attachment, key_override)]
        return self.download_file(url, filename, True)

    def fetch_messages(self):
        offset = 0

        selector = 'user_id' if self.type == 'user' else 'peer_id'
        author_id = self.id if self.type == 'user' else (2000000000 + self.id if self.type == 'chat' else -self.id)

        while True:
            messages = self.api.call('messages.getHistory',
                                     [('offset', offset), ('count', 200), (selector, author_id), ('rev', 1)])
            if len(messages['items']) == 0:
                break
            for msg in messages['items']:
                yield (msg, messages['count'])
            offset += len(messages['items'])

    def handle_link(self, context, link):
        downloaded = None
        if 'photo' in link:
            downloaded = self.download_image(link['photo'])

        return {
            'type': 'link',
            'url': link['url'],
            'title': link['title'] if 'title' in link else '',
            'caption': link['caption'] if 'caption' in link else '',
            'description': link['description'] if 'description' in link else '',
            'filename': downloaded
        }

    def handle_photo(self, context, photo):
        downloaded = self.download_image(photo)
        return {
            'type': 'photo',
            'filename': downloaded,
            'url': self.find_largest(photo),
            'description': photo['text'],
            'owner_id': photo['owner_id'],
            'width': photo['width'],
            'height': photo['height'],
            'date': photo['date'],
            'id': photo['id'],
            'album_id': photo['album_id']
        }

    def handle_sticker(self, context, sticker):
        # find the largest sticker image file
        largest = None
        for image in sticker['images']:
            if largest is None or image['width'] > largest['width']:
                largest = image

        url = largest['url'] if largest is not None else ''

        downloaded = self.download_file(url, str(sticker['sticker_id'])) if largest is not None else None

        return {
            'type': 'sticker',
            'filename': downloaded,
            'url': url
        }

    def handle_video(self, context, video):
        video_thumb = self.download_image(video)

        context.add_user(video['owner_id'], self)

        return {
            'type': 'video',
            'description': video['description'],
            'url': "https://vk.com/video%s_%s" % (video['owner_id'], video['id']),
            'title': video["title"],
            'duration': video["duration"],
            'views': video['views'],
            'comments': video['comments'],
            'thumbnail_filename': video_thumb,
            'platform': video['platform'] if 'platform' in video else '',
            'date': video['date'],
            'owner_id': video['owner_id']
        }

    def handle_wall(self, context, wall):
        if 'from_id' in wall:
            context.add_user(wall['from_id'], self)

        if 'to_id' in wall:
            context.add_user(wall['to_id'], self)

        exported_post = {
            'type': 'post',
            'from_id': wall.get('from_id', ''),
            'to_id': wall.get('to_id', ''),
            'post_type': wall.get('post_type', ''),
            'date': wall['date'],
            'text': wall['text'],
            'url': "https://vk.com/wall%s_%s" % (wall['from_id'], wall['id']),
            'views': wall['views']['count'] if 'views' in wall else -1,
            'likes': wall['likes']['count'] if 'likes' in wall else -1,
            'comments': wall['comments']['count'] if 'comments' in wall else -1,
            'reposts': wall['reposts']['count'] if 'reposts' in wall else -1,
            'source': wall.get('post_source', {'type': 'api', 'platform': 'unknown'})
        }

        if "attachments" in wall:
            exported_post['attachments'] = self.export_attachments(context.next_level(), wall['attachments'])

        if "copy_history" in wall:
            # this is a repost
            for repost in wall['copy_history']:
                exported_post['repost'] = []
                if repost["post_type"] == "post":
                    exported_post['repost'].append(self.handle_wall(context.next_level(), repost))
                else:
                    progress.error("No handler for post type: %s\n" % repost["post_type"])

        return exported_post

    def handle_audio(self, context, audio):
        filename = '%s.mp3' % audio['id']
        url = audio['url']

        downloaded = None
        if self.options.arguments.audio and context.depth <= self.options.arguments.audio_depth:
            if not url or "audio_api_unavailable.mp3" in url:
                progress.error("Audio file [%s - %s] is no more available, skipping\n"
                               % (audio['artist'], audio['title']))
            else:
                downloaded = self.download_file(url, filename)

        return {
            'type': 'audio',
            'artist': audio['artist'],
            'title': audio['title'],
            'duration': audio['duration'],
            'filename': downloaded,
            'url': url
        }

    def handle_voice_msg(self, context, audio_msg):
        filename = '%s.%s' % (audio_msg['id'], audio_msg['ext'])
        url = audio_msg['preview']['audio_msg']['link_mp3'] or audio_msg['preview']['audio_msg']['link_ogg']

        downloaded = None
        if not self.options.arguments.no_voice:
            if url:
                downloaded = self.download_file(url, filename)
            else:
                progress.error("Voice message is no more available, skipping\n")

        return {
            'type': 'voice',
            'filename': downloaded,
            'url': url,
            'duration': audio_msg["preview"]["audio_msg"]["duration"],
            'id': audio_msg['id'],
            'owner_id': audio_msg['owner_id'],
            'date': audio_msg['date']
        }

    def handle_doc(self, context, doc):
        if 'preview' in doc and 'audio_msg' in doc['preview']:
            return self.handle_voice_msg(context, doc)

        filename = '%s.%s' % (doc['id'], doc['ext'])
        url = doc['url']

        downloaded = None
        if self.options.arguments.docs and context.depth <= self.options.arguments.docs_depth:
            if url:
                downloaded = self.download_file(url, filename, False, doc.get('size', -1))
            else:
                progress.error("Document [%s] is no more available, skipping\n" % doc['title'])

        return {
            'type': 'doc',
            'filename': downloaded,
            'url': url,
            'title': doc.get('title', ''),
            'size': doc.get('size', 0),
            'ext': doc.get('ext', '')
        }

    def handle_gift(self, context, gift):
        gift_thumb = self.download_image(gift, 'thumb_')

        return {
            'type': 'gift',
            'thumbnail': gift_thumb
        }

    def handle_unknown(self, context, attachment):
        return {
            'type': attachment['type']
        }

    def export_attachments(self, context, attachments):
        known_types = ('photo', 'video', 'audio', 'doc', 'wall', 'sticker', 'link', 'gift')

        results = []
        for att in attachments:
            if att['type'] in known_types:
                results.append(getattr(self, 'handle_' + att['type'])(context, att[att['type']]))
            else:
                results.append(self.handle_unknown(context, att))

        return results

    def export_message(self, ctx, vk_msg):
        # write message head
        exported_msg = {
            'date': vk_msg['date'],
            'message': vk_msg['body'],
            'is_important': 'important' in vk_msg and vk_msg['important'],
            'is_updated': 'update_time' in vk_msg and vk_msg['update_time']
        }

        is_updated = False
        if 'update_time' in vk_msg and vk_msg['update_time']:
            is_updated = True
            exported_msg['updated_at'] = vk_msg['update_time']
        exported_msg['is_updated'] = is_updated

        sender_id = vk_msg['from_id'] if 'from_id' in vk_msg else vk_msg['user_id']
        ctx.add_user(sender_id, self)

        exported_msg['sender'] = {
            'id': sender_id
        }

        # handle forwarded messages
        if 'fwd_messages' in vk_msg and len(vk_msg['fwd_messages']) > 0:
            exported_msg['forwarded'] = []
            for fwd_msg in vk_msg['fwd_messages']:
                exported_msg['forwarded'].append(self.export_message(ctx, fwd_msg))

        # handle attachments
        if 'attachments' in vk_msg:
            exported_msg['attachments'] = self.export_attachments(ctx, vk_msg['attachments'])

        if 'action' in vk_msg:
            exported_msg['action'] = vk_msg['action']

        if 'action_text' in vk_msg:
            exported_msg['action_text'] = vk_msg['action_text']

        if 'action_mid' in vk_msg:
            exported_msg['action_mid'] = vk_msg['action_mid']

        if self.options.arguments.save_raw:
            exported_msg['raw'] = vk_msg

        return exported_msg

    def export(self):
        cur_step = 0

        ctx = ExportContext(self.user_fetcher)

        for msg, total in self.fetch_messages():
            if cur_step == 0:
                progress.update(0, total)

            exported_msg = self.export_message(ctx, msg)

            self.json_out['messages'].append(exported_msg)

            cur_step += 1
            progress.update(cur_step, total)

        self.json_out['users'] = ctx.users

        return self.json_out
