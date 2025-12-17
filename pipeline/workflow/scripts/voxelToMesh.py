import nibabel as nib
import numpy as np
from skimage.measure import marching_cubes
from skimage.morphology import remove_small_objects
import os
import pyvista as pv



def nii_to_vtk(input_path, output_path, min_voxel_count=20, smooth_iters=50, decimation_degree=0.7, plot_png_path=None, plot_html_path=None, enable_interactive_plot=False):
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

    # Optional headless plotting for report artifacts
    if plot_png_path or plot_html_path or enable_interactive_plot:
        # Enable off-screen rendering if running in headless/container
        os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
        
        # Generate PNG in a separate plotter context
        if plot_png_path:
            try:
                plotter_png = pv.Plotter(off_screen=True)
                plotter_png.add_mesh(mesh, smooth_shading=True)
                plotter_png.set_background("white")
                plotter_png.show(auto_close=False)
                plotter_png.screenshot(plot_png_path)
                plotter_png.close()
            except Exception as e:
                print(f"Warning: Failed to generate PNG: {e}")

        # Generate HTML in a separate plotter context
        if plot_html_path:
            try:
                plotter_html = pv.Plotter(off_screen=True)
                plotter_html.add_mesh(mesh, smooth_shading=True)
                plotter_html.set_background("white")
                plotter_html.export_html(plot_html_path)
                plotter_html.close()
            except Exception as e:
                print(f"Warning: Failed to generate HTML: {e}")

        # Optional interactive plotting (guarded; do not use by default in Docker)
        if enable_interactive_plot:
            try:
                # This may hang in headless environments; keep disabled unless explicitly enabled
                mesh.plot(smooth_shading=True)
            except Exception as e:
                print(f"Warning: Failed to plot interactively: {e}")

