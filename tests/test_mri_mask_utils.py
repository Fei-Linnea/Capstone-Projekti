import os
import numpy as np
import nibabel as nib
import SimpleITK as sitk
import tempfile
import unittest

from nii_parse import binarify_hd_mask, combine_labels, split_one_label

class TestMRIMaskUtils(unittest.TestCase):
    def setUp(self):
        # Temporary directory for test files
        self.tempdir = tempfile.TemporaryDirectory()
        self.dir = self.tempdir.name

        # Create synthetic fuzzy mask for testing binarify_hd_mask
        self.fuzzy_mask = sitk.GetImageFromArray((np.random.rand(10, 10, 10) * 255).astype(np.uint8))
        self.fuzzy_path = os.path.join(self.dir, 'fuzzy.nii.gz')
        sitk.WriteImage(self.fuzzy_mask, self.fuzzy_path)

        # Create synthetic multi-label mask for combine_labels and split_one_label
        self.multi_label_data = np.zeros((10, 10, 10), dtype=np.uint8)
        self.multi_label_data[2:5, 2:5, 2:5] = 1
        self.multi_label_data[6:9, 6:9, 6:9] = 2
        self.multi_label_img = nib.Nifti1Image(self.multi_label_data, affine=np.eye(4))
        self.multi_label_path = os.path.join(self.dir, 'multi_label.nii.gz')
        nib.save(self.multi_label_img, self.multi_label_path)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_binarify_hd_mask(self):
        out_path = os.path.join(self.dir, 'binary.nii.gz')
        binarify_hd_mask(self.fuzzy_path, out_path)
        result = sitk.ReadImage(out_path)
        arr = sitk.GetArrayFromImage(result)
        self.assertTrue(set(np.unique(arr)).issubset({0, 1}))

    def test_combine_labels(self):
        out_path = os.path.join(self.dir, 'combined.nii.gz')
        combine_labels(self.multi_label_path, out_path)
        res = nib.load(out_path).get_fdata()
        self.assertTrue(set(np.unique(res)).issubset({0, 1}))
        self.assertEqual(res.sum(), np.count_nonzero(self.multi_label_data))

    def test_split_one_label(self):
        out_path = os.path.join(self.dir, 'label1.nii.gz')
        split_one_label(self.multi_label_path, out_path, label=1)
        res = nib.load(out_path).get_fdata()
        self.assertTrue(set(np.unique(res)).issubset({0, 1}))
        self.assertEqual(res.sum(), np.count_nonzero(self.multi_label_data == 1))


if __name__ == '__main__':
    unittest.main()
