from utils import *
import codecs
import json


class HTMLExporterOutput:
    def __init__(self):
        self.data = []

    def append(self, text):
        self.data.append(text)

    def get(self):
        return ''.join(self.data)


class HTMLExporterContext:
    def __init__(self, progress, output, input_json, level):
        self.progress = progress
        self.output = output
        self.input_json = input_json
        self.level = level

    def next_level(self):
        return HTMLExporterContext(self.progress, self.output, self.input_json, self.level + 1)


class HTMLExporter:
    def __init__(self, options):
        self.options = options

    @property
    def extension(self):
        return "html"

    def export(self, input_json, progress):
        # load stylesheet early
        with codecs.open('style.css', 'r', encoding='utf-8') as f:
            stylesheet = f.read()

        ctx = HTMLExporterContext(progress, HTMLExporterOutput(), input_json, 1)

        link_block = ''
        if self.options.arguments.embed_resources:
            link_block = '<style>{stylesheet}</style>'.format(stylesheet=stylesheet)
        else:
            link_block = '<link rel="stylesheet" href="style.css" />'

        ctx.output.append('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            {link_block}
        </head>
        <body>
            <div class="messages">
        '''.format(link_block=link_block))

        cur_step = 0
        total = len(input_json['messages'])
        for msg in input_json['messages']:
            if cur_step == 0:
                ctx.progress.update(0, total)

            ctx.output.append(self.export_message(ctx, msg))

            cur_step += 1
            ctx.progress.update(cur_step, total)

        ctx.output.append('</div></body></html>')

        files = dict()
        if not self.options.arguments.embed_resources:
            files['style.css'] = stylesheet

        return {
            'text': ctx.output.get(),
            'files': files
        }

    def get_action_text(self, ctx, msg, action, action_text, action_mid):
        action_text_dict = {
            'chat_photo_update': 'Updated the chat photo',
            'chat_photo_remove': 'Removed the chat photo',
            'chat_create': 'Created the chat',
            'chat_invite_user': 'Invited user to the chat',
            'chat_kick_user': 'Kicked user from the chat',
            'chat_invite_user_by_link': 'Entered the chat by invite link'
        }

        if action == 'chat_title_update':
            return 'Changed chat title to: <span class="new-chat-title">{title}</span>'.format(title=action_text)
        elif action == 'chat_pin_message':
            return 'Pinned message <span class="new-chat-title">{text}</span>'.format(text=action_text)
        elif action == 'chat_unpin_message':
            return 'Unpinned message <span class="new-chat-title">{text}</span>'.format(text=action_text)
        elif action == 'chat_kick_user':
            if action_mid is None:
                return 'Kicked user'
            elif action_mid == msg['sender']['id']:
                return 'Left the chat'
            else:
                return 'Kicked user <span class="new-chat-title">{name}</span>'.format(name=ctx.input_json['users'].get(action_mid)['name'])
        else:
            return action_text_dict.get(action, '')

    def export_action_message(self, ctx, msg):
        sender = ctx.input_json['users'][msg['sender']['id']]

        attach_block = ''
        if 'attachments' in msg:
            for attachment in msg['attachments']:
                attach_block += self.export_attachment(ctx, attachment)

        if len(attach_block) > 0:
            attach_block = '<div class="msg-attachments">{attach_block}</div>'.format(attach_block=attach_block)

        return '''
        <div class="msg msg--level-{level} msg--action msg-action" data-json='{json}'>
            <span class="msg-action__sender">{sender_fullname}</span>
            :
            {message}
            {attach_block}
        </div>
        '''.format(**{
            'level': ctx.level,
            'json': json.dumps(msg, ensure_ascii=False) if self.options.arguments.save_json_in_html else '',
            'sender_profile': sender['link'],
            'sender_fullname': sender['name'],
            'sender_firstname': sender['first_name'],
            'sender_photo': sender['filename'],
            'date': fmt_timestamp(msg['date']),
            'message': self.get_action_text(ctx, msg, msg['action'], msg.get('action_text', ''), msg.get('action_mid', None)),
            'attach_block': attach_block
        })

    def export_message(self, ctx, msg):
        if 'action' in msg:
            return self.export_action_message(ctx, msg)

        extra_classes = []

        if msg['is_important']:
            extra_classes.append('msg--important')

        if msg['is_updated']:
            extra_classes.append('msg--edited')

        sender = ctx.input_json['users'][msg['sender']['id']]

        fwd_block = ''
        if 'forwarded' in msg:
            for fwd_msg in msg['forwarded']:
                fwd_block += self.export_message(ctx, fwd_msg)

        if len(fwd_block) > 0:
            fwd_block = '<div class="msg-forwarded">{fwd_block}</div>'.format(fwd_block=fwd_block)

        attach_block = ''
        if 'attachments' in msg:
            for attachment in msg['attachments']:
                attach_block += self.export_attachment(ctx, attachment)

        if len(attach_block) > 0:
            attach_block = '<div class="msg-attachments">{attach_block}</div>'.format(attach_block=attach_block)

        return '''
        <div class="msg msg--level-{level} {extra_classes}" data-json='{json}'>
            <div class="msg-head">
                <div class="msg-head__photo-block">
                    <img class="msg-head__photo" src="{sender_photo}" />
                </div>
                <div class="msg-head__info">
                    <a class="msg-head__profile" href="{sender_profile}" title="{sender_fullname}">{sender_firstname}</a>
                    <div class="msg-head__date-block">
                        <span class="msg-head__date">{date}</span>
                        {edited_block}
                    </div>
                </div>
            </div>
            <div class="msg-body">
                <div class="msg-text">
                    {message}
                </div>
                {fwd_block}
                {attach_block}
            </div>
        </div>
        '''.format(**{
            'level': ctx.level,
            'extra_classes': ' '.join(extra_classes) if extra_classes is not None else '',
            'sender_profile': sender['link'],
            'sender_fullname': sender['name'],
            'sender_firstname': sender['first_name'],
            'sender_photo': sender['filename'],
            'date': fmt_timestamp(msg['date']),
            'edited_block': '<span class="msg-head__edit-date">Edited at: {date}</span>'.format(date=fmt_timestamp(msg['updated_at'])) if msg['is_updated'] else '',
            'message': msg['message'],
            'fwd_block': fwd_block,
            'attach_block': attach_block,
            'json': json.dumps(msg, ensure_ascii=False) if self.options.arguments.save_json_in_html else ''
        })

    def export_attachment(self, ctx, attach):
        known_types = ('photo', 'video', 'audio', 'doc', 'post', 'sticker', 'link', 'gift', 'voice')

        if attach['type'] in known_types:
            return getattr(self, 'handle_' + attach['type'])(ctx, attach)
        else:
            return self.handle_unknown(ctx, attach)

    def handle_unknown(self, ctx, attach):
        return '''
        <div class="attach attach-{type}">
            <span class="attach-{type}__title">{title}</span>
        </div>
        '''.format(**{
            'type': attach['type'],
            'title': "Unknown attachment type"
        })

    def handle_link(self, ctx, attach):
        if 'filename' in attach and attach['filename'] is not None:
            return '''
            <div class="attach attach-link">
                <a class="attach-link__link-block" title="{title}" href="{url}">
                    <div class="attach-link__image-block">
                        <img class="attach-link__image" src="{filename}" />
                    </div>
                    <div class="attach-link__description">
                        <div class="attach-link__title">{title}</div>
                        <div class="attach-link__description-text">{description}</div>
                        <div class="attach-link__caption">{caption}</div>
                    </div>
                </a>
            </div>
            '''.format(**attach)
        else:
            return '''
            <div class="attach attach-link">
                <a class="attach-link__link-block attach-link__link-block--no-image" title="{title}" href="{url}">
                    <div class="attach-link__description">
                        <div class="attach-link__title">{title}</div>
                        <div class="attach-link__description-text">{description}</div>
                        <div class="attach-link__caption">{caption}</div>
                    </div>
                </a>
            </div>
            '''.format(**attach)

    def handle_photo(self, ctx, attach):
        return '''
        <div class="attach attach-photo">
            <span class="attach-photo__title">{description}</span>
            <img class="attach-photo__image" src="{filename}" alt="{description}" />
        </div>
        '''.format(**attach)

    def handle_sticker(self, ctx, attach):
        return '''
        <div class="attach attach-sticker">
            <img class="attach-sticker__image" src="{filename}" />
        </div>
        '''.format(**attach)

    def handle_video(self, ctx, attach):
        args = {**attach, **{
            'duration': fmt_time(attach['duration']),
            'date': fmt_timestamp(attach['date'])
        }}

        uploader_profile = ''
        owner_id = attach['owner_id']
        if owner_id in ctx.input_json['users']:
            uploader_profile = '<a href="{link}">{name}</a>'.format(**ctx.input_json['users'][owner_id])

        args['uploader_profile'] = uploader_profile

        return '''
        <div class="attach attach-video">
            <a class="attach-video__link" href="{url}" title="{title}">
                <img class="attach-video__thumbnail" src="{thumbnail_filename}" alt="{title}" />
                <div class="attach-video__title">{title}</div>
            </a>
            <div class="attach-video__meta meta">
                <p>Views on VK: <span class="meta__views">{views}, comments on VK: <span class="meta__comments">{comments}</span></p>
                <p>Added at: <span class="meta__date">{date}</span> from {platform} by {uploader_profile}</p>
            </div>
            <div class="attach-video__description">{description}</div>
        </div>
        '''.format(**args)

    def handle_post(self, ctx, attach):
        args = {**attach, **{
            'date': fmt_timestamp(attach['date'])
        }}

        attach_block = ''
        if 'attachments' in attach:
            for attachment in attach['attachments']:
                attach_block += self.export_attachment(ctx, attachment)

        if len(attach_block) > 0:
            attach_block = '<div class="msg-attachments">{attach_block}</div>'.format(attach_block=attach_block)

        args['attach_block'] = attach_block

        head_block = ''
        if 'from_id' in attach and attach['from_id'] in ctx.input_json['users']:
            user_data = ctx.input_json['users'][attach['from_id']]
            if 'filename' in user_data:
                head_block = '''
                <div class="post-head">
                    <div class="post-head__image-block">
                        <img class="post-head__image" src="{filename}" />
                    </div>
                    <div class="post-head__info">
                        <div class="post-head__name">
                            <a class="post-head__link" href="{link}">{name}</a>
                        </div>
                        <div class="post-head__date">{date}</div>
                    </div>
                </div>
                '''.format(**user_data, date=args['date'])
            else:
                head_block = '''
                <div class="post-head">
                    <div class="post-head__name">
                        <a class="post-head__link" href="{link}">{name}</a>
                    </div>
                    <div class="post-head__date">{date}</div>
                </div>
                '''.format(**user_data, date=args['date'])

        args['head_block'] = head_block

        repost_block = ''
        if 'repost' in attach:
            for repost in attach['repost']:
                repost_block = '''
                <div class="attach-post__repost">
                    {repost_block}
                </div>
                '''.format(repost_block=self.handle_post(ctx, repost))

        args['repost_block'] = repost_block

        return '''
        <div class="attach attach-post">
            {head_block}
            <div class="attach-post__text">{text}</div>
            <a class="attach-post__link" href="{url}"></a>
            {attach_block}
            {repost_block}
        </div>
        '''.format(**args)

    def handle_audio(self, ctx, attach):
        args = {**attach, **{'duration': fmt_time(attach['duration'])}}

        if 'downloaded' in attach and attach['downloaded'] is not None:
            audio_block = '<audio class="attach-audio__audio" controls src="{filename}" />'.format(**attach)
        else:
            audio_block = '<div class="attach-audio__audio attach-audio__audio--failed">Unavailable</div>'

        return '''
        <div class="attach attach-audio">
            <div class="attach-audio__title">
                Audio:
                <span class="attach-audio__author">
                    <span class="attach-audio__composition-artist">{artist}</span>
                    -
                    <span class="attach-audio__composition-title">{title}</span>
                </span>
            </div>
            <span class="attach-audio__audio-block">
                {audio_block}
                <div class="attach-audio__duration">{duration}</div>
            </span>
        </div>
        '''.format(**args, audio_block=audio_block)

    def handle_voice(self, ctx, attach):
        args = {**attach, **{'duration': fmt_time(attach['duration'])}}

        return '''
        <div class="attach attach-voice">
            <div class="attach-voice__title">Voice message</div>
            <div class="attach-voice__audio-block">
                <audio class="attach-voice__audio" controls src="{filename}"></audio>
                <div class="attach-voice__duration">{duration}</div>
            </div>
        </div>
        '''.format(**args)

    def handle_doc(self, ctx, attach):
        args = {**attach, **{
            'filename': attach['filename'] or attach["url"],
            'size': fmt_size(attach['size'])
        }}

        return '''
        <div class="attach attach-doc">
            <a href="{filename}" class="attach-doc__link-block">
                <div class="attach-doc__desc">
                    <div class="attach-doc__link" title="{title}">{title}</div>
                    <div class="attach-doc__size">{size}</div>
                </div>
            </a>
        </div>
        '''.format(**args)

    def handle_gift(self, ctx, attach):
        return '''
        <div class="attach attach-gift">
            <div class="attach-gift__title">Gift</div>
            <img class="attach-gift__thumbnail" src="{thumbnail}" />
        </div>
        '''.format(**attach)
