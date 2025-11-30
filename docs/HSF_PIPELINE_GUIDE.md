# ============================================================================
# HSF Pipeline - Build and Run Guide
# ============================================================================
# Simplified pipeline using HSF (Hippocampal Segmentation Factory)
# No conda complexity - direct pip installation
# ============================================================================

## What Changed?

### From Hippodeep to HSF:
1. **Simpler Docker image**: Python 3.11-slim + pip install (no conda/mamba)
2. **Simpler Snakefile**: Direct HSF command (no temp directory manipulation)
3. **Cleaner dependencies**: HSF[onnx] + Snakemake only

### Why HSF is Better:
- Direct output directory support (no in-place file writing workarounds)
- Single command-line tool with clean API
- Faster installation (pip only, ~200MB vs ~2GB)
- More segmentation options (5 subfields: DG, CA1, CA2, CA3, SUB)

## Build Instructions

### Step 1: Build Docker Image
```powershell
# Navigate to project root
cd D:\Work\BigBrain\radiomic-feature-extraction-hippocampus-morphometry

# Build the new HSF image
docker build -f pipeline/Dockerfile -t hsf-pipeline:latest .
```

**Expected output:**
- Image size: ~500MB (much smaller than conda-based image)
- Build time: 2-5 minutes

### Step 2: Verify HSF Installation
```powershell
# Check HSF is installed
docker run --rm hsf-pipeline:latest --version

# Test HSF command
docker run --rm hsf-pipeline:latest bash -c "hsf --help"
```

## Run Instructions

### Dry Run (Check Pipeline)
```powershell
docker run --rm `
  -v "D:\Work\Uni Work\Capstone\SampleDataset:/data" `
  -v "${PWD}/pipeline/workflow:/app/workflow" `
  -v "${PWD}/pipeline/config:/app/config" `
  -v "${PWD}/logs:/app/logs" `
  hsf-pipeline:latest `
  --snakefile /app/workflow/Snakefile `
  --cores 4 `
  --dry-run
```

### Full Run
```powershell
docker run --rm `
  -v "D:\Work\Uni Work\Capstone\SampleDataset:/data" `
  -v "${PWD}/pipeline/workflow:/app/workflow" `
  -v "${PWD}/pipeline/config:/app/config" `
  -v "${PWD}/logs:/app/logs" `
  hsf-pipeline:latest `
  --snakefile /app/workflow/Snakefile `
  --cores 4
```

### Interactive Shell (Debugging)
```powershell
docker run --rm -it `
  -v "D:\Work\Uni Work\Capstone\SampleDataset:/data" `
  -v "${PWD}/pipeline/workflow:/app/workflow" `
  -v "${PWD}/pipeline/config:/app/config" `
  hsf-pipeline:latest `
  bash
```

## File Structure

### Pipeline Structure:
```
pipeline/
  Dockerfile          # Simplified Docker image (Python 3.11 + pip)
  config/
    config.yaml       # HSF configuration
  workflow/
    Snakefile         # HSF segmentation workflow
    envs/             # (empty - no conda needed)
    scripts/          # Custom scripts
```

### Input Structure (BIDS):
```
/data/
  sub-01/
    ses-1/
      anat/
        sub-01_ses-1_T1w.nii.gz
  sub-02/
    ses-1/
      anat/
        sub-02_ses-1_T1w.nii.gz
```

### Output Structure (BIDS Derivatives):
```
/data/derivatives/hsf/
  sub-01/
    ses-1/
      anat/
        sub-01_ses-1_space-T1w_desc-hsf_dseg.nii.gz
  sub-02/
    ses-1/
      anat/
        sub-02_ses-1_space-T1w_desc-hsf_dseg.nii.gz
```

## Configuration Options

Edit `pipeline/config/config.yaml` to change:

### HSF Parameters:
- **contrast**: `"t1"` - MRI contrast type
- **margin**: `"[8,8,8]"` - ROI localization margin in voxels
- **segmentation_mode**: 
  - `"single_fast"` - Quick single model (default)
  - `"single_accurate"` - Slower but more accurate
  - `"bagging_fast"` - Ensemble of fast models
  - `"bagging_accurate"` - Ensemble of accurate models
- **ca_mode**: 
  - `""` - Whole hippocampus (no CA subdivision)
  - `"123"` - All CA subfields merged
  - `"1/23"` - CA1 separate, CA2+CA3 merged
  - `"1/2/3"` - All CA subfields separate (default)

## Troubleshooting

### Check if subjects are discovered:
```powershell
docker run --rm `
  -v "D:\Work\Uni Work\Capstone\SampleDataset:/data" `
  -v "${PWD}/pipeline/workflow:/app/workflow" `
  -v "${PWD}/pipeline/config:/app/config" `
  hsf-pipeline:latest `
  --snakefile /app/workflow/Snakefile `
  --dry-run
```

### View logs:
```powershell
# Logs are written to logs/hsf/sub-XX_ses-Y.log
cat logs/hsf/sub-01_ses-1.log
```

### Common Issues:

1. **No subjects found**:
   - Check BIDS structure matches: `sub-*/ses-*/anat/*_T1w.nii.gz`
   - Verify dataset is mounted at `/data`

2. **HSF command fails**:
   - Check HSF is installed: `docker run --rm hsf-pipeline:latest bash -c "python -c 'import hsf; print(hsf.__version__)'"`
   - Check models downloaded to container

3. **Output not BIDS compliant**:
   - HSF creates `*_seg_crop.nii.gz` which is moved to `*_desc-hsf_dseg.nii.gz`
   - Check Snakefile shell command for proper renaming

## Next Steps (Future Workflow)

After Step 1 (segmentation) completes:

### Step 2: Data Processing
- Use `nii_parse.py` to split/combine labels
- 5 labels: DG, CA1, CA2, CA3, SUB

### Step 3: Feature Extraction
- spharm-pdm for shape features
- PyRadiomics for texture features
- Output: CSV files with features

## Performance Notes

- **Build time**: ~2-5 minutes
- **Per-subject processing**: ~5-10 minutes (depends on image size)
- **Docker image size**: ~500MB (vs ~2GB for conda-based)
- **Memory usage**: ~2GB per subject
