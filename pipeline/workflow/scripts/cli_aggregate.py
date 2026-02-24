"""
CLI entry point for feature aggregation rules.

Handles:
- Per-subject aggregation of radiomics + curvature features across hemispheres
- Cross-subject summary aggregation

These operations were previously in Snakemake run: blocks but are now
standalone CLI scripts to avoid pickle serialization issues between
different Snakemake versions (host vs container).
"""

import argparse
import os
import sys

import pandas as pd

# Ensure sibling modules are importable when run as standalone script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aggregate_data import aggregate_region_data, form_row_from_data


def restructure_curvature_dict(flat_dict):
    """
    Convert flat curvature dict to nested dict.

    Example:
        {'Mean_median': 0.5, 'Mean_mean': 0.6}
        -> {'Mean': {'median': 0.5, 'mean': 0.6}}
    """
    nested = {}
    for key, value in flat_dict.items():
        parts = key.split('_', 1)
        if len(parts) == 2:
            curv_type, stat_name = parts
            if curv_type not in nested:
                nested[curv_type] = {}
            nested[curv_type][stat_name] = value
    return nested


def read_label_csvs(csv_files):
    """Read per-label CSV files and organise by label name."""
    label_data = {}
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        label = df['label'].values[0]
        feature_dict = {
            k: v for k, v in df.to_dict('records')[0].items()
            if k not in ['subject', 'session', 'hemisphere', 'label']
        }
        label_data[label] = feature_dict
    return label_data


def read_combined_csv(csv_file):
    """Read a combined-features CSV and return plain feature dict."""
    df = pd.read_csv(csv_file)
    return {
        k: v for k, v in df.to_dict('records')[0].items()
        if k not in ['subject', 'session', 'hemisphere', 'label']
    }


def read_label_curvature_csvs(csv_files):
    """Read per-label curvature CSVs and restructure to nested dicts."""
    label_data = {}
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        label = df['label'].values[0]
        flat_dict = {
            k: v for k, v in df.to_dict('records')[0].items()
            if k not in ['subject', 'session', 'hemisphere', 'label']
        }
        label_data[label] = restructure_curvature_dict(flat_dict)
    return label_data


def read_combined_curvature(csv_file):
    """Read combined curvature CSV and restructure to nested dict."""
    df = pd.read_csv(csv_file)
    flat = {
        k: v for k, v in df.to_dict('records')[0].items()
        if k not in ['subject', 'session', 'hemisphere', 'label']
    }
    return restructure_curvature_dict(flat)


# =========================================================================
# Subject-level aggregation
# =========================================================================

def aggregate_subject(args):
    """Aggregate all features for a single subject/session."""
    # --- Radiomics ---
    label_radiomics_L = read_label_csvs(args.label_radiomics_L)
    label_radiomics_R = read_label_csvs(args.label_radiomics_R)
    combined_radiomics_L = read_combined_csv(args.combined_radiomics_L)
    combined_radiomics_R = read_combined_csv(args.combined_radiomics_R)

    # --- Curvature ---
    label_curvature_L = read_label_curvature_csvs(args.label_curvature_L)
    label_curvature_R = read_label_curvature_csvs(args.label_curvature_R)
    combined_curvature_L = read_combined_curvature(args.combined_curvature_L)
    combined_curvature_R = read_combined_curvature(args.combined_curvature_R)

    # --- Aggregate ---
    radiomics_data = aggregate_region_data(
        combined_radiomics_L,
        label_radiomics_L.get('DG', {}),
        label_radiomics_L.get('CA1', {}),
        label_radiomics_L.get('CA2', {}),
        label_radiomics_L.get('CA3', {}),
        label_radiomics_L.get('SUB', {}),
        combined_radiomics_R,
        label_radiomics_R.get('DG', {}),
        label_radiomics_R.get('CA1', {}),
        label_radiomics_R.get('CA2', {}),
        label_radiomics_R.get('CA3', {}),
        label_radiomics_R.get('SUB', {}),
    )

    curvature_data = aggregate_region_data(
        combined_curvature_L,
        label_curvature_L.get('DG', {}),
        label_curvature_L.get('CA1', {}),
        label_curvature_L.get('CA2', {}),
        label_curvature_L.get('CA3', {}),
        label_curvature_L.get('SUB', {}),
        combined_curvature_R,
        label_curvature_R.get('DG', {}),
        label_curvature_R.get('CA1', {}),
        label_curvature_R.get('CA2', {}),
        label_curvature_R.get('CA3', {}),
        label_curvature_R.get('SUB', {}),
    )

    row = form_row_from_data(args.t1w_image, radiomics_data, curvature_data)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    pd.DataFrame([row]).to_csv(args.output, index=False)


# =========================================================================
# Cross-subject summary aggregation
# =========================================================================

def aggregate_all(args):
    """Concatenate all per-subject feature CSVs into a summary."""
    all_dfs = []
    issues_found = []

    for csv_file in args.input_files:
        df = pd.read_csv(csv_file)
        all_dfs.append(df)

        nan_columns = df.columns[df.isna().any()].tolist()
        if nan_columns:
            subject_id = df['Subject'].values[0] if 'Subject' in df.columns else 'unknown'
            session_id = df['Session'].values[0] if 'Session' in df.columns else 'unknown'
            issues_found.append(
                f"sub-{subject_id}_ses-{session_id}: "
                f"Empty masks or processing failures in {len(nan_columns)} features"
            )

    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df = combined_df.sort_values(['Subject', 'Session'])

    os.makedirs(os.path.dirname(args.output_summary), exist_ok=True)
    combined_df.to_csv(args.output_summary, index=False)

    with open(args.output_issues, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("PROCESSING ISSUES REPORT\n")
        f.write("=" * 80 + "\n\n")
        if issues_found:
            f.write(f"Found {len(issues_found)} subjects with processing issues:\n\n")
            for issue in issues_found:
                f.write(f"  - {issue}\n")
            f.write("\nNote: NaN values indicate empty masks (likely too few voxels in subregion)\n")
        else:
            f.write("No processing issues detected. All subjects completed successfully!\n")
        f.write("\n" + "=" * 80 + "\n")


# =========================================================================
# CLI entry point
# =========================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feature aggregation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- subject sub-command ---
    sub_p = subparsers.add_parser("subject", help="Aggregate features for one subject")
    sub_p.add_argument("--label-radiomics-L", nargs="+", required=True)
    sub_p.add_argument("--label-radiomics-R", nargs="+", required=True)
    sub_p.add_argument("--combined-radiomics-L", required=True)
    sub_p.add_argument("--combined-radiomics-R", required=True)
    sub_p.add_argument("--label-curvature-L", nargs="+", required=True)
    sub_p.add_argument("--label-curvature-R", nargs="+", required=True)
    sub_p.add_argument("--combined-curvature-L", required=True)
    sub_p.add_argument("--combined-curvature-R", required=True)
    sub_p.add_argument("--t1w-image", required=True)
    sub_p.add_argument("--output", required=True)

    # --- all sub-command ---
    all_p = subparsers.add_parser("all", help="Aggregate all subjects into summary")
    all_p.add_argument("--input-files", nargs="+", required=True)
    all_p.add_argument("--output-summary", required=True)
    all_p.add_argument("--output-issues", required=True)

    args = parser.parse_args()

    if args.command == "subject":
        aggregate_subject(args)
    elif args.command == "all":
        aggregate_all(args)
