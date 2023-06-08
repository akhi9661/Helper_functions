def mosaic_rasters(path):

    '''
    This function mosaics rasters in a folder. It reprojects the rasters to the CRS of the first raster if CRS of all raster is not the same. 
    The output is a raster named 'mosaic.TIF' in the same folder as the input rasters.

    Parameters:
        path: Path to the folder containing the rasters to mosaic

    Returns:
        None
    
    '''
    
    import rasterio, os, glob, tempfile
    from rasterio.merge import merge
    from rasterio.crs import CRS
    from rasterio.warp import calculate_default_transform, reproject

    files = glob.glob(os.path.join(path, '*.TIF'))
    files_to_mosaic = []

    for file in files:
        files_to_mosaic.append(file)

    with rasterio.open(files_to_mosaic[0]) as src:
        param = src.profile
        src_crs = src.crs  # Get the CRS of the first raster

    # Check CRS compatibility
    temp_folder = tempfile.mkdtemp()  # Create a temporary folder
    reprojected_files = []  # Store the paths of the reprojected files

    for file in files_to_mosaic[1:]:
        with rasterio.open(file) as src:
            if src.crs != src_crs:
                # Reproject the raster to the CRS of the first raster
                transform, width, height = calculate_default_transform(src.crs, src_crs, src.width, src.height, *src.bounds)
                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': src_crs,
                    'transform': transform,
                    'width': width,
                    'height': height
                })
                # Create a temporary filename in the temporary folder
                temp_filename = os.path.join(temp_folder, os.path.basename(file))
                # Store the path of the reprojected file
                reprojected_files.append(temp_filename)
                with rasterio.open(temp_filename, 'w', **kwargs) as dst:
                    reproject(
                        source=rasterio.band(src, 1),
                        destination=rasterio.band(dst, 1),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=src_crs,
                        resampling=rasterio.enums.Resampling.nearest
                    )
            else:
                # Use the original file if CRS matches
                reprojected_files.append(file)

    # Mosaic the reprojected rasters
    mosaic, out_trans = merge(reprojected_files)
    param.update(height=mosaic.shape[1],
                 width=mosaic.shape[2],
                 transform=out_trans)

    with rasterio.open(os.path.join(path, 'mosaic.TIF'), 'w', **param) as dst:
        dst.write(mosaic)

    # Clean up temporary files and folder
    for file in reprojected_files:
        if file != os.path.join(path, 'mosaic.TIF'):
            os.remove(file)
    os.rmdir(temp_folder)

    return None

# ----------------- Example ----------------- #
# path = r'path/to/rasters/to/mosaic'
# mosaic_rasters(path)
