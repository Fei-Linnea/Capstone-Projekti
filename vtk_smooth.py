import vtk

def smooth_vtk(input_path, output_path, iterations=50, relaxation=0.1):
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(input_path)
    reader.Update()
    polydata = reader.GetOutput()
    smoother = vtk.vtkSmoothPolyDataFilter()
    smoother.SetInputData(polydata)
    smoother.SetNumberOfIterations(iterations)
    smoother.SetRelaxationFactor(relaxation)
    smoother.FeatureEdgeSmoothingOff()
    smoother.BoundarySmoothingOff()
    smoother.Update()
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(output_path)
    writer.SetInputData(smoother.GetOutput())
    writer.Write()
    print(f"Saved smoothed model: {output_path}")
