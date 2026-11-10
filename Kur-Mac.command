#!/bin/bash
set -euo pipefail

host_name='com.tektik.video'
extension_id='kdecmlbnjjcfjipibclhfkclhkjmbmjo'
source_dir="$(cd "$(dirname "$0")" && pwd)"
install_dir="$HOME/Library/Application Support/TekTikVideo"
chrome_dir="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
edge_dir="$HOME/Library/Application Support/Microsoft Edge/NativeMessagingHosts"
manifest_name="$host_name.json"

if [[ "${1:-}" == '--uninstall' ]]; then
  for dir in "$chrome_dir" "$edge_dir"; do
    if [[ -f "$dir/$manifest_name" ]] && /usr/bin/python3 - "$dir/$manifest_name" "$install_dir/host_mac.py" <<'PY'
import json, sys
try:
    with open(sys.argv[1], encoding='utf-8') as source:
        assert json.load(source).get('path') == sys.argv[2]
except (OSError, ValueError, AssertionError):
    sys.exit(1)
PY
    then
      rm "$dir/$manifest_name"
    fi
  done
  rm -f "$install_dir/host_mac.py" "$install_dir/tools-mac.json" "$install_dir/folder.txt"
  rmdir "$install_dir" 2>/dev/null || true
  echo 'TekTık Video Mac yardımcısı kaldırıldı. Tarayıcı uzantısını ayrıca kaldırabilirsin.'
  exit 0
fi

if [[ "${1:-}" != '' ]]; then
  echo 'Kullanım: Kur-Mac.command [--uninstall]' >&2
  exit 2
fi
if [[ "$(uname -s)" != 'Darwin' ]]; then
  echo 'Bu kurulum macOS içindir.' >&2
  exit 1
fi

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
missing=()
for tool in yt-dlp deno ffmpeg ffprobe; do
  if ! command -v "$tool" >/dev/null 2>&1; then missing+=("$tool"); fi
done
if (( ${#missing[@]} )); then
  if ! command -v brew >/dev/null 2>&1; then
    echo 'Homebrew gerekli: https://brew.sh adresinden kurup yeniden çalıştır.' >&2
    exit 1
  fi
  packages=()
  seen=' '
  for tool in "${missing[@]}"; do
    if [[ "$tool" == 'ffprobe' ]]; then tool='ffmpeg'; fi
    if [[ "$seen" != *" $tool "* ]]; then
      packages+=("$tool")
      seen+="$tool "
    fi
  done
  echo "Eksik bileşenler kuruluyor: ${packages[*]}"
  brew install "${packages[@]}"
fi

for tool in yt-dlp deno ffmpeg ffprobe; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "$tool bulunamadı." >&2
    exit 1
  fi
done

mkdir -p "$install_dir" "$chrome_dir" "$edge_dir"
cp "$source_dir/native/host_mac.py" "$install_dir/host_mac.py"
chmod 755 "$install_dir/host_mac.py"
/usr/bin/python3 - "$install_dir" "$(command -v yt-dlp)" "$(command -v deno)" "$(command -v ffmpeg)" "$(command -v ffprobe)" "$host_name" "$extension_id" "$chrome_dir" "$edge_dir" <<'PY'
import json, os, sys
root, ytdlp, deno, ffmpeg, ffprobe, name, extension, chrome, edge = sys.argv[1:]
with open(os.path.join(root, 'tools-mac.json'), 'w', encoding='utf-8') as target:
    json.dump({'yt-dlp': ytdlp, 'deno': deno, 'ffmpeg': ffmpeg, 'ffprobe': ffprobe}, target)
manifest = {'name': name, 'description': 'TekTik Video local download host',
            'path': os.path.join(root, 'host_mac.py'), 'type': 'stdio',
            'allowed_origins': ['chrome-extension://' + extension + '/']}
for directory in (chrome, edge):
    with open(os.path.join(directory, name + '.json'), 'w', encoding='utf-8') as target:
        json.dump(manifest, target, ensure_ascii=False)
PY

echo 'Mac yardımcısı hazır. Chrome veya Edge uzantılar sayfasında geliştirici modunu aç.'
echo "Paketlenmemiş öğe yükle seçeneğiyle $source_dir/extension klasörünü seç."
