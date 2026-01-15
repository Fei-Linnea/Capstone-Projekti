import numpy as np
import pandas as pd
from radiomics import featureextractor

#extracts wanted pyradiomics features from nii.gz files with nii.gz mask
def extract_pyradiomics_features(imagePath, maskPath, features): 
    extractor = featureextractor.RadiomicsFeatureExtractor()
    extractor.disableAllFeatures() # Disable all features first
    extractor.enableFeatureClassByName('shape') # Enable only the features we need, this cuts down on computation time
    result = extractor.execute(imagePath, maskPath)
    data = {}
    for feature_name in features:
        if feature_name in result:
            data[feature_name] = result[feature_name]
        else:
            data[feature_name] = None
            print(f"Warning: Feature {feature_name} not found in pyradiomics output.")
    print("features extracted with pyradiomics")
    return data

#extracs point-wise curvature features from .vtk files    
def extract_curvatures(input):
    import pyvista as pv
    
    mesh = pv.read(input)
    
    # Check if mesh is empty
    if mesh.n_points == 0 or mesh.n_cells == 0:
        print(f"WARNING: Empty mesh detected: {input}. Returning NaN values.")
        # Return empty dataframe with expected columns
        return pd.DataFrame({
            "Mean": [np.nan],
            "Gaussian": [np.nan],
            "k1": [np.nan],
            "k2": [np.nan],
        })
    
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
        
        # Handle empty or all-NaN data
        if len(data) == 0 or np.all(np.isnan(data)):
            stats[col] = {
                "median": np.nan,
                "mean": np.nan,
                "std": np.nan,
                "min": np.nan,
                "max": np.nan,
                "25th_percentile": np.nan,
                "75th_percentile": np.nan,
            }
        else:
            # Filter out NaN values for statistics
            valid_data = data[~np.isnan(data)]
            if len(valid_data) == 0:
                stats[col] = {
                    "median": np.nan,
                    "mean": np.nan,
                    "std": np.nan,
                    "min": np.nan,
                    "max": np.nan,
                    "25th_percentile": np.nan,
                    "75th_percentile": np.nan,
                }
            else:
                stats[col] = {
                    "median": np.median(valid_data),
                    "mean": np.mean(valid_data),
                    "std": np.std(valid_data, ddof=1) if len(valid_data) > 1 else 0.0,
                    "min": np.min(valid_data),
                    "max": np.max(valid_data),
                    "25th_percentile": np.percentile(valid_data, 25),
                    "75th_percentile": np.percentile(valid_data, 75),
                }
    return stats
