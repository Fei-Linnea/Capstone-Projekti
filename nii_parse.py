import os
import SimpleITK as sitk
from radiomics import featureextractor
import numpy as np
import csv
import nibabel as nib


def mask_process(path_L, path_R, output):
    #combine left and right side of hippocamp
    mask = sitk.ReadImage("path_L")+sitk.ReadImage("path_R")
    mask_array = sitk.GetArrayFromImage(mask)
    #the hippodeep returns a different kind of mask so you have to 
    # turn 32-256 probability mask into binary mask with some threshold, 0.5 seemed pretty accurate
    binary_mask_array = (mask_array > 128).astype(np.uint8)
    binary_mask = sitk.GetImageFromArray(binary_mask_array)
    binary_mask.CopyInformation(mask)
    #write new combined mask binarified mask into a file
    sitk.WriteImage(binary_mask, "output")



#this is for parsing from hippodeep with left and right side combined
imagePath = 'sub-01/ses-1/anat/sub-01_ses-1_T1w.nii.gz'
maskPath = "combined_bin.nii.gz"
extractor = featureextractor.RadiomicsFeatureExtractor()
result = extractor.execute(imagePath, maskPath)
feature_name = 'original_shape_VoxelVolume'
if feature_name in result.keys():
    print(f"{feature_name} = {result[feature_name]}")


#this prints the hippocampus segments produced by hsf
def print_volumes(seg_path, img_path):
    seg = nib.load(seg_path)
    #fetches metadata from the segmented nii
    data = np.rint(seg.get_fdata()).astype(np.uint8)
    #fetches the "segments" as in labels, the hippocampus is split in 5 subregions so it returns 5 unique labels
    labels = np.unique(data)
    labels = labels[labels != 0]  # skip background
    extractor = featureextractor.RadiomicsFeatureExtractor()

    #this gets the volume for each label, pyradiomics has a multilabel but gpt said this is simpler, but might very well be hallucinations
    for label in labels:
        result = extractor.execute(img_path, seg_path, label=int(label))
        #here you can choose which feature to take
        voxel_volume = result.get("original_shape_VoxelVolume")
        print(f"Voxel Volume (label {int(label)}): {voxel_volume}")

#this is the cropped original image to only have the hippocampus, you can use the original image here sometimes?
#probably better to use the cropped on tho, might need testing
imagePath = "sub-01/ses-1/anat/hsf_outputs/sub-01_ses-1_T1w_left_hippocampus.nii.gz"
#the segmented mask hsf outputs is called seg_crop and it produces one for left and right hippocampus
seg_path = "sub-01/ses-1/anat/hsf_outputs/sub-01_ses-1_T1w_left_hippocampus_seg_crop.nii.gz"
print_volumes(seg_path, imagePath)
print("\n")

imagePath = "sub-01/ses-1/anat/hsf_outputs/sub-01_ses-1_T1w_right_hippocampus.nii.gz"
seg_path = "sub-01/ses-1/anat/hsf_outputs/sub-01_ses-1_T1w_right_hippocampus_seg_crop.nii.gz"
print_volumes(seg_path, imagePath)
#here i manually printed the total volume of all the subregions and it was 8205, where as hippodeep gave 7295 for the whole hippocampus
#don't know what we will do about this
print(557+1973+69+129+1214+572+2176+67+146+1302)