#!/bin/bash
#SBATCH --job-name=otso
#SBATCH --account=project_462001140
#SBATCH --partition=standard-g
#SBATCH --nodes=1
#SBATCH --gpus-per-node=8
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=56
#SBATCH --mem=480G
#SBATCH --time=03:00:00
#SBATCH --output=/scratch/project_462001140/ammar/eccv/cran-pm/experiments/global1km/realtime/logs/%x_%j.out
# Otso step 3: FLEXGREEN then the forecast for one start day (one GCD is used; standard-g allocates whole nodes, and its
# queue is much shorter than small-g: user decision of 2026-10-10).
#   sbatch otso_job.sh <yyyy-mm-dd> [--no-emis] [--hindcast]   (inputs built in realtime/data/<date>/ by fetch.py + build.py;
#   --hindcast: also the forecast without fires, pred_nofires.npy, for the validation of the 2026 inputs)
set -uo pipefail
DATE=$1; shift
EMIS="--emis --emis-fallback"; HIND=0
for o in "$@"; do [ "$o" = "--no-emis" ] && EMIS=""; [ "$o" = "--hindcast" ] && HIND=1; done
unset PYTHONPATH
export MIOPEN_USER_DB_PATH=/tmp/${USER}-miopen-${SLURM_JOB_ID}
export MIOPEN_CUSTOM_CACHE_DIR=$MIOPEN_USER_DB_PATH
export OMP_NUM_THREADS=4
SIF=/appl/local/containers/sif-images/lumi-pytorch-rocm-6.1.3-python-3.12-pytorch-v2.4.1.sif
G1=/scratch/project_462001140/ammar/eccv/cran-pm/experiments/global1km
ENV="mkdir -p \$MIOPEN_USER_DB_PATH; unset PYTHONPATH; source /opt/miniconda3/bin/activate pytorch;
  source /projappl/project_462001140/envs/torchenv/bin/activate;
  export PYTHONPATH=/scratch/project_462001140/ammar/eccv/cran-pm/src; export MPLCONFIGDIR=/tmp/mpl-\$SLURM_PROCID; export HF_HOME=/tmp/hf-\$USER"
cd $G1
echo "start $(date -u +%FT%TZ) otso $DATE $EMIS"
srun singularity exec -B /projappl,/scratch,/pfs,/appl,/tmp $SIF bash -c "$ENV; python -u flexgreen.py run --src hres --rt-dir realtime/data/$DATE --particles 32 $EMIS --instant --all-cells --verbose"
rc=$?; echo "flexgreen rc=$rc $(date -u +%FT%TZ)"; [ $rc -ne 0 ] && exit $rc
srun singularity exec -B /projappl,/scratch,/pfs,/appl,/tmp $SIF bash -c "$ENV; cd realtime; python -u predict.py $DATE"
rc=$?; echo "predict rc=$rc $(date -u +%FT%TZ)"; [ $rc -ne 0 ] && exit $rc
if [ $HIND = 1 ]; then
  srun singularity exec -B /projappl,/scratch,/pfs,/appl,/tmp $SIF bash -c "$ENV; cd realtime; python -u predict.py $DATE --no-fires --out pred_nofires.npy"
  rc=$?; echo "predict (no fires) rc=$rc $(date -u +%FT%TZ)"
fi
exit $rc
