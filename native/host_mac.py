#!/usr/bin/python3
"""Native Messaging host for macOS."""
import json
import math
import os
import pathlib
import signal
import struct
import subprocess
import sys
import tempfile
import threading
from urllib.parse import urlsplit

MAX_REQUEST = 262144
PREFIX_PROGRESS = 'TEKTIK_PROGRESS '
PREFIX_FILE = 'TEKTIK_FILE '
PREFIX_DURATION = 'TEKTIK_DURATION '
PREFIX_SIZE = 'TEKTIK_SIZE '
VIDEO_EXTENSIONS = {'.mp4', '.m4v', '.mkv', '.webm', '.mov', '.avi', '.mpg', '.mpeg',
                    '.3gp', '.3g2', '.wmv', '.flv', '.mts', '.m2ts', '.ogv', '.ts'}
AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.opus', '.ogg', '.wav', '.flac', '.aac'}
OUTPUT_LOCK = threading.Lock()
DISCONNECTED = threading.Event()


def send(message):
    if DISCONNECTED.is_set():
        return
    data = json.dumps(message, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    with OUTPUT_LOCK:
        try:
            sys.stdout.buffer.write(struct.pack('<I', len(data)) + data)
            sys.stdout.buffer.flush()
        except (BrokenPipeError, OSError):
            DISCONNECTED.set()


def error(message):
    send({'type': 'error', 'message': message})


def request():
    header = sys.stdin.buffer.read(4)
    if not header:
        return None
    if len(header) != 4:
        raise ValueError('Incomplete header')
    size = struct.unpack('<I', header)[0]
    if size < 1 or size > MAX_REQUEST:
        raise ValueError('Invalid message size')
    body = sys.stdin.buffer.read(size)
    if len(body) != size:
        raise ValueError('Incomplete message')
    value = json.loads(body.decode('utf-8'))
    if not isinstance(value, dict):
        raise ValueError('Invalid message')
    return value


def valid_url(value):
    if not isinstance(value, str) or len(value) > 12000 or any(ord(c) < 32 for c in value):
        return False
    try:
        parts = urlsplit(value)
        return (parts.scheme in ('http', 'https') and bool(parts.hostname)
                and not parts.username and not parts.password and not parts.fragment
                and not any(c.isspace() for c in parts.netloc))
    except ValueError:
        return False


def download_folder():
    setting = pathlib.Path(__file__).with_name('folder.txt')
    if setting.is_file():
        chosen = pathlib.Path(setting.read_text(encoding='utf-8').strip())
        if chosen.is_absolute() and chosen.is_dir():
            return chosen
    folder = pathlib.Path.home() / 'Downloads' / 'TekTik Video'
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def choose_folder():
    result = subprocess.run(['/usr/bin/osascript', '-e',
                             'POSIX path of (choose folder with prompt "Videoların kaydedileceği klasörü seç")'],
                            capture_output=True, text=True, timeout=120)
    if result.returncode:
        send({'type': 'cancelled'})
        return
    path = pathlib.Path(result.stdout.strip())
    if not path.is_absolute() or not path.is_dir():
        error('Seçilen klasör kullanılamıyor.')
        return
    pathlib.Path(__file__).with_name('folder.txt').write_text(str(path), encoding='utf-8')
    send({'type': 'folder', 'path': str(path)})


def write_cookies(data, staging, url):
    if 'cookies' not in data:
        return None
    cookies = data['cookies']
    if not isinstance(cookies, list) or len(cookies) > 100:
        raise ValueError('Invalid cookies')
    host = urlsplit(url).hostname.lower()
    lines = ['# Netscape HTTP Cookie File']
    for cookie in cookies:
        if not isinstance(cookie, dict):
            raise ValueError('Invalid cookie')
        domain = cookie.get('domain', '')
        name = cookie.get('name', '')
        value = cookie.get('value', '')
        path = cookie.get('path', '/')
        if not all(isinstance(item, str) for item in (domain, name, value, path)):
            raise ValueError('Invalid cookie')
        bare_domain = domain.lstrip('.').lower()
        if (not bare_domain or (host != bare_domain and not host.endswith('.' + bare_domain))
                or len(name) > 256 or len(value) > 4096
                or any(char in item for item in (name, value, path) for char in '\r\n\t')):
            raise ValueError('Invalid cookie')
        secure = cookie.get('secure', False)
        if not isinstance(secure, bool):
            raise ValueError('Invalid cookie')
        lines.append('\t'.join((domain, 'TRUE' if domain.startswith('.') else 'FALSE', path,
                                'TRUE' if secure else 'FALSE', '0', name, value)))
    cookie_path = pathlib.Path(staging) / 'cookies.txt'
    cookie_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return cookie_path


def tools():
    config = pathlib.Path(__file__).with_name('tools-mac.json')
    paths = json.loads(config.read_text(encoding='utf-8'))
    if any(not pathlib.Path(paths[name]).is_file() for name in ('yt-dlp', 'deno', 'ffmpeg', 'ffprobe')):
        raise FileNotFoundError()
    return paths


def stop_process(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=3)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def watch_disconnect(active_process):
    try:
        os.read(sys.stdin.fileno(), 1)
    except OSError:
        pass
    DISCONNECTED.set()
    stop_process(active_process[0])


def make_mac_mp4(path, staging, paths, active_process):
    if DISCONNECTED.is_set():
        return None
    converted = pathlib.Path(staging) / '.converted'
    converted.mkdir()
    output = converted / (path.stem + '.mp4')
    command = [paths['ffmpeg'], '-nostdin', '-v', 'error', '-i', str(path),
               '-map', '0:v:0', '-map', '0:a:0?', '-c:v', 'libx264',
               '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p',
               '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(output)]
    send({'type': 'progress', 'percent': None})
    conversion = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL, start_new_session=True)
    active_process[0] = conversion
    if DISCONNECTED.is_set():
        stop_process(conversion)
        return None
    try:
        code = conversion.wait()
    finally:
        stop_process(conversion)
    return output if code == 0 and output.is_file() and not DISCONNECTED.is_set() else None


def failure_message(line):
    low = line.lower()
    if not line.startswith('ERROR:'):
        return None
    if 'drm' in low:
        return 'Bu video DRM korumalı.'
    if 'unsupported url' in low:
        return 'Bu sayfa video indirmeyi desteklemiyor.'
    if 'requested format is not available' in low:
        return 'Seçilen kalite bu videoda bulunamadı. Ayarlardan En iyi mevcut kalite seçeneğini dene.'
    if 'sign in' in low or 'private video' in low:
        return 'Site oturum açılmasını istiyor. Video sayfasında sağ tıklayıp Bu sitenin oturum çerezleriyle indir seçeneğini dene.'
    if 'http error 429' in low:
        return 'Kaynak site çok fazla istek aldı. Bir süre sonra yeniden dene.'
    return None


def save_video(path, folder):
    for index in range(1, 1001):
        name = path.stem + ('' if index == 1 else ' ({})'.format(index)) + path.suffix
        destination = folder / name
        try:
            os.link(str(path), str(destination), follow_symlinks=False)
            path.unlink()
            return name
        except FileExistsError:
            continue
    raise OSError('No unused filename')


def download(data):
    url = data['url']
    quality = data.get('quality', 'best')
    mode = data.get('mode', 'video')
    max_minutes = data.get('maxMinutes', 0)
    if (quality not in ('best', '1080', '720', '480') or mode not in ('video', 'audio')
            or type(max_minutes) is not int or max_minutes not in (0, 10, 30, 60, 120)):
        error('İndirme ayarları geçersiz.')
        return
    try:
        paths = tools()
    except (OSError, KeyError, ValueError):
        error('İndirme bileşenleri eksik. Mac kurulumunu yeniden çalıştır.')
        return
    folder = download_folder()
    with tempfile.TemporaryDirectory(prefix='.tektik-', dir=str(folder)) as staging:
        cookies_path = write_cookies(data, staging, url)
        if mode == 'audio':
            video_format = 'bestaudio/best'
        elif quality == 'best':
            video_format = 'bv*[vcodec^=avc1]+ba[acodec^=mp4a]/bv*[vcodec^=avc1]+ba/bv*+ba/b'
        else:
            height = '[height<=' + quality + ']'
            video_format = ('bv*' + height + '[vcodec^=avc1]+ba[acodec^=mp4a]/'
                            + 'bv*' + height + '+ba/b' + height)
        video_filter = ('!is_live & duration & duration <= ' + str(max_minutes * 60)
                        if max_minutes else '!is_live')
        command = [paths['yt-dlp'], '--ignore-config', '--no-plugin-dirs',
                   '--no-remote-components', '--no-playlist', '--playlist-items', '1',
                   '--match-filter', video_filter, '--no-mtime', '--socket-timeout', '20',
                   '--encoding', 'utf-8', '--ffmpeg-location', str(pathlib.Path(paths['ffmpeg']).parent),
                   '--js-runtimes', 'deno:' + paths['deno'],
                   '--format', video_format,
                   '--merge-output-format', 'mp4/mkv', '--paths', staging,
                   '--output', '%(title).100s.%(ext)s', '--color', 'never', '--no-simulate',
                   '--progress', '--newline', '--progress-delta', '0.75',
                   '--progress-template', 'download:' + PREFIX_PROGRESS + '%(progress._percent)s',
                   '--progress-template', 'postprocess:' + PREFIX_PROGRESS + 'NA',
                   '--print', 'before_dl:' + PREFIX_DURATION + '%(duration)s',
                   '--print', 'before_dl:' + PREFIX_SIZE + '%(filesize,filesize_approx)s',
                   '--print', 'after_move:' + PREFIX_FILE + '%(filepath)j']
        if mode == 'audio':
            command.extend(('--extract-audio', '--audio-format', 'mp3'))
        if cookies_path is not None:
            command.extend(('--cookies', str(cookies_path)))
        command.extend(('--', url))
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                                   errors='replace', bufsize=1, start_new_session=True)
        active_process = [process]
        threading.Thread(target=watch_disconnect, args=(active_process,), daemon=True).start()
        send({'type': 'started'})
        staged_file = None
        failure = None
        try:
            for raw in process.stdout:
                line = raw.rstrip('\r\n')
                if line.startswith(PREFIX_FILE):
                    try:
                        staged_file = json.loads(line[len(PREFIX_FILE):])
                    except ValueError:
                        pass
                elif line.startswith(PREFIX_PROGRESS):
                    try:
                        percent = float(line[len(PREFIX_PROGRESS):])
                        percent = round(min(99, max(0, percent)), 1) if math.isfinite(percent) else None
                    except ValueError:
                        percent = None
                    send({'type': 'progress', 'percent': percent})
                elif line.startswith((PREFIX_DURATION, PREFIX_SIZE)):
                    prefix, field = ((PREFIX_DURATION, 'duration') if line.startswith(PREFIX_DURATION)
                                     else (PREFIX_SIZE, 'size'))
                    try:
                        number = float(line[len(prefix):])
                        if math.isfinite(number) and number >= 0:
                            send({'type': 'info', 'field': field, 'value': number})
                    except ValueError:
                        pass
                else:
                    failure = failure_message(line) or failure
            code = process.wait()
        finally:
            stop_process(process)
        if DISCONNECTED.is_set():
            return
        if code:
            error(failure or 'Video indirilemedi. Sayfanın erişilebilir olduğunu kontrol edip yeniden dene.')
            return
        if not isinstance(staged_file, str):
            error('Video seçilen süre sınırını aşıyor veya indirilebilir bir dosya bulunamadı.'
                  if max_minutes else 'Bu sayfada indirilebilir bir video bulunamadı.')
            return
        path = pathlib.Path(staged_file)
        extensions = AUDIO_EXTENSIONS if mode == 'audio' else VIDEO_EXTENSIONS
        if (path.parent != pathlib.Path(staging) or path.suffix.lower() not in extensions
                or path.is_symlink() or not path.is_file()):
            error('Bu sayfadan desteklenen bir video dosyası alınamadı.')
            return
        if mode == 'audio':
            send({'type': 'completed', 'filename': save_video(path, folder)})
            return
        playable = make_mac_mp4(path, staging, paths, active_process)
        if playable is None:
            if not DISCONNECTED.is_set():
                error('Video Mac uyumlu MP4 biçimine dönüştürülemedi.')
            return
        send({'type': 'completed', 'filename': save_video(playable, folder)})


def main():
    try:
        data = request()
        if data is None:
            return
        kind = data.get('type')
        if kind == 'ping':
            send({'type': 'ready'})
        elif kind == 'getFolder':
            send({'type': 'folder', 'path': str(download_folder())})
        elif kind == 'chooseFolder':
            choose_folder()
        elif kind == 'openFolder':
            subprocess.Popen(['/usr/bin/open', str(download_folder())],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            send({'type': 'opened'})
        elif kind == 'download':
            if not valid_url(data.get('url')):
                error('Geçerli bir HTTP veya HTTPS video adresi gerekiyor.')
            else:
                download(data)
        else:
            error('Bu işlem desteklenmiyor.')
    except (ValueError, UnicodeError, json.JSONDecodeError):
        error('Tarayıcıdan gelen istek okunamadı.')
    except (OSError, subprocess.SubprocessError):
        error('Yerel yardımcı başlatılamadı. Mac kurulumunu yeniden çalıştırmayı dene.')


if __name__ == '__main__':
    main()
