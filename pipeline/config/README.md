# Configuration layout

- `config.yaml`: Primary default values.
- `profiles/`: Snakemake profiles for different environments. Activate with `--profile pipeline/config/profiles/<name>`.

## Profiles (Slurm and local)

### CSC
- Path: `pipeline/config/profiles/csc`
- Runs on CSC Slurm with Snakemake preinstalled (no top-level Docker).
- Uses rule-level `container:` directives (Singularity enabled in profile); no conda.

### TYKS
- Path: `pipeline/config/profiles/tyks`
- Runs inside the main Docker image (no per-rule containers, no conda); local execution.

Both profiles are templates: update `partition`, `account`, `mem_mb`, and `time` to your case, then run:
```
snakemake --profile pipeline/config/profiles/csc ...
```

Profiles only affect execution (cores/cluster submission/logging).