import os
import SimpleITK as sitk
import numpy as np
import nibabel as nib

#turns the fuzzy mask into a binary mask
def binarify_hd_mask(input_path, output_path):
    mask = sitk.ReadImage(input_path)
    mask_array = sitk.GetArrayFromImage(mask)
    #probably we should do some experimentation with this number, maybe with the test-retest method?
    binary_mask_array = (mask_array > 128).astype(np.uint8)
    binary_mask = sitk.GetImageFromArray(binary_mask_array)
    binary_mask.CopyInformation(mask)
    sitk.WriteImage(binary_mask, output_path)
    print(f"Saved binary mask into: {output_path}")

#splits multi labeled masks into separe one label masks
def split_mask_by_label(input_path, output_dir):
    img = nib.load(input_path)
    data = img.get_fdata()
    affine = img.affine
    header = img.header
    labels = np.unique(data)
    labels = labels[labels != 0]
    for label in labels:
        label_mask = (data == label).astype(np.uint8)
        label_img = nib.Nifti1Image(label_mask, affine, header)
        base = os.path.basename(input_path)
        name, ext = os.path.splitext(base)
        output_path = os.path.join(output_dir, f"{name}_label_{int(label)}{ext}")
        nib.save(label_img, output_path)
        print(f"Saved split label {label} from {input} into: {output_path}")