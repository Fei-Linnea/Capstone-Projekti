import nibabel as nib
import numpy as np
from skimage.measure import marching_cubes
from skimage.morphology import remove_small_objects, ball
from scipy.ndimage import binary_fill_holes, binary_closing, binary_opening
import os
import pyvista as pv



def nii_to_vtk(input_path, output_path, min_voxel_count=20, smooth_iters=50, plot_png_path=None, plot_html_path=None, enable_interactive_plot=False):
    img = nib.load(input_path)
    data = img.get_fdata().astype(bool)
    
    # Check if mask is empty or has too few voxels
    voxel_count = np.sum(data)
    if voxel_count == 0 or voxel_count < min_voxel_count:
        # Create empty VTK file as placeholder
        empty_mesh = pv.PolyData()
        empty_mesh.save(output_path, binary=True)
        
        # Create empty PNG if requested
        if plot_png_path:
            os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
            plotter = pv.Plotter(off_screen=True)
            plotter.set_background("white")
            plotter.add_text(f"Empty mask\n({voxel_count} voxels)", font_size=12)
            plotter.show(auto_close=False)
            plotter.screenshot(plot_png_path)
            plotter.close()
        
        # Log warning
        print(f"WARNING: Mask has only {voxel_count} voxels (min={min_voxel_count}). Created empty mesh: {input_path}")
        return
    
     # fill small holes
    _tmp = binary_fill_holes(data)
    if np.sum(_tmp) != 0:
        data = _tmp

    # close small openings
    _tmp = binary_closing(data, ball(3))
    if np.sum(_tmp) != 0:
        data = _tmp

    # remove  spikes
    _tmp = binary_opening(data, ball(1))
    if np.sum(_tmp) != 0:
        data = _tmp

    # Remove small objects
    _tmp = remove_small_objects(data, min_size=min_voxel_count)
    if np.sum(_tmp) != 0:
        data = _tmp
    
    # Check again after cleaning - might be empty now
    voxel_count_after = np.sum(data)
    if voxel_count_after == 0:
        # Create empty VTK file as placeholder
        empty_mesh = pv.PolyData()
        empty_mesh.save(output_path, binary=True)
        
        # Create empty PNG if requested
        if plot_png_path:
            os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
            plotter = pv.Plotter(off_screen=True)
            plotter.set_background("white")
            plotter.add_text(f"Empty after cleanup\n(removed small objects)", font_size=12)
            plotter.show(auto_close=False)
            plotter.screenshot(plot_png_path)
            plotter.close()
        
        print(f"WARNING: Mask became empty after removing small objects. Created empty mesh: {input_path}")
        return
    
    spacing = img.header.get_zooms()
    
    try:
        verts, faces, _, _ = marching_cubes(
            data,
            level=0.5,
            spacing=spacing
        )
    except ValueError as e:
        # Handle marching cubes errors (e.g., "Surface level must be within volume data range")
        print(f"WARNING: Marching cubes failed for {input_path}: {e}. Creating empty mesh.")
        empty_mesh = pv.PolyData()
        empty_mesh.save(output_path, binary=True)
        
        if plot_png_path:
            os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
            plotter = pv.Plotter(off_screen=True)
            plotter.set_background("white")
            plotter.add_text(f"Marching cubes failed\n{str(e)[:50]}", font_size=10)
            plotter.show(auto_close=False)
            plotter.screenshot(plot_png_path)
            plotter.close()
        return
    
    faces_flat = np.c_[np.full(len(faces), 3), faces].ravel()
    mesh = pv.PolyData(verts, faces_flat)
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

