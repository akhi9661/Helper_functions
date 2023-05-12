import rasterio, os, numpy as np
from scipy.signal import convolve2d

def convolve(folder, inp_name):
        
    opf = os.path.join(folder, 'Output')
    os.makedirs(opf, exist_ok = True)
    
    print(f'Processing: {inp_name}')
    
    with rasterio.open(os.path.join(folder, inp_name)) as r:
        img = r.read(1).astype('float32')
        param = r.profile
    
    kernel = np.ones((3, 3))/(9)
    aod_convolved = convolve2d(img, kernel, mode = 'valid')
    with (rasterio.open)((os.path.join(opf, 'Jaipur_' + inp_name)), 'w', **param) as (w):
        w.write(aod_convolved, 1)
    
    return 'Done'

inpf = input('Enter the folder path containing images: \n')

gtif = list(filter(lambda x: x.endswith(('tif', 'TIF', 'tiff', 'img', 'jp2')), os.listdir(inpf)))
for inp_name in gtif:
    convolve(inpf, inp_name)
