import csv
import os
import re
#from datetime import datetime

# Used for aggregating both radiomics and curvature data
def aggregate_region_data(hippocampus_data_L, DG_data_L, CA1_data_L, CA2_data_L, CA3_data_L, SUB_data_L,
                          hippocampus_data_R, DG_data_R, CA1_data_R, CA2_data_R, CA3_data_R, SUB_data_R):
    regions_data = {}
    regions_data['Hippocampus'] = {"L": hippocampus_data_L, "R": hippocampus_data_R}
    regions_data['DG'] = {"L": DG_data_L, "R": DG_data_R}   
    regions_data['CA1'] = {"L": CA1_data_L, "R": CA1_data_R}
    regions_data['CA2'] = {"L": CA2_data_L, "R": CA2_data_R}
    regions_data['CA3'] = {"L": CA3_data_L, "R": CA3_data_R}
    regions_data['SUB'] = {"L": SUB_data_L, "R": SUB_data_R}

    return regions_data

# Takes dictionaries of radiomics and curvature data produced by aggregate_region_data function and forms a single row for CSV
def form_row_from_data(image_path, radiomics_data, curvature_data):
    # Extract subject and session identifiers from BIDS filename (e.g. sub-01_ses-1_... or sub-THP0001_ses-THP0001CCF1_...)
    filename = os.path.basename(image_path)
    sub_match = re.search(r'\bsub-([^_]+)', filename)
    ses_match = re.search(r'ses-([^_]+)', filename)
    subject = sub_match.group(1) if sub_match else None
    session = ses_match.group(1) if ses_match else None

    # First elements: Subject and Session (identifiers without the 'sub-'/'ses-' prefix)
    row = {'Subject': subject, 'Session': session}

    # Add timestamp
    #row['Timestamp'] = datetime.now().isoformat()

    # Add data to the row
    for region in ['Hippocampus', 'DG', 'CA1', 'CA2', 'CA3', 'SUB']:
        for side in ['L', 'R']:
            # Add Radiomics features to the row
            for feature_name, value in radiomics_data.get(region, {}).get(side, {}).items():
                # Remove "original_shape_" prefix from feature name
                clean_feature_name = feature_name.replace("original_shape_", "")
                row[f'Radiomics_{region}_{side}_{clean_feature_name}'] = value
            # Add Curvature metrics to the row
            for curvature_type, stats in curvature_data.get(region, {}).get(side, {}).items():
                for stat_name, value in stats.items():
                    row[f'Curvature_{region}_{side}_{curvature_type}_curvature_{stat_name}'] = value

    return row

# Appends a row of data produced by form_row_from_data function to a CSV file, creating the file with headers if it doesn't exist
def append_csv(csv_path, row):
    file_exists = os.path.isfile(csv_path)

    with open(csv_path, mode='a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)