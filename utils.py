import datetime
import html
import os


def fmt_time(secs):
    return str(datetime.timedelta(seconds=secs))


def fmt_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def fmt_date_diff(diff, add_sign=False):
    units = [('s', 60), ('m', 60), ('h', 24), ('d', 0)]

    cur = diff
    result = ''
    for unit in units:
        rem = cur % unit[1] if unit[1] > 0 else cur
        new_result = '{0}{1} {2}'.format(rem, unit[0], result)
        if unit[1] == 0 or cur <= 0:
            if rem != 0:
                result = new_result
            break
        result = new_result
        cur = (cur - rem) // unit[1]

    if add_sign:
        result = ('+' if diff > 0 else '-') + result

    return result


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
