import os
import unittest
import tempfile
import numpy as np
import nibabel as nib
from skimage.morphology import ball
from voxelToMesh import nii_to_vtk

class TestNiiToVtk(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.dir = self.tempdir.name

        # Create a synthetic 3D binary NIfTI mask (sphere)
        data = np.zeros((20, 20, 20), dtype=np.uint8)
        xx, yy, zz = np.meshgrid(np.arange(20), np.arange(20), np.arange(20), indexing='ij')
        sphere = (xx - 10)**2 + (yy - 10)**2 + (zz - 10)**2 <= 5**2
        data[sphere] = 1

        self.nii_path = os.path.join(self.dir, "test_sphere.nii.gz")
        img = nib.Nifti1Image(data, affine=np.eye(4))
        nib.save(img, self.nii_path)
        self.vtk_path = os.path.join(self.dir, "output.vtk")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_nii_to_vtk_creates_file(self):
        nii_to_vtk(self.nii_path, self.vtk_path, min_voxel_count=5, smooth_iters=2, decimation_degree=0.5)
        self.assertTrue(os.path.exists(self.vtk_path))

if __name__ == '__main__':
    unittest.main()