# Configuration layout

This folder contains:

- `config.yaml`: Pipeline configuration defaults (BIDS/derivatives paths, parameters).
- `profiles/`: Snakemake execution profiles for different environments.

Profile path depends on how you run:

- Using the pipeline wrapper inside the container: `--profile config/profiles/<name>`
- Running Snakemake directly from the repo root: `--profile pipeline/config/profiles/<name>`

## Profiles

### CSC
- Path: `pipeline/config/profiles/csc`
- Intended for CSC Puhti/Slurm.
- Uses the Snakemake executor-style profile (`executor: slurm`), which requires a Snakemake version that supports this profile format.
- Uses Apptainer via `software-deployment-method: apptainer`.

You will likely need to update these defaults for your project:

- `slurm_account`, `slurm_partition`
- `mem_mb`, `runtime`
- `tmpdir` (must be on shared storage visible to compute nodes)
- `apptainer-args` binds and environment variables

### TYKS
- Path: `pipeline/config/profiles/tyks`
- Intended for single-machine local execution inside the main container image.
- No per-rule containers and no conda; runs with local bash execution.
- Sets a default `cores: 16` (adjust for your machine).

## Notes

- Snakemake `--cores` supports special behavior: `--cores` without a value (or `--cores all`) means “use all available CPU cores”.
	- In this pipeline wrapper, omit `--cores` to use the profile default, or pass `--cores` (no value) to use all available cores.

Profiles mainly affect execution (local vs Slurm, scheduling defaults, logging/latency/retries). Pipeline inputs and parameters live in `config.yaml`.