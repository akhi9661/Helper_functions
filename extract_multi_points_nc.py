import os, shutil, pandas as pd, rioxarray as rxr, xarray as xr, geopandas as gpd, rasterstats as rs, rasterio.crs as rio_crs

def extract_sr(rast_path, opf_tif, rast_name, shp_filename, out_df):

    '''
    This code extracts the mean value of a raster file for each point in a shapefile.

    Parameters:
        rast_path: Path to the folder containing the raster files. Original folder path. Inherited from main function.
        opf_tif: Path to the folder containing the GeoTIFF files
        rast_name: Name of the raster file
        shp_filename: Path to the shapefile layer
        out_df: Empty dataframe to store the extracted values

    Returns:
        src_rast: Raster file
        pts_crs: Shapefile layer
        out_df: Dataframe containing the extracted values
        output_path: Path to the folder containing the temporary shapefile
    
    '''

    print('Processing:', rast_name)
    src_filename = os.path.join(opf_tif, rast_name)
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
    
    col_name = os.path.basename(rast_name)
    src_pixel = rs.zonal_stats(temp_shp, src_rast.values,
                           affine = src_rast.rio.transform(),
                           geojson_out = True,
                           copy_properties = True,
                           stats = "mean")
    
    temp_df = gpd.GeoDataFrame.from_features(src_pixel)
    out_df[col_name] = temp_df['mean']
    
    return (src_rast, pts_crs, out_df, output_path)

def nc2tiff(rast_path, inp_name, variable):

    '''
    This code converts a NetCDF file to GeoTIFF format.

    Parameters:
        rast_path: Path to the folder containing the raster files. Original folder path. Inherited from main function.
        inp_name: Name of the raster file
        variable: Variable name to be extracted from the NetCDF file

    Returns:   
        opf: Path to the folder containing the GeoTIFF files
    
    '''
    
    opf = os.path.join(rast_path, 'GeoTIFF')
    os.makedirs(opf, exist_ok = True)
    
    file = os.path.join(rast_path, inp_name)
    print("Processing: " + file)
    
    ncfile = xr.open_dataset(file)
    pr = ncfile[variable]
    
    # Extract latitude and longitude variables
    lat = ncfile['lat']
    lon = ncfile['lon']
    
    # Select a specific time slice to convert to 2D array
    pr_2d = pr.isel(time=0)
    
    # Set geotransform using the latitude and longitude variables
    transform = (lon[0], lon[1] - lon[0], 0, lat[-1], 0, lat[1] - lat[0])
    
    # Create an empty dataset with CRS assigned
    dataset = xr.Dataset({"pr": pr_2d}, coords = {"lat": lat, "lon": lon})
    dataset.rio.write_crs(rio_crs.CRS.from_string('EPSG:4326'), inplace=True)
    
    op_name = os.path.join(opf, (os.path.basename(inp_name) + '.TIF'))
    dataset.rio.to_raster(op_name, transform = transform)
    
    ncfile.close
    
    return (opf)

def main(rast_path, shp_filename, variable = 'GPM_3IMERGHHL_06_precipitationCal', remove_temp = False):

    '''
    This code extracts the mean value of a raster file for each point in a shapefile. 
    The raster files are in NetCDF format and are converted to GeoTIFF format before extracting the values.

    Parameters:
        rast_path: Path to the folder containing the raster files. Original folder path. Inherited from main function.
        shp_filename: Path to the shapefile layer
        variable: Variable name to be extracted from the NetCDF file. Default value is 'GPM_3IMERGHHL_06_precipitationCal'
        remove_temp: Boolean value to remove the temporary (GeoTIFF) files. Default value is False. If True, the temporary files are removed.

    Returns:
        out_df: Dataframe containing the extracted values. The dataframe is also saved as an Excel file in the same folder as the raster files.
    '''
    
    out_df = pd.DataFrame()
    print('\nProcess: Converting NetCDF to GeoTIFF\n')
    file_list = list(filter(lambda x: x.endswith(('nc', 'NC')), os.listdir(rast_path)))
    for file in file_list:
        opf = nc2tiff(rast_path, file, variable = variable)
    print('\nProcess: Extracting multi-points \n')
    file_tiff = list(filter(lambda x: x.endswith(("TIF")), os.listdir(opf)))
    for gtif in file_tiff:
        src_rast, pts_crs, out_df, output_path = extract_sr(rast_path, opf, gtif, shp_filename, out_df)

    out_df.to_excel(os.path.join(rast_path, 'extracted.xlsx'), header = True) 
    
    if remove_temp:
        shutil.rmtree(opf)

    if os.path.exists(output_path):
        shutil.rmtree(output_path)
        
# ------- Function call ------- #
rast_path = input('Enter folder path containing raster [netcdf] files (e.g. /home/user/Downloads): \n')
shp_filename = input('Enter shapefile path (e.g. /home/user/Downloads/shapefile.shp): \n')
main(rast_path, shp_filename, variable = 'GPM_3IMERGHHL_06_precipitationCal', remove_temp = False)
