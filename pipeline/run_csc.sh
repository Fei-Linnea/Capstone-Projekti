#!/bin/bash
# ============================================================================
# CSC Puhti Pipeline Launcher
# ============================================================================
# Launches the hippocampus pipeline on CSC Puhti using SLURM + Apptainer
#
# Each Snakemake rule is submitted as a separate SLURM job that runs
# inside the container - no dependency installation needed.
#
# Usage:
#   ./run_csc.sh --bids /path/to/bids --output /path/to/output [--dryrun]
#
# ============================================================================

set -e

# ============================================================================
# Configuration
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_DIR="$SCRIPT_DIR"
PROJECT="project_2001988"

# Container settings
CONTAINER_IMAGE="${CONTAINER_IMAGE:-/projappl/$PROJECT/containers/hippocampus-pipeline.sif}"

# ============================================================================
# Parse Arguments
# ============================================================================
BIDS_ROOT=""
DERIVATIVES_ROOT=""
DRYRUN=""
EXTRA_ARGS=""

print_usage() {
    echo "Usage: $0 --bids <path> --output <path> [options]"
    echo ""
    echo "Required:"
    echo "  --bids, -b      Path to BIDS root directory"
    echo "  --output, -o    Path to derivatives output directory"
    echo ""
    echo "Options:"
    echo "  --dryrun, -n    Dry run (don't submit jobs)"
    echo "  --container, -c Path to container SIF (default: /projappl/$PROJECT/containers/hippocampus-pipeline.sif)"
    echo "  --help, -h      Show this help"
    echo ""
    echo "Example:"
    echo "  $0 --bids /scratch/$PROJECT/my_study/bids --output /scratch/$PROJECT/my_study/derivatives"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --bids|-b)
            BIDS_ROOT="$2"
            shift 2
            ;;
        --output|-o)
            DERIVATIVES_ROOT="$2"
            shift 2
            ;;
        --container|-c)
            CONTAINER_IMAGE="$2"
            shift 2
            ;;
        --dryrun|-n)
            DRYRUN="--dryrun"
            shift
            ;;
        --help|-h)
            print_usage
            exit 0
            ;;
        *)
            EXTRA_ARGS="$EXTRA_ARGS $1"
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$BIDS_ROOT" || -z "$DERIVATIVES_ROOT" ]]; then
    echo "ERROR: --bids and --output are required"
    print_usage
    exit 1
fi

# ============================================================================
# Environment Setup
# ============================================================================
echo "============================================================"
echo "CSC Puhti - Hippocampus Pipeline"
echo "============================================================"
echo ""
echo "Configuration:"
echo "  BIDS root:        $BIDS_ROOT"
echo "  Output:           $DERIVATIVES_ROOT"
echo "  Container:        $CONTAINER_IMAGE"
echo "  Dry run:          ${DRYRUN:-no}"
echo ""

# Check container exists
if [[ ! -f "$CONTAINER_IMAGE" ]]; then
    echo "ERROR: Container not found at: $CONTAINER_IMAGE"
    echo ""
    echo "Build/pull the container first:"
    echo "  module load apptainer"
    echo "  apptainer pull $CONTAINER_IMAGE docker://ghcr.io/your-repo/hippocampus-pipeline:latest"
    echo ""
    echo "Or build from Dockerfile:"
    echo "  # On a machine with Docker:"
    echo "  docker build -t hippocampus-pipeline:latest pipeline/"
    echo "  docker save hippocampus-pipeline:latest | gzip > hippocampus-pipeline.tar.gz"
    echo "  # Copy to CSC, then:"
    echo "  apptainer build hippocampus-pipeline.sif docker-archive://hippocampus-pipeline.tar.gz"
    exit 1
fi

# Check BIDS directory
if [[ ! -d "$BIDS_ROOT" ]]; then
    echo "ERROR: BIDS directory not found: $BIDS_ROOT"
    exit 1
fi

# Create output directory
mkdir -p "$DERIVATIVES_ROOT"

# Create SLURM log directory
mkdir -p "$PIPELINE_DIR/logs/slurm"

# ============================================================================
# Load Modules (CSC specific)
# ============================================================================
echo "Loading modules..."
module purge 2>/dev/null || true
module load snakemake/7.32.4 2>/dev/null || {
    # Fallback: use module from scratch/projappl if installed there
    echo "Warning: snakemake module not found, trying to use from environment"
}

# ============================================================================
# Run Pipeline
# ============================================================================
echo ""
echo "Starting pipeline..."
echo "============================================================"

cd "$PIPELINE_DIR"

# Set container image as environment variable for Snakefile
export PIPELINE_CONTAINER="$CONTAINER_IMAGE"

snakemake \
    --profile config/profiles/csc \
    --config \
        bids_root="$BIDS_ROOT" \
        derivatives_root="$DERIVATIVES_ROOT" \
        container="$CONTAINER_IMAGE" \
    --singularity-args "--bind /scratch,/projappl,/users --env HSF_HOME=/users/$USER/.hsf" \
    $DRYRUN \
    $EXTRA_ARGS

echo ""
echo "============================================================"
if [[ -n "$DRYRUN" ]]; then
    echo "Dry run complete. Run without --dryrun to submit jobs."
else
    echo "Jobs submitted. Monitor with: squeue -u $USER"
fi
echo "============================================================"
