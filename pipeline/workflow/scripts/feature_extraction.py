# Copyright (c) 2026 Team Big Brain
#
# This file is part of radiomic-feature-extraction-hippocampus-morphometry.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-3.0-or-later


"""
Feature extraction utilities for radiomics and mesh-based curvature analysis.

This module provides:

1. Shape-based radiomics feature extraction using PyRadiomics.
2. Point-wise curvature computation from VTK meshes using PyVista.
3. Statistical summarization of curvature metrics.

These functions are used during the feature extraction stage of the
hippocampus radiomic feature extraction pipeline.
"""

import numpy as np
import pandas as pd
import pyvista as pv
from radiomics import featureextractor


def extract_pyradiomics_features(imagePath, maskPath, features):
    """
    Extract selected PyRadiomics shape features from a masked image.

    The function initializes a PyRadiomics feature extractor, disables all
    features, and enables only the "shape" feature class to reduce
    computation time. It then extracts the requested features from the
    provided image and mask.

    Args:
        imagePath (str): Path to the input NIfTI image file (.nii or .nii.gz).
        maskPath (str): Path to the corresponding binary mask file.
        features (list[str]): List of feature names to extract from the
            PyRadiomics result dictionary.

    Returns:
        dict: Dictionary mapping feature names to their extracted values.
        If a requested feature is not found in the PyRadiomics output,
        its value is set to None.

    Notes:
        - Only shape features are enabled.
        - Scalar NumPy outputs are converted to native Python types.
    """
    extractor = featureextractor.RadiomicsFeatureExtractor()
    extractor.disableAllFeatures()
    extractor.enableFeatureClassByName('shape')

    result = extractor.execute(imagePath, maskPath)

    data = {}
    for feature_name in features:
        if feature_name in result:
            value = result[feature_name]
            if isinstance(value, np.ndarray) and value.size == 1:
                value = value.item()
            data[feature_name] = value
        else:
            data[feature_name] = None
            print(f"Warning: Feature {feature_name} not found in pyradiomics output.")

    print("features extracted with pyradiomics")
    return data


def extract_curvatures(input):
    """
    Compute point-wise curvature measures from a VTK mesh file.

    The function reads a mesh file, computes mean curvature, Gaussian
    curvature, and principal curvatures (k1, k2), and returns them as
    a pandas DataFrame.

    Args:
        input (str): Path to a VTK mesh file (.vtk).

    Returns:
        pandas.DataFrame: DataFrame containing point-wise curvature values
        with the following columns:
            - Mean
            - Gaussian
            - k1 (principal curvature 1)
            - k2 (principal curvature 2)

        If the mesh is empty, a DataFrame with NaN values is returned.
    """
    mesh = pv.read(input)

    if mesh.n_points == 0 or mesh.n_cells == 0:
        print(f"WARNING: Empty mesh detected: {input}. Returning NaN values.")
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


def calculate_curv_metrics(df):
    """
    Compute statistical summaries from point-wise curvature values.

    For each curvature type (Mean, Gaussian, k1, k2), the following
    statistics are calculated:

        - median
        - mean
        - standard deviation
        - 25th percentile
        - 75th percentile

    NaN values are ignored during computation. If all values are NaN or
    the input is empty, all statistics are set to NaN.

    Args:
        df (pandas.DataFrame): DataFrame containing curvature columns:
            - Mean
            - Gaussian
            - k1
            - k2

    Returns:
        dict: Nested dictionary structured as:

            {
                "Mean": {
                    "median": ...,
                    "mean": ...,
                    "std": ...,
                    "25th_percentile": ...,
                    "75th_percentile": ...
                },
                ...
            }

    Notes:
        - Standard deviation uses sample standard deviation (ddof=1).
        - If only one valid value exists, std is set to 0.0.
    """
    stats = {}
    curvature_cols = ["Mean", "Gaussian", "k1", "k2"]

    for col in curvature_cols:
        data = df[col].values

        if len(data) == 0 or np.all(np.isnan(data)):
            stats[col] = {
                "median": np.nan,
                "mean": np.nan,
                "std": np.nan,
                "25th_percentile": np.nan,
                "75th_percentile": np.nan,
            }
        else:
            valid_data = data[~np.isnan(data)]

            if len(valid_data) == 0:
                stats[col] = {
                    "median": np.nan,
                    "mean": np.nan,
                    "std": np.nan,
                    "25th_percentile": np.nan,
                    "75th_percentile": np.nan,
                }
            else:
                stats[col] = {
                    "median": np.median(valid_data),
                    "mean": np.mean(valid_data),
                    "std": np.std(valid_data, ddof=1) if len(valid_data) > 1 else 0.0,
                    "25th_percentile": np.percentile(valid_data, 25),
                    "75th_percentile": np.percentile(valid_data, 75),
                }

    return stats


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Feature extraction utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # PyRadiomics subcommand
    pyrad = subparsers.add_parser("pyradiomics", help="Extract PyRadiomics shape features")
    pyrad.add_argument("--image", required=True, help="Input image path")
    pyrad.add_argument("--mask", required=True, help="Input mask path")
    pyrad.add_argument("--features", nargs="+", required=True, help="Feature names")
    pyrad.add_argument("--subject", required=True)
    pyrad.add_argument("--session", required=True)
    pyrad.add_argument("--hemisphere", required=True)
    pyrad.add_argument("--label", required=True)
    pyrad.add_argument("--output", required=True, help="Output CSV path")

    # Curvature subcommand
    curv = subparsers.add_parser("curvature", help="Extract curvature features from VTK mesh")
    curv.add_argument("--vtk", required=True, help="Input VTK mesh path")
    curv.add_argument("--subject", required=True)
    curv.add_argument("--session", required=True)
    curv.add_argument("--hemisphere", required=True)
    curv.add_argument("--label", required=True)
    curv.add_argument("--output", required=True, help="Output CSV path")

    args = parser.parse_args()

    if args.command == "pyradiomics":
        features_dict = extract_pyradiomics_features(args.image, args.mask, args.features)
        features_dict['subject'] = args.subject
        features_dict['session'] = args.session
        features_dict['hemisphere'] = args.hemisphere
        features_dict['label'] = args.label
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        df = pd.DataFrame([features_dict])
        df.to_csv(args.output, index=False)

    elif args.command == "curvature":
        curvature_df = extract_curvatures(args.vtk)
        metrics_dict = calculate_curv_metrics(curvature_df)
        flat_metrics = {}
        for curv_type, stats in metrics_dict.items():
            for stat_name, value in stats.items():
                flat_metrics[f'{curv_type}_{stat_name}'] = float(value)
        flat_metrics['subject'] = args.subject
        flat_metrics['session'] = args.session
        flat_metrics['hemisphere'] = args.hemisphere
        flat_metrics['label'] = args.label
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        df = pd.DataFrame([flat_metrics])
        df.to_csv(args.output, index=False)
