import pyvista as pv
import numpy as np
import pandas as pd
from radiomics import featureextractor

#extracts wanted pyradiomics features from nii.gz files with nii.gz mask
def extract_pyradiomics_features(imagePath, maskPath, features): 
    extractor = featureextractor.RadiomicsFeatureExtractor()
    result = extractor.execute(imagePath, maskPath)
    data = {}
    for feature_name in features:
        if feature_name in result:
            data[feature_name] = result[feature_name]
        else:
            data[feature_name] = None
    print("features extracted with pyradiomics")
    return data

#extracs point-wise curvature features from .vtk files    
def extract_curvatures(input):
    mesh = pv.read(input)
    H = mesh.curvature(curv_type='mean')
    mesh['Mean_Curvature'] = H
    K = mesh.curvature(curv_type='gaussian')
    mesh['Gaussian_Curvature'] = K
    disc = np.maximum(H**2 - K, 0.0)
    sqrt_disc = np.sqrt(disc)
    k1 = H + sqrt_disc
    k2 = H - sqrt_disc
    mesh['Principal_Curvature_k1'] = k1
    mesh['Principal_Curvature_k2'] = k2
    df = pd.DataFrame({
        "Mean": mesh['Mean_Curvature'],
        "Gaussian": mesh['Gaussian_Curvature'],
        "k1": mesh['Principal_Curvature_k1'],
        "k2": mesh['Principal_Curvature_k2'],
    })
    return df

#calculates curvature metrics from a pandas dataframe of point-wise curvature features
def calculate_curv_metrics(df):
    stats = {}
    curvature_cols = ["Mean", "Gaussian", "k1", "k2"]
    for col in curvature_cols:
        data = df[col].values
        stats[col] = {
            "median": np.median(data),
            "mean": np.mean(data),
            "std": np.std(data, ddof=1),
            "min": np.min(data),
            "max": np.max(data),
            "25th_percentile": np.percentile(data, 25),
            "75th_percentile": np.percentile(data, 75),
        }
    return stats

#this is supposed to be done in snakemake i think? il leave it here as reference
"""
pyrdata = extract_pyradiomics_features('sub-01/ses-1/anat/sub-01_ses-1_T1w.nii.gz', "sub-01/ses-1/anat/sub-01_ses-1_T1w_binary.nii.gz", ['original_shape_VoxelVolume', "original_shape_SurfaceVolumeRatio"])
curv_data = extract_curvatures("smoothed_vtk/label_1_pp_surf_SPHARM_smooth.vtk")
curv_metrics = calculate_curv_metrics(curv_data)
summary_statistics = pd.DataFrame([ {**curv_metrics, **pyrdata} ])
curv_data.to_csv("curvatures/curvatures_pointwise.csv", index=False)
curv_metrics.to_csv("curvatures/curvatures_statistics.csv")
print("Point-wise curvatures and summary statistics saved.")"""
