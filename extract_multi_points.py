import os
import shutil
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np

def extract_sr(rast_path, rast_name, shp_filename, out_df, verbose = True):
    
    if verbose:
        print('Processing:', rast_name)
    src_filename = os.path.join(rast_path, rast_name)

    # Read the raster file
    with rasterio.open(src_filename) as src:
        # Read the shapefile
        pts = gpd.read_file(shp_filename)
        pts_crs = pts.to_crs(src.crs)

        # Iterate over each row in the shapefile
        for idx, row in pts_crs.iterrows():
            # Get the geometry of the current row
            geom = row.geometry
            # Perform masking
            shapes = [geom]
            # Read the raster data within the shapefile bounds
            out_image, out_transform = mask(src, shapes, crop=True)
            # Calculate zonal statistics (mean)
            stats = {"mean": np.mean(out_image)}
            # Add zonal statistics to the output dataframe
            col_name = rast_name.split(".")[0]
            out_df.at[idx, col_name] = stats["mean"]

    return out_df

def main(rast_path, shp_filename, verbose = True):
    
    out_df = pd.DataFrame()

    gtif = list(filter(lambda x: x.endswith(("TIF", "tif", "img", "jp2", "tiff")), os.listdir(rast_path)))
    for gi in gtif:
        df = extract_sr(rast_path, gi, shp_filename, out_df, verbose)

    out_df.to_excel(os.path.join(rast_path, 'extracted.xlsx'), header = True) 

    if os.path.exists(output_path):
        shutil.rmtree(output_path)
        
    return df
