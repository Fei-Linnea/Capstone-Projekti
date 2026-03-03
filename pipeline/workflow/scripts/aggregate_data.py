"""
Aggregation utilities for radiomics and curvature feature data.

This module provides helper functions to:

1. Combine left/right hemisphere feature dictionaries into a structured
   region-level dictionary.
2. Convert aggregated feature dictionaries into a single flattened row
   suitable for CSV export.
3. Append structured feature rows to a CSV file, creating headers if needed.

These functions are used during the final aggregation stage of the
hippocampus radiomic feature extraction pipeline.
"""

import csv, os, re


def aggregate_region_data(hippocampus_data_L, DG_data_L, CA1_data_L, CA2_data_L, CA3_data_L, SUB_data_L,
                          hippocampus_data_R, DG_data_R, CA1_data_R, CA2_data_R, CA3_data_R, SUB_data_R):
    """
    Combine region-wise radiomics or curvature data for both hemispheres.

    This function groups feature dictionaries by anatomical region and
    hemisphere (Left/Right) into a structured nested dictionary.

    Args:
        hippocampus_data_L (dict): Feature dictionary for left whole hippocampus.
        DG_data_L (dict): Feature dictionary for left dentate gyrus.
        CA1_data_L (dict): Feature dictionary for left CA1.
        CA2_data_L (dict): Feature dictionary for left CA2.
        CA3_data_L (dict): Feature dictionary for left CA3.
        SUB_data_L (dict): Feature dictionary for left subiculum.
        hippocampus_data_R (dict): Feature dictionary for right whole hippocampus.
        DG_data_R (dict): Feature dictionary for right dentate gyrus.
        CA1_data_R (dict): Feature dictionary for right CA1.
        CA2_data_R (dict): Feature dictionary for right CA2.
        CA3_data_R (dict): Feature dictionary for right CA3.
        SUB_data_R (dict): Feature dictionary for right subiculum.

    Returns:
        dict: Nested dictionary structured as:

            {
                "RegionName": {
                    "L": {...},
                    "R": {...}
                }
            }

        Where region names include:
        - Hippocampus
        - DG
        - CA1
        - CA2
        - CA3
        - SUB
    """
    regions_data = {}
    regions_data['Hippocampus'] = {"L": hippocampus_data_L, "R": hippocampus_data_R}
    regions_data['DG'] = {"L": DG_data_L, "R": DG_data_R}
    regions_data['CA1'] = {"L": CA1_data_L, "R": CA1_data_R}
    regions_data['CA2'] = {"L": CA2_data_L, "R": CA2_data_R}
    regions_data['CA3'] = {"L": CA3_data_L, "R": CA3_data_R}
    regions_data['SUB'] = {"L": SUB_data_L, "R": SUB_data_R}

    return regions_data


def form_row_from_data(image_path, radiomics_data, curvature_data):
    """
    Flatten radiomics and curvature feature dictionaries into a single CSV row.

    This function extracts subject and session identifiers from a BIDS-formatted
    filename and combines all region- and hemisphere-specific radiomics and
    curvature metrics into a single flat dictionary suitable for CSV writing.

    Args:
        image_path (str): Path to the input image file. Expected to follow
            BIDS naming convention (e.g., sub-01_ses-1_T1w.nii.gz).
        radiomics_data (dict): Nested region dictionary produced by
            ``aggregate_region_data`` containing radiomics features.
        curvature_data (dict): Nested region dictionary produced by
            ``aggregate_region_data`` containing curvature metrics.

    Returns:
        dict: A flattened dictionary representing one subject/session row.
        Keys follow this naming structure:

        - Radiomics_<Region>_<Side>_<FeatureName>
        - Curvature_<Region>_<Side>_<CurvatureType>_curvature_<Statistic>

        Additionally includes:
        - Subject
        - Session
    """
    # Extract subject and session identifiers from BIDS filename
    filename = os.path.basename(image_path)
    sub_match = re.search(r'\bsub-([^_]+)', filename)
    ses_match = re.search(r'ses-([^_]+)', filename)
    subject = sub_match.group(1) if sub_match else None
    session = ses_match.group(1) if ses_match else None

    # First elements: Subject and Session
    # Ensure they are stored as strings to preserve leading zeros (e.g., '001' not 1)
    row = {'Subject': str(subject) if subject else None, 'Session': str(session) if session else None}

    # Add data to the row
    for region in ['Hippocampus', 'DG', 'CA1', 'CA2', 'CA3', 'SUB']:
        for side in ['L', 'R']:
            # Add Radiomics features
            for feature_name, value in radiomics_data.get(region, {}).get(side, {}).items():
                clean_feature_name = feature_name.replace("original_shape_", "")
                row[f'{region}_{side}_{clean_feature_name}'] = value

            # Add Curvature metrics
            for curvature_type, stats in curvature_data.get(region, {}).get(side, {}).items():
                for stat_name, value in stats.items():
                    row[f'{region}_{side}_{curvature_type}_curvature_{stat_name}'] = value

    return row


def append_csv(csv_path, row):
    """
    Append a feature row to a CSV file.

    If the CSV file does not exist, it is created and a header row is written
    automatically. If it already exists, the new row is appended.

    Args:
        csv_path (str): Path to the CSV file.
        row (dict): Dictionary representing one subject/session row,
            typically produced by ``form_row_from_data``.

    Returns:
        None
    """
    file_exists = os.path.isfile(csv_path)

    with open(csv_path, mode='a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
