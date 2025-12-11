import os
import numpy as np
import pandas as pd
import tempfile
import unittest
import pyvista as pv
from radiomics import featureextractor

from feature_extraction import extract_pyradiomics_features, extract_curvatures,calculate_curv_metrics

class TestCurvatureFeaturePipeline(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.dir = self.tempdir.name

        # --- Synthetic mesh for testing curvature extraction ---
        sphere = pv.Sphere(theta_resolution=10, phi_resolution=10, radius=1.0)
        self.mesh_path = os.path.join(self.dir, "sphere.vtk")
        sphere.save(self.mesh_path)

        # --- Synthetic NIfTI test files for pyradiomics ---
        # Pyradiomics requires valid images, but here we only ensure the function doesn't crash
        # and correctly handles missing features.
        self.fake_image = os.path.join(self.dir, "img.nii.gz")
        self.fake_mask = os.path.join(self.dir, "mask.nii.gz")
        fake_data = np.zeros((5, 5, 5))
        fake_mask_data = np.ones((5, 5, 5))
        featureextractor.imageoperations.writeImage(fake_data, self.fake_image, True)
        featureextractor.imageoperations.writeImage(fake_mask_data, self.fake_mask, True)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_extract_curvatures(self):
        df = extract_curvatures(self.mesh_path)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("Mean", df.columns)
        self.assertIn("Gaussian", df.columns)
        self.assertIn("k1", df.columns)
        self.assertIn("k2", df.columns)
        self.assertGreater(len(df), 0)

    def test_calculate_curv_metrics(self):
        df = pd.DataFrame({
            "Mean": np.random.rand(20),
            "Gaussian": np.random.rand(20),
            "k1": np.random.rand(20),
            "k2": np.random.rand(20)
        })
        stats = calculate_curv_metrics(df)
        for col in ["Mean", "Gaussian", "k1", "k2"]:
            self.assertIn(col, stats)
            self.assertIn("median", stats[col])
            self.assertIn("mean", stats[col])
            self.assertIn("std", stats[col])

    def test_extract_pyradiomics_features_handles_missing(self):
        requested = ["original_shape_VoxelVolume", "nonexistent_feature"]
        data = extract_pyradiomics_features(self.fake_image, self.fake_mask, requested)
        self.assertIn("original_shape_VoxelVolume", data)
        self.assertIn("nonexistent_feature", data)
        self.assertIsNone(data["nonexistent_feature"])


if __name__ == "__main__":
    unittest.main()
