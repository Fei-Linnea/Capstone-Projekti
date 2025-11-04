## Quick guide — build & run the hello-world pipeline (PowerShell-friendly)

This short guide shows how to build the Docker image and run the repository as a mounted volume using a relative/current-directory mount. The examples below are written for PowerShell (Windows). If you use Command Prompt (cmd.exe) or a Unix shell, see the alternative examples.

### 1) From the project root

Open PowerShell in the project root (the directory that contains `Dockerfile` and this repository). The commands assume you are already in the project root.

### 2) Build the Docker image

Run:

```powershell
docker build -t neuroimaging-pipeline .
```

This builds the image and tags it `neuroimaging-pipeline`.

### 3) Run the container and mount the current project directory

Use a volume mount that maps the current working directory into `/app` inside the container. This keeps paths relative to wherever you run the commands and ensures files produced by the pipeline are written to your host repository.

PowerShell (recommended):

```powershell
docker run --rm -it -v "${PWD}:/app" -w /app neuroimaging-pipeline
```

Notes:
- `${PWD}` expands to the current path in PowerShell and is wrapped in quotes to safely handle spaces.
- `--rm` removes the container after it exits (optional but convenient for interactive runs).
- `-w /app` sets the working directory inside the container so commands run from the project root.

If you prefer Command Prompt (cmd.exe) instead of PowerShell, use `%cd%`:

```cmd
docker run --rm -it -v "%cd%:/app" -w /app neuroimaging-pipeline
```

On Unix-like shells (bash/zsh):

```bash
docker run --rm -it -v "$(pwd):/app" -w /app neuroimaging-pipeline
```

### 4) Running the pipeline inside the container

If the image includes the pipeline tools (for example, `snakemake`), you can run the pipeline directly when starting the container. Example (PowerShell):

```powershell
docker run --rm -it -v "${PWD}:/app" -w /app neuroimaging-pipeline bash -lc "snakemake -s workflow/Snakefile --cores 1"
```

Or start an interactive shell and run commands manually:

```powershell
docker run --rm -it -v "${PWD}:/app" -w /app neuroimaging-pipeline bash
# then, inside the container shell:
# cd /app
# snakemake -s workflow/Snakefile --cores 1
```

Adjust `--cores` or other snakemake options as needed. If your image uses a different entrypoint or a different runner script, replace `snakemake -s workflow/Snakefile` with the appropriate command.

### 5) Helpful tips & troubleshooting

- Ensure Docker Desktop is running on Windows and you have file sharing enabled for the drive containing the project (usually enabled by default with Docker Desktop).
- If volume mounting fails or you see permission errors, try running PowerShell as Administrator or check Docker Desktop settings for shared drives.
- If you have Windows-style backslashes in paths, the examples above handle them because `${PWD}`/`%cd%` produce the native Windows path; Docker Desktop will translate as needed.
- If you want only a subfolder mounted, run the commands from the desired subfolder, or replace `${PWD}` with `${PWD}\subdir` (wrap in quotes). For example:

```powershell
docker run --rm -it -v "${PWD}\results:/app/results" -w /app neuroimaging-pipeline
```

### 6) Keep repository files visible on host

Files created by the pipeline (for example `results/`, `logs/`) are written to the mounted folder and will appear in your host workspace. Note: the repository already contains a `.gitignore` that excludes `.snakemake/`, `logs/`, and `results/` by default.

---

If you want, I can add a small `Makefile` or PowerShell script (`run.ps1`) that wraps the build + run commands to make this a single command (helpful for reproducibility). Which would you prefer? A `Makefile`, a `run.ps1`, or both?
