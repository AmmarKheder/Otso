#!/bin/bash
#SBATCH --job-name=otso_daily
#SBATCH --account=project_462001140
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=05:00:00
#SBATCH --output=/scratch/project_462001140/ammar/eccv/cran-pm/experiments/global1km/realtime/logs/daily_%j.out
# Otso step 5b: the daily driver. Runs on a CPU node: fetch + build for today, submits the GPU job (otso_job.sh) and
# waits for it, builds the products, publishes, prunes, and resubmits itself for tomorrow at the same hour
# (scrontab is disabled on LUMI). Usage: sbatch --begin=11:00 daily.sh [yyyy-mm-dd]
set -uo pipefail
RT=/scratch/project_462001140/ammar/eccv/cran-pm/experiments/global1km/realtime
cd $RT
DATE=${1:-$(date -u +%F)}
HOUR=${OTSO_HOUR:-10:00}
echo "start $(date -u +%FT%TZ) otso daily $DATE"
# tomorrow's run, submitted first so that a failure today does not stop the chain
TOMORROW=$(date -u -d "$DATE + 1 day" +%F)
if [ "${OTSO_NO_RESUBMIT:-0}" = 1 ]; then echo "no resubmission (test)"; else
  BEGIN=$(date -d "${TOMORROW}T${HOUR}:00Z" +%Y-%m-%dT%H:%M:%S)                 # HOUR is UTC; Slurm reads --begin in the local time zone
  NEXT=$(sbatch --parsable --begin="$BEGIN" --export=ALL,OTSO_HOUR=$HOUR $RT/daily.sh $TOMORROW)
  echo "resubmitted for $TOMORROW $HOUR UTC (local $BEGIN) as job $NEXT"
fi
# the world venv is used directly (no `module load`: lmod hung on a Lustre RPC for minutes on 2026-10-10)
unset PYTHONPATH; export PYTHONNOUSERSITE=1; export PYTHONPATH=$RT/pylib
export XDG_CACHE_HOME=/projappl/project_462001140/envs/.cache MPLCONFIGDIR=/tmp/mpl-$USER-$$
PY=/projappl/project_462001140/envs/world/bin/python
export WORLD_DATA=/scratch/project_462001140/ammar/eccv/data/world
$PY -u fetch.py $DATE --deadline 15:30 --every 10 || { echo "fetch failed $(date -u +%FT%TZ)"; exit 1; }
$PY -u build.py $DATE || { echo "build failed $(date -u +%FT%TZ)"; exit 1; }
JOB=$(sbatch --parsable --job-name otso_$DATE $RT/otso_job.sh $DATE)
echo "gpu job $JOB submitted $(date -u +%FT%TZ)"
REL=0
while squeue -h -j $JOB -o %T 2>/dev/null | grep -qE "PENDING|RUNNING|CONFIGURING|COMPLETING"; do
  # a GPU job held by Slurm ("user env retrieval failed requeued held") never starts on its own: release it (3 times at most)
  if [ $REL -lt 3 ] && squeue -h -j $JOB -o %r 2>/dev/null | grep -qi "held"; then scontrol release $JOB && REL=$((REL+1)) && echo "gpu job $JOB released from hold ($REL) $(date -u +%FT%TZ)"; fi
  sleep 60
done
ST=$(sacct -j $JOB --format=State -n -P | head -1)
echo "gpu job $JOB $ST $(date -u +%FT%TZ)"
[ -f $RT/out/$DATE/pred.npy ] || { echo "no forecast for $DATE"; exit 1; }
$PY -u products.py $DATE || { echo "products failed"; exit 1; }
$PY -u fetch_camsfc.py $DATE || echo "CAMS forecast not fetched (the verification will lack it for $DATE)"
$PY -u verify.py $DATE || echo "verification failed (published without it)"
$PY -u publish.py $DATE || { echo "publish failed"; exit 1; }
# housekeeping: the IFS GRIB files (2 GB/day) are only needed to build hres_B.npy; the FLEXGREEN stores (green/) and the
# predictions are kept 10 days; the inputs (cams, hres_B, fires, journal, meta) are kept
find $RT/data -mindepth 2 -maxdepth 2 -type d -name ifs -mtime +1 -exec rm -rf {} + 2>/dev/null
find $RT/data -mindepth 2 -maxdepth 2 -type d -name green -mtime +10 -exec rm -rf {} + 2>/dev/null
find $RT/data -mindepth 2 -maxdepth 2 -name "cams_*.zip" -mtime +3 -delete 2>/dev/null
find $RT/out -mindepth 2 -maxdepth 2 -name "pred*.npy" -mtime +10 -delete 2>/dev/null
echo "end $(date -u +%FT%TZ)"
