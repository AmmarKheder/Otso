#!/bin/bash
# Otso 1 km daily chain. Called by Otso's realtime/daily.sh AFTER the 0.4 deg products are published (user order
# 2026-10-28: publish Otso 1 km daily on the Otso site). It only submits two jobs and returns at once, so it can never
# block or change the 0.4 deg run; this file is read at run time (not copied by sbatch), so edits here need no
# resubmission of Otso's daily job.
#   GPU  otso1km_job.sh <day> pmA_final best.ckpt pmA_final_K0T3   (standard-g, ~16 min; model, prior and sampler as frozen)
#   CPU  web/web_job.sh <day> pmA_final_K0T3                        (small, ~5 min, afterok): tiles -> branch live1km
# Switch off: touch otso_1km/web/OFF (or O1K_OFF=1). Status lines: logs/OTSO1KM_STATUS.md, tag [otso1km-web].
#   bash o1k_chain.sh <yyyy-mm-dd>
set -uo pipefail
W=/scratch/project_462001804/ammar/global_model_forecasting_air_pollution
O=$W/otso_1km
DATE=$1
CKPT=$W/runs_global/pmA_final/ckpt/best.ckpt                                  # the published system; to switch it (lead's
TAG=pmA_final_K0T3                                                               # say-so only) write CKPT=... TAG=... in web/system.env
[ -f $O/web/system.env ] && source $O/web/system.env
unset PYTHONPATH MPLCONFIGDIR                                                   # the caller's (Otso's) python settings stay there
note() { printf '%s\n' "- $(date '+%F %H:%M') [otso1km-web] chain: $1" >> $W/logs/OTSO1KM_STATUS.md; }
if [ "${O1K_OFF:-0}" = 1 ] || [ -f $O/web/OFF ]; then note "$DATE: daily chain OFF (otso_1km/web/OFF), nothing submitted"; exit 0; fi
if [ -f $O/out/$DATE/$TAG/run.json ]; then                                     # products already there (a rerun): tiles only
  J2=$(sbatch --parsable --job-name o1k_web_$DATE $O/web/web_job.sh $DATE $TAG) || { note "$DATE: web job not submitted"; exit 1; }
  note "$DATE: 1 km products exist, web job $J2"
else
  J1=$(sbatch --parsable --job-name o1k_$DATE $O/otso1km_job.sh $DATE $CKPT $TAG) || { note "$DATE: GPU job not submitted"; exit 1; }
  J2=$(sbatch --parsable --job-name o1k_web_$DATE --dependency=afterok:$J1 --kill-on-invalid-dep=yes $O/web/web_job.sh $DATE $TAG) \
    || { note "$DATE: GPU job $J1 submitted, web job NOT submitted"; exit 1; }
  note "$DATE: GPU job $J1 (otso1km_job.sh) -> web job $J2 (afterok)"
fi
mkdir -p $O/out/$DATE/$TAG && touch $O/out/$DATE/$TAG/.daily
# housekeeping: the npz products of DAILY runs (marker .daily, 2.5 GB/day) are kept 7 days; json/png and research runs stay
find $O/out -mindepth 3 -maxdepth 3 -name .daily -mtime +7 2>/dev/null | while read -r m; do rm -f "$(dirname "$m")"/lead*_part*.npz; done
exit 0
