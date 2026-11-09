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

MAX_REQUEST = 16384
PREFIX_PROGRESS = 'TEKTIK_PROGRESS '
PREFIX_FILE = 'TEKTIK_FILE '
VIDEO_EXTENSIONS = {'.mp4', '.m4v', '.mkv', '.webm', '.mov', '.avi', '.mpg', '.mpeg',
                    '.3gp', '.3g2', '.wmv', '.flv', '.mts', '.m2ts', '.ogv', '.ts'}
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
    folder = pathlib.Path.home() / 'Downloads' / 'TekTik Video'
    folder.mkdir(parents=True, exist_ok=True)
    return folder


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
    if 'sign in' in low or 'private video' in low:
        return 'Kaynak site bu video için oturum açılmasını veya ek doğrulama istiyor.'
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


def download(url):
    try:
        paths = tools()
    except (OSError, KeyError, ValueError):
        error('İndirme bileşenleri eksik. Mac kurulumunu yeniden çalıştır.')
        return
    folder = download_folder()
    with tempfile.TemporaryDirectory(prefix='.tektik-', dir=str(folder)) as staging:
        command = [paths['yt-dlp'], '--ignore-config', '--no-plugin-dirs',
                   '--no-remote-components', '--no-playlist', '--playlist-items', '1',
                   '--match-filter', '!is_live', '--no-mtime', '--socket-timeout', '20',
                   '--encoding', 'utf-8', '--ffmpeg-location', str(pathlib.Path(paths['ffmpeg']).parent),
                   '--js-runtimes', 'deno:' + paths['deno'],
                   '--format', 'bv*[vcodec^=avc1]+ba[acodec^=mp4a]/bv*[vcodec^=avc1]+ba/bv*+ba/b',
                   '--merge-output-format', 'mp4/mkv', '--paths', staging,
                   '--output', '%(title).100s.%(ext)s', '--color', 'never', '--no-simulate',
                   '--progress', '--newline', '--progress-delta', '0.75',
                   '--progress-template', 'download:' + PREFIX_PROGRESS + '%(progress._percent)s',
                   '--progress-template', 'postprocess:' + PREFIX_PROGRESS + 'NA',
                   '--print', 'after_move:' + PREFIX_FILE + '%(filepath)j', '--', url]
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
            error('Bu sayfada indirilebilir bir video bulunamadı.')
            return
        path = pathlib.Path(staged_file)
        if (path.parent != pathlib.Path(staging) or path.suffix.lower() not in VIDEO_EXTENSIONS
                or path.is_symlink() or not path.is_file()):
            error('Bu sayfadan desteklenen bir video dosyası alınamadı.')
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
        elif kind == 'openFolder':
            subprocess.Popen(['/usr/bin/open', str(download_folder())],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            send({'type': 'opened'})
        elif kind == 'download':
            if not valid_url(data.get('url')):
                error('Geçerli bir HTTP veya HTTPS video adresi gerekiyor.')
            else:
                download(data['url'])
        else:
            error('Bu işlem desteklenmiyor.')
    except (ValueError, UnicodeError, json.JSONDecodeError):
        error('Tarayıcıdan gelen istek okunamadı.')
    except (OSError, subprocess.SubprocessError):
        error('Yerel yardımcı başlatılamadı. Mac kurulumunu yeniden çalıştırmayı dene.')


if __name__ == '__main__':
    main()
