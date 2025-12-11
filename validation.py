import os
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from nibabel.orientations import io_orientation, aff2axcodes
from nibabel import as_closest_canonical

def load_nii(file_path):
    """Load a .nii or .nii.gz file and return the nibabel object."""
    try:
        img = nib.load(file_path)
        print(f"[OK] Loaded: {file_path}")
        return img
    except Exception as e:
        print(f"[ERROR] Failed to load {file_path}: {e}")
        return None

def check_shape_and_voxels(img):
    """Print shape and voxel dimensions."""
    print(f"Shape: {img.shape}")
    print(f"Voxel sizes (mm): {img.header.get_zooms()}")
    print(f"Data type: {img.get_data_dtype()}")

def check_orientation(img):
    """Print the orientation of the image and return canonical version."""
    axcodes = aff2axcodes(img.affine)
    print(f"Original orientation: {axcodes}")
    canonical_img = as_closest_canonical(img)
    canonical_axcodes = aff2axcodes(canonical_img.affine)
    if canonical_axcodes != axcodes:
        print(f"Reoriented to canonical: {canonical_axcodes}")
    return canonical_img

def check_non_empty(img):
    """Verify the scan has non-zero voxels."""
    data = img.get_fdata()
    nonzero_count = np.count_nonzero(data)
    if nonzero_count == 0:
        print("[WARNING] Scan is empty!")
    else:
        print(f"Non-zero voxels: {nonzero_count}")
    return data

def validate_nii(file_path):
    """Run all validation checks on a single NIfTI file."""
    img = load_nii(file_path)
    if img is None:
        return
    
    check_shape_and_voxels(img)
    img = check_orientation(img)
    data = check_non_empty(img)
validate_nii("sub-01/ses-1/anat/sub-01_ses-1_T1w.nii.gz")