import os, pandas as pd, rioxarray as rxr, geopandas as gpd, earthpy.plot as ep, rasterstats as rs
from pylab import *

def extract_sr(rast_path, rast_name, shp_filename, out_df):
    
    print('Processing:', rast_name)
    src_filename = os.path.join(rast_path, rast_name)
    src_rast = rxr.open_rasterio(src_filename, masked=True).squeeze()
    cc = src_rast.rio.crs.to_proj4()
    crs = cc.split('=')[1]
    
    pts = gpd.read_file(shp_filename)
    pts_crs = pts.to_crs(crs)
    
    output_path = os.path.join(rast_path, "Temp_shp")
    
    if not os.path.isdir(output_path):
        os.mkdir(output_path)
    
    temp_shp = os.path.join(output_path, "temp_shp.shp")
    pts_crs.to_file(temp_shp)
    
    col_name = rast_name.split('.')[0]
    src_pixel = rs.zonal_stats(temp_shp, src_rast.values,
                           affine = src_rast.rio.transform(),
                           geojson_out = True,
                           copy_properties = True,
                           stats = "mean")
    
    temp_df = gpd.GeoDataFrame.from_features(src_pixel)
    out_df[col_name] = temp_df['mean']
    
    return (src_rast, pts_crs, out_df, output_path)

def main(rast_path, shp_filename, visual = False):
    
    out_df = pd.DataFrame()

    gtif = list(filter(lambda x: x.endswith(("TIF", "tif", "img", "jp2", "tiff")), os.listdir(rast_path)))
    for gi in gtif:
        src_rast, pts_crs, out_df, output_path = extract_sr(rast_path, gi, shp_filename, out_df)

    out_df.to_excel(os.path.join(rast_path, 'extracted.xlsx'), header = True) 

    if visual:
      
        fig, ax = plt.subplots(figsize = (10, 10))
        ep.plot_bands(src_rast, extent = plotting_extent(src_rast, src_rast.rio.transform()),
                      cmap = 'Greys',
                      title = "Random Points for Comparison",
                      scale = False,
                      ax = ax)

        pts_crs.plot(ax = ax, marker = 'o', markersize = 15, color = 'red')
        ax.set_axis_off()
        plt.show()

    if os.path.exists(output_path):
        shutil.rmtree(output_path)
        
rast_path = input('Enter folder path containing raster files: \n')
shp_filename = input('Enter the shapefile layer [path + filename.shp]: \n')
main(rast_path, shp_filename)
