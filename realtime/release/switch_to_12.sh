#!/bin/bash
# Otso 1.2 release, in one command (reversible: rm realtime/model.json + git revert of the page commit).
#   bash release/switch_to_12.sh
set -euo pipefail
RT=/scratch/project_462001140/ammar/eccv/cran-pm/experiments/global1km/realtime
WEB=/scratch/project_462001140/ammar/eccv/foehn
D=$(cat $RT/release/shadow_day 2>/dev/null || echo 2026-10-10)
cd $RT
unset PYTHONPATH; export PYTHONNOUSERSITE=1 XDG_CACHE_HOME=/projappl/project_462001140/envs/.cache PYTHONPATH=$RT/pylib
PY=/projappl/project_462001140/envs/world/bin/python
# 1. the live model
echo '{"version": "1.2", "ckpt": "runs/otso12_a/final.ckpt"}' > $RT/model.json
# 2. today's forecast with 1.2 (the shadow run), products, publication
[ -f out/$D/pred_12a.npy ] || { echo "no shadow forecast for $D"; exit 1; }
[ -f out/$D/pred_11.npy ] || cp out/$D/pred.npy out/$D/pred_11.npy
cp out/$D/pred_12a.npy out/$D/pred.npy
$PY - <<PYX
import json; p = "out/$D/meta.json"; m = json.load(open(p)); m["ckpt"] = "$RT/runs/otso12_a/final.ckpt"; m["version"] = "1.2"; json.dump(m, open(p, "w"), indent=1)
PYX
$PY -u products.py $D && $PY -u publish.py $D
# 3. the page, the app manifest, the main page and the README
cp $WEB/docs/otso/index.html $RT/release/index_11_backup.html
$PY release/page_to_12.py $WEB/docs/otso/index.html
grep -q "<footer>" $WEB/docs/otso/index.html || { echo "page check failed"; cp $RT/release/index_11_backup.html $WEB/docs/otso/index.html; exit 1; }
cp $RT/out/scores_otso12.json $WEB/docs/otso/scores_otso12.json
sed -i 's/"name": "Otso 1.1 — PM2.5 forecast (Foehn project)"/"name": "Otso 1.2 — PM2.5 forecast (Foehn project)"/' $WEB/docs/otso/manifest.webmanifest
sed -i 's/Otso 1\.1/Otso 1.2/g' $WEB/docs/index.html
sed -i 's/## Otso 1\.1: the live forecast (beta)/## Otso 1.2: the live forecast (beta)/; s/Otso 1\.1 is the coarse Foehn model of the paper/Otso 1.2 is the coarse Foehn model of the paper, fine-tuned on the live inputs of January-August 2026/' $WEB/README.md
V=$(grep -o 'otso-1.1-[0-9a-z]*' $WEB/docs/otso/sw.js | head -1); sed -i "s/$V/otso-1.2-$(date -u +%Y%m%d%H%M)/" $WEB/docs/otso/sw.js
cd $WEB && git add -A docs README.md && git -c user.name=AmmarKheder -c user.email=ammarkheder@outlook.fr commit -q -m "Otso 1.2: Foehn-CAMS fine-tuned on the live inputs of January-August 2026 (15-24 % lower error than 1.1 on 6-20 September, ahead of the CAMS forecast from three days on)" --author="AmmarKheder <ammarkheder@outlook.fr>" && git push -q origin main
echo "Otso 1.2 live: model.json, today's forecast republished, page updated"
