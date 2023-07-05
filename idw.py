import geopandas as gpd
import numpy as np
import rasterio
import os

def idw_interpolation(shapefile_path, output_folder=None, power=2, radius=1.0, num_points=10, cell_size=0.01, exclude_columns=None):

    '''
    This function performs IDW interpolation on a shapefile with point features and saves the interpolated values as a raster TIFF for each attribute field. 
    The function uses the Inverse Distance Weighting (IDW) method to interpolate the values of the attribute fields based on the values of the nearest known points.

    Parameters: 
        shapefile_path (str): The path to the shapefile with point features to be interpolated. Must contain 'Lat' and 'Long' columns with the coordinates of the points.
        output_folder (str): The path to the folder where the interpolated values will be saved as raster TIFFs. If None, current working directory will be used.
        power (float): The power parameter of the IDW interpolation. It controls the influence of each data point on the interpolated values. 
                       Higher values give more weight to nearby points, resulting in a smoother interpolation. The default value is 2.
        radius (float): The radius parameter of the IDW interpolation. It defines the maximum distance between a data point and a target point for the data point to have an effect on the interpolation. Data points outside this radius are ignored. 
                        Smaller values give more localized interpolation, while larger values incorporate more distant points. The default value is 1.0.
        num_points (int): The number of points to generate in each dimension for the regular grid. This parameter determines the resolution of the resulting interpolated raster. 
                          Increasing this value will produce a denser grid and a higher-resolution raster. The default value is 100.
        cell_size (float): The size of each cell in the regular grid, specified as the distance between adjacent points in the grid. Depends on the coordinate system of the input shapefile.
                           Smaller values result in a higher-resolution raster with smaller cells. Adjust this parameter according to the desired spatial resolution of the output raster. The default value is 0.001.
        exclude_columns (list): A list of column names to exclude from the interpolation. The default value is None.

    Returns:
        xi (numpy.ndarray): A 2D array of x-coordinates of the regular grid points.
        yi (numpy.ndarray): A 2D array of y-coordinates of the regular grid points.
        interpolated_data (dict): A dictionary of interpolated values for each attribute field. The keys are the names of the attribute fields, and the values are 2D arrays of interpolated values for each grid point.
    
    '''

    if output_folder is None:
        output_folder = os.getcwd()

    # Read the shapefile using GeoPandas
    gdf = gpd.read_file(shapefile_path)

    # Exclude 'lat', 'lon', and geometry columns from attribute fields
    attribute_fields = [col for col in gdf.columns if col not in ['Lat', 'Long', 'geometry']]

    # Exclude additional columns specified by exclude_columns
    if exclude_columns:
        attribute_fields = [col for col in attribute_fields if col not in exclude_columns]

    # Extract the coordinates
    x = gdf['Long'].values.astype(float)
    y = gdf['Lat'].values.astype(float)

    # Define the grid extent based on the minimum and maximum coordinates
    xmin, ymin, xmax, ymax = np.min(x), np.min(y), np.max(x), np.max(y)

    # Generate a regular grid of points within the extent with smaller cell size
    xi = np.arange(xmin, xmax, cell_size)
    yi = np.arange(ymin, ymax, cell_size)
    xi, yi = np.meshgrid(xi, yi)

    interpolated_data = {}

    # Perform IDW interpolation for each attribute field
    for attr_field in attribute_fields:
        try:
            # Extract the attribute values and convert to float
            z = gdf[attr_field].astype(float).values

            # Perform IDW interpolation on the regular grid
            zi = idw(x, y, z, xi.flatten(), yi.flatten(), power=power, radius=radius)
            interpolated_data[attr_field] = zi

            # Save the interpolated values as a raster TIFF for each attribute field if output folder is provided
            if output_folder:
                tif_path = os.path.join(output_folder, f'field_{attr_field}.TIF')
                width = xi.shape[1]
                height = xi.shape[0]
                with rasterio.open(tif_path, 'w', driver='GTiff', height=height, width=width, count=1,
                                   dtype=zi.dtype, crs=gdf.crs, transform=rasterio.transform.from_origin(xmin, ymax, cell_size, cell_size)) as dst:
                    dst.write(zi.reshape(height, width), 1)
        except (ValueError, TypeError) as e:
            print(f"Error interpolating column '{attr_field}': {e}")

    return xi, yi, interpolated_data

def idw(x, y, z, xi, yi, power=2, radius=1.0):

    '''
    This function performs IDW interpolation on a set of points and returns the interpolated values for a set of target points.

    Parameters:
        x (numpy.ndarray): A 1D array of x-coordinates of the known points.
        y (numpy.ndarray): A 1D array of y-coordinates of the known points.
        z (numpy.ndarray): A 1D array of values of the known points.
        xi (numpy.ndarray): A 1D array of x-coordinates of the target points.
        yi (numpy.ndarray): A 1D array of y-coordinates of the target points.
        power (float): The power parameter of the IDW interpolation. It controls the influence of each data point on the interpolated values. Default value is 2.
        radius (float): The radius parameter of the IDW interpolation. It defines the maximum distance between a data point and a target point. Default value is 1.0.

    Returns:
        zi (numpy.ndarray): A 1D array of interpolated values for the target points.
        
    
    '''

    # Initialize interpolated values array
    zi = np.zeros_like(xi)

    for i in range(len(xi)):
        # Calculate the distances between the current point (xi[i], yi[i]) and all known points (x, y)
        distances = np.sqrt((xi[i] - x) ** 2 + (yi[i] - y) ** 2)

        # Calculate the weights based on the distances using Inverse Distance Weighting formula
        weights = 1 / (distances ** power)

        # Exclude points with zero weight (outside the radius)
        nonzero_weights = weights > 0.0
        if np.any(nonzero_weights):
            # Normalize the weights for nonzero points to sum up to 1
            weights_sum = np.sum(weights[nonzero_weights])
            if weights_sum != 0.0:
                weights[nonzero_weights] /= weights_sum

            # Calculate the interpolated value as the weighted average of known values
            zi[i] = np.sum(z[nonzero_weights] * weights[nonzero_weights])

    return zi
