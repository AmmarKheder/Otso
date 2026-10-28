#!/bin/bash
#SBATCH --job-name=o1k_web
#SBATCH --account=project_462001804
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=110G
#SBATCH --time=01:30:00
#SBATCH --output=/scratch/project_462001804/ammar/global_model_forecasting_air_pollution/otso_1km/logs/o1k_web_%j.out
# Otso 1 km web layer for one day: tiles.py (XYZ PNG tiles in node-local /tmp) -> publish1km.py (orphan branch live1km of
# AmmarKheder/Otso, latest day only). Never touches Otso's 0.4 deg products or its `live` branch.
#   sbatch web_job.sh <yyyy-mm-dd> [tag] [--dry-run]
set -uo pipefail
W=/scratch/project_462001804/ammar/global_model_forecasting_air_pollution
O=$W/otso_1km
DATE=$1; TAG=${2:-pmA_final_K0T3}; DRY=${3:-}
note() { printf '%s\n' "- $(date '+%F %H:%M') [otso1km-web] job $SLURM_JOB_ID: $1" >> $W/logs/OTSO1KM_STATUS.md; }
unset PYTHONPATH; export PYTHONNOUSERSITE=1 XDG_CACHE_HOME=/projappl/project_462001804/envs/.cache
PY=/projappl/project_462001804/envs/world/bin/python
T=/tmp/o1k_web_${SLURM_JOB_ID:-$$}
trap 'rm -rf $T' EXIT
mkdir -p $T $O/web/runs
cd $O/web
echo "start $(date -u +%FT%TZ) o1k web $DATE $TAG $DRY"
[ -f $O/out/$DATE/$TAG/run.json ] || { note "no Otso 1 km products for $DATE ($TAG): nothing published"; exit 2; }
T0=$(date +%s)
# repository size (GitHub API, KB): the daily force-push leaves unreachable objects until GitHub collects them; above ~2 GB
# the days J+3..J+5 stop at z5 (lead's rule, 2026-10-28)
KB=$(curl -s --max-time 20 https://api.github.com/repos/AmmarKheder/Otso | $PY -c "import json,sys; print(int(json.load(sys.stdin).get('size', 0)))" 2>/dev/null || echo 0)
ZMAX="mean:7,7,6,6,6/prob15:6"
if [ "${KB:-0}" -gt 2000000 ]; then ZMAX="mean:7,7,5,5,5/prob15:6,6,5,5,5"; note "$DATE: GitHub repo size ${KB} KB > 2 GB: J+3..J+5 limited to z5"; fi
$PY -u -W ignore tiles.py $DATE --tag $TAG --out $T/tiles --workers 10 --zmax $ZMAX || { note "tiles $DATE FAILED (otso_1km/logs/o1k_web_$SLURM_JOB_ID.out)"; exit 1; }
T1=$(date +%s)
cp $T/tiles/tiles.json $O/web/runs/tiles_$DATE.json
$PY -u publish1km.py $DATE --tiles $T/tiles --work $T/repo $DRY || { note "publish $DATE FAILED (otso_1km/logs/o1k_web_$SLURM_JOB_ID.out)"; exit 1; }
T2=$(date +%s)
SUM=$($PY -c "import json;m=json.load(open('$T/tiles/tiles.json'));print(f\"{m['total_tiles']} tiles, {m['total_bytes']/1e6:.1f} MB\")")
if [ -z "$DRY" ]; then note "Otso 1 km $DATE web layer published on live1km: $SUM (tiles $((T1-T0)) s, push $((T2-T1)) s; repo size before push ${KB} KB, zmax $ZMAX)";
else note "Otso 1 km $DATE web layer built (dry run, not pushed): $SUM (tiles $((T1-T0)) s)"; fi
echo "end $(date -u +%FT%TZ)"
