import datetime
import html
import os


def fmt_time(secs):
    return str(datetime.timedelta(seconds=secs))


def fmt_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def fmt_size(size):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(size) < 1024.0:
            return "%3.1f%sB" % (size, unit)
        size /= 1024.0
    return "%.1f%sB" % (size, 'Yi')


def esc(text):
    return html.escape(text)


def guess_image_ext(content_type):
    return {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif'
    }.get(content_type.lower(), 'jpg')


def has_downloaded_image(download_dir, filename):
    def is_downloaded_image(existing_file):
        return os.path.splitext(existing_file)[0] == filename

    try:
        downloaded_file = next(f for f in os.listdir(download_dir) if is_downloaded_image(f))
        if os.stat(os.path.join(download_dir, downloaded_file)).st_size > 0:
            return downloaded_file
        return None
    except StopIteration:
        return None
