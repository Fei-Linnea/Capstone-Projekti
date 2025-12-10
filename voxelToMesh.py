import nibabel as nib
import numpy as np
from skimage.measure import marching_cubes
from skimage.morphology import remove_small_objects
import pyvista as pv



def nii_to_vtk(input_path, output_path, min_voxel_count=20, smooth_iters=50, decimation_degree=0.7):
    img = nib.load(input_path)
    data = img.get_fdata().astype(bool)
    data = remove_small_objects(data, min_size=min_voxel_count)
    spacing = img.header.get_zooms() 
    verts, faces, _, _ = marching_cubes(
        data,
        level=0.5,
        spacing=spacing
    )
    faces_flat = np.c_[np.full(len(faces), 3), faces].ravel()
    mesh = pv.PolyData(verts, faces_flat)
    mesh = mesh.decimate(decimation_degree)
    mesh = mesh.smooth(n_iter=smooth_iters, relaxation_factor=0.1)
    mesh.compute_normals(inplace=True)
    mesh.save(output_path, binary=True)
    mesh.plot(smooth_shading=True)

