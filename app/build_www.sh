#!/bin/bash
# Otso 2.0 app: the web assets bundled in the native shell = the site's docs/ folder, minus what only the website needs
# (the classic page, the old 1km/ redirect, the QR code, the coastline files of the classic map). The page itself detects
# the native shell at run time (window.Capacitor) and adapts (no service worker, no install section, native share/haptics).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); DOCS=$HERE/../docs; WWW=$HERE/www
rm -rf "$WWW"; mkdir -p "$WWW"
rsync -a --exclude classic --exclude 1km --exclude 'qr.*' --exclude 'lines*.json' --exclude labels.json --exclude sw.js --exclude '.nojekyll' "$DOCS/" "$WWW/"
cp "$HERE/native.js" "$WWW/native.js"; cp "$HERE/plugins.js" "$WWW/plugins.js"
sed -i.bak 's|<script src="vendor/maplibre-gl.js"></script>|<script src="plugins.js"></script>\
<script src="native.js"></script>\
&|' "$WWW/index.html" && rm -f "$WWW/index.html.bak"                              # GNU and BSD sed: suffix glued to -i, newline = backslash + real line break
grep -q -F '<script src="plugins.js">' "$WWW/index.html" || { echo "plugins.js not injected: the <script src=\"vendor/maplibre-gl.js\"> tag was not found in docs/index.html" >&2; exit 1; }
grep -q -F '<script src="native.js">' "$WWW/index.html" || { echo "native.js not injected" >&2; exit 1; }
echo "plugins.js + native.js injected"
du -sh "$WWW"; find "$WWW" -type f | wc -l
