import rasterio, os
from rasterio.enums import Resampling
from rasterio import Affine

def resample_raster(inpf, inp_name, resolution, verbose = True):

    '''
    This function resamples the input raster to the desired resolution.

    Parameters: 
        inpf (str): Input folder path containing the raster files.
        inp_name (str): Input raster file name.
        resolution (float): Desired resolution in meters.
        verbose (bool): If True, prints the processing status. Default is True.

    Returns:
        opf (str): Output folder path containing the resampled raster files.
    
    '''
    
    opf = os.path.join(inpf, f'Resampled_{resolution}m')
    os.makedirs(opf, exist_ok = True)
    
    if verbose: 
        print(f'Processing: {inp_name} at {resolution}m')
    
    with rasterio.open(os.path.join(inpf, inp_name)) as (r):
        x, y = r.res
        scale = x / resolution
        t = r.transform
        transform = Affine(t.a / scale, t.b, t.c, t.d, t.e / scale, t.f)
        height = r.height * scale
        width = r.width * scale
        profile = r.profile
        profile.update(transform = transform, driver = 'GTiff', height = height, width = width)
        data = r.read(out_shape = (r.count, int(height), int(width)), resampling = (Resampling.nearest))

    r.close()
    
    with (rasterio.open)((os.path.join(opf, inp_name)), 'w', **profile) as (dataset):
        dataset.write(data)
    dataset.close() 
    
    return opf

inpf = input('Enter the folder path containing images: \n')
cell_size = float(input('Enter the output cell size [in m, if CRS is UTM, else decimal degrees, if CRS is GCS]: '))

gtif = list(filter(lambda x: x.endswith(('tif', 'TIF', 'tiff', 'img', 'jp2')), os.listdir(inpf)))
for inp_name in gtif:
    resample_raster(inpf, inp_name, cell_size)
print('Done.')
