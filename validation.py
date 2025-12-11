import os
import nibabel as nib
import numpy as np
from nibabel.orientations import aff2axcodes
from nibabel import as_closest_canonical

def load_nii(file_path):
    try:
        img = nib.load(file_path)
        print(f"[OK] Loaded: {file_path}")
        return img
    except Exception as e:
        print(f"[ERROR] Failed to load {file_path}: {e}")
        return None

def check_shape_and_voxels(img, expected_shape=None):
    shape = img.shape
    print(f"Shape: {shape}")
    if expected_shape is not None and shape != expected_shape:
        print(f"[ERROR] Unexpected shape: {shape}")
        return False
    print(f"Voxel sizes (mm): {img.header.get_zooms()}")
    print(f"Data type: {img.get_data_dtype()}")
    return True

def check_orientation(img, expected_orientation=None):
    axcodes = aff2axcodes(img.affine)
    print(f"Original orientation: {axcodes}")
    if expected_orientation is not None and axcodes != expected_orientation:
        print(f"[ERROR] Unexpected orientation: {axcodes}")
        return False
    canonical_img = as_closest_canonical(img)
    canonical_axcodes = aff2axcodes(canonical_img.affine)
    if canonical_axcodes != axcodes:
        print(f"Reoriented to canonical: {canonical_axcodes}")
    return True

def check_non_empty(img):
    data = img.get_fdata()
    nonzero_count = np.count_nonzero(data)
    if nonzero_count == 0:
        print("[ERROR] Scan is empty!")
        return False
    print(f"Non-zero voxels: {nonzero_count}")
    return True

def validate_nii(file_path, expected_shape=None, expected_orientation=None):
    img = load_nii(file_path)
    if img is None:
        return False
    if not check_shape_and_voxels(img, expected_shape):
        return False
    if not check_orientation(img, expected_orientation):
        return False
    if not check_non_empty(img):
        return False
    return True

print(validate_nii("sub-01/ses-1/anat/sub-01_ses-1_T1w.nii.gz"))
