import os, pandas as pd, numpy as np, geopandas as gpd, pyproj, rasterio
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from rasterio.transform import from_origin

def perform_kriging(input_data, 
                    start_column, 
                    kernel = C(1.0, (1e-3, 1e3)) * RBF(1.0, (1e-2, 1e2)),
                    use_external_drift = False, 
                    external_drift_column = None, 
                    export_shp = True, 
                    dest_folder = os.getcwd()):
    
    '''
    This function performs kriging interpolation on a CSV or point shapefile. 
    The input CSV or shapefile must contain columns for longitude ('lon'), latitude ('lat'), and the variables to be interpolated.

    The brief summary of kernel parameters is as follows: 
    The line kernel = C(1.0, (1e-3, 1e3)) * RBF(1.0, (1e-2, 1e2)) defines the kernel function used in the Gaussian process regression for kriging interpolation.
    In Gaussian process regression, the kernel function determines the shape and characteristics of the covariance matrix, 
    which represents the similarity between different data points. It quantifies how the values of nearby points are correlated and 
    provides information about the spatial structure of the data. 
    
    The kernel function is defined as a combination of two components: a constant kernel (C) and a radial basis function (RBF). 
    The constant kernel C(1.0, (1e-3, 1e3)) adds a constant term to the covariance matrix. 
    It allows for modeling a global trend in the data. The first argument 1.0 represents the initial value of the constant, 
    and the tuple (1e-3, 1e3) specifies the bounds within which the optimizer can adjust the constant during the fitting process.

    The radial basis function kernel RBF(1.0, (1e-2, 1e2)) represents the spatial correlation between points based on their Euclidean distance. 
    It assigns higher weights to nearby points and lower weights to distant points. 
    The first argument 1.0 represents the initial value of the length scale parameter, which controls the smoothness of the correlation. 
    The tuple (1e-2, 1e2) specifies the bounds within which the optimizer can adjust the length scale during the fitting process.
    
    By combining the constant kernel and the radial basis function kernel using the multiplication operator *, 
    the resulting kernel captures both the global trend and the spatial correlation of the data. 
    This combined kernel is then used in the Gaussian process regression for kriging interpolation.

    Parameters: 
        input_data (str): The path to the input CSV or shapefile. 
        start_column (int): The index of the first column containing the variables to be interpolated. All the columns after this index will be interpolated.
        kernel (sklearn.gaussian_process.kernels.Kernel): The kernel function used in the Gaussian process regression for kriging interpolation. 
        use_external_drift (bool): Whether to use external drift for kriging interpolation. Default is False.
        external_drift_column (str): The name of the column containing the external drift variable. Default is None.
        export_shp (bool): Whether to export the input shapefile. Default is True.
        dest_folder (str): The path to the folder where the output files will be saved. Default is the current working directory.

    Returns:
        None    
    '''

    opf = os.path.join(dest_folder, 'Output_Kriging')
    os.makedirs(opf, exist_ok = True)
    
    if input_data.endswith('.csv'):
        data = pd.read_csv(input_data)
        geometry = gpd.points_from_xy(data['lon'], data['lat'])
        gdf = gpd.GeoDataFrame(data, geometry=geometry)
    elif input_data.endswith('.shp'):
        gdf = gpd.read_file(input_data)
    else:
        raise ValueError("Invalid input file format. Supported formats are CSV and Shapefile.")
    
    if export_shp:
        output_shapefile = os.path.join(opf, 'input_shapefile.shp')
        gdf.to_file(output_shapefile, driver = 'ESRI Shapefile')

    volume_columns = list(data.columns[start_column:])

    # Remove the external_drift_column from volume_columns if use_external_drift is True
    if use_external_drift and external_drift_column and external_drift_column in volume_columns:
        volume_columns.remove(external_drift_column)

    # Perform kriging interpolation for each volume column
    for volume_column in volume_columns:
        # Perform kriging interpolation
        # Extract coordinates from the GeoDataFrame
        lon = gdf['geometry'].x
        lat = gdf['geometry'].y

        # Prepare the input variables for kriging
        X = np.column_stack((lon, lat))

        # Define the target variable for kriging
        y = gdf[volume_column]

        # Perform linear regression to estimate external drift
        if use_external_drift and external_drift_column and external_drift_column in data.columns:
            external_drift = data[external_drift_column].values.reshape(-1, 1)
            poly = PolynomialFeatures(degree=1)
            X_drift = poly.fit_transform(external_drift)
            reg = LinearRegression().fit(X_drift, y)
            drift_estimate = reg.predict(X_drift)
            y -= drift_estimate

        # Perform kriging interpolation
        gpr = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        gpr.fit(X, y)

        # Define the grid to interpolate over
        grid_lon = gdf['geometry'].bounds['minx'].min(), gdf['geometry'].bounds['maxx'].max()
        grid_lat = gdf['geometry'].bounds['miny'].min(), gdf['geometry'].bounds['maxy'].max()

        # Define the resolution of the grid
        grid_res = 0.01  # Adjust the resolution as needed

        # Create the grid
        gridx = np.arange(grid_lon[0], grid_lon[1], grid_res)
        gridy = np.arange(grid_lat[0], grid_lat[1], grid_res)
        grid_lon, grid_lat = np.meshgrid(gridx, gridy)
        grid_points = np.column_stack((grid_lon.ravel(), grid_lat.ravel()))

        # Perform the kriging interpolation
        z = gpr.predict(grid_points)
        z = z.reshape(grid_lon.shape)

        # Export the interpolated product as a GeoTIFF
        output_tif = os.path.join(opf, f'interpolated_{volume_column}.TIF')

        # Define the transformation for the raster
        x_min, y_max, x_max, y_min = grid_lon.min(), grid_lat.max(), grid_lon.max(), grid_lat.min()
        width = grid_lon.shape[1]
        height = grid_lon.shape[0]
        pixel_width = (x_max - x_min) / width
        pixel_height = (y_max - y_min) / height
        transform = rasterio.transform.from_origin(x_min, y_max, pixel_width, pixel_height)

        # Write the interpolated product as a GeoTIFF
        with rasterio.open(output_tif, 'w', driver='GTiff', height=height, width=width, count=1,
                           dtype=z.dtype, crs=gdf.crs, transform=transform) as dst:
            dst.write(z, 1)
            
    return None

# ---------------------- Example ---------------------          
# input_file = r'path\to\file.csv'
# perform_kriging(input_data = input_file, start_column = 2, use_external_drift = True, external_drift_column = 'external_drift', export_shp = True)
