from wombat.datasets import Datasets,City
from osgeo import gdal, osr, gdal_array
import pandas as pd
from pyproj import Transformer
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mticker
from rasterio.transform import from_origin
import os

import rasterio
from rasterio.transform import from_origin
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly

# Function to find closest index
def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

def generate_test_dem():
    # Create a grid with simulated elevation data
    # Create an x-y grid
    x = np.linspace(-5, 5, 100)
    y = np.linspace(-5, 5, 100)
    X, Y = np.meshgrid(x, y)
    # Create elevation data (a simple sin wave pattern here for demonstration)
    Z = (
        1*np.exp(-((X-2)**2 + (Y-2)**2)) +
        0.7 * np.exp(-((X+1)**2 + (Y+1)**2)) +
        0.9 * np.exp(-((X+2)**2 + (Y-4)**2))+
        0.9 * np.exp(-((X+2)**2 + (Y-4)**2))
    )

    x = X.ravel()
    y = Y.ravel()
    z = Z.ravel()
    return x,X,y,Y,z,Z

    # Your position vector
    #x_pos, y_pos = 1,2
    #target = np.array([50,20,0.1]) #np.random.randint(0, 100, size=2)

    # Compute the indices in the meshgrid corresponding to x_pos and y_pos:
    #x_index = find_nearest(x, x_pos)
    #y_index = find_nearest(y, y_pos)

    # Fetch the height (elevation) from Z array
    #elevation = Z[y_index][x_index] # Note: Use y_index first because of row/column order in 2D NumPy arrays

def plot_test_dem(x,y,z,observer_x,observer_y,elevation):
    """Plots a 3D mesh with an observer point.

    Args:
        x (list): List of x-coordinates of the mesh vertices.
        y (list): List of y-coordinates of the mesh vertices.
        z (list): List of z-coordinates of the mesh vertices.
        observer_x (float): x-coordinate of the observer point.
        observer_y (float): y-coordinate of the observer point.
        elevation (float): Elevation of the observer point.

    Returns:
        go.Figure: A 3D plot figure.

    Example:
        x = [0, 1, 1, 0]
        y = [0, 0, 1, 1]
        z = [0, 0, 0, 0]
        observer_x = 0.5
        observer_y = 0.5
        elevation = 1.0
        plot = plot_test_dem(x, y, z, observer_x, observer_y, elevation)
        plot.show()
    """
    fig = go.Figure(data=[go.Mesh3d(x=x, y=y, z=z, color='lightpink', opacity=0.50)])

    fig.update_layout(
        autosize=False,
        width=1100,
        height=800,
        paper_bgcolor="LightSteelBlue",
        margin=dict(l=10, r=10, t=10, b=0), # new margin parameters
        scene=dict(
            camera=dict(eye=dict(x=2, y=1.5, z=0.7)),
            xaxis=dict(title_text='Longitude',
                    backgroundcolor="rgb(200, 200, 230)",
                    gridcolor="white",
                    showbackground=True,
                    zerolinecolor="white"),
            yaxis=dict(title_text='Latitude',
                    backgroundcolor="rgb(230, 200,230)",
                    gridcolor="white",
                    showbackground=True,
                    zerolinecolor="white"),
            zaxis=dict(title_text='Elevation',
                    backgroundcolor="rgb(230, 230,200)",
                    gridcolor="white",
                    showbackground=True,
                    zerolinecolor="white"),
            aspectmode = 'manual',
            dragmode = 'turntable',
        ),

    )

    fig.add_trace(go.Scatter3d(x=[observer_x], y=[observer_y], z=[elevation],
                            mode='markers',
                            marker=dict(size=6, color='green'),
                            name='Observer'))

    return fig

def compare_dems(data1,data2,extent1,extent2,title1="",title2=""):
    """Compares two elevation datset and creates a plotly figure with two heatmaps.
    
    Args:
        data1 (numpy.ndarray): The first dataset.
        data2 (numpy.ndarray): The second dataset.
        extent1 (tuple): The extent of the first dataset in the form (xmin, xmax, ymin, ymax).
        extent2 (tuple): The extent of the second dataset in the form (xmin, xmax, ymin, ymax).
        title1 (str, optional): The title for the first heatmap. Defaults to "".
        title2 (str, optional): The title for the second heatmap. Defaults to "".
    
    Returns:
        plotly.graph_objects.Figure: The subplot with the two heatmaps.
    """
    
    # Find global min and max
    global_zmin = min(data1.min(), data2.min())
    global_zmax = max(data1.max(), data2.max())

    # Define the subplot
    fig = make_subplots(rows=1, cols=2,subplot_titles=(title1, title2))

    # Create the heatmaps and add them to the subplot
    heatmap1 = go.Heatmap(z=data1,     
                        x=np.linspace(extent1[0],extent1[1], num=data1.shape[0]),
                        y=np.linspace(extent1[2],extent1[3], num=data1.shape[1]),
                        hovertemplate='Elevation: %{z}<extra></extra>m',
                        colorscale='Viridis', 
                        showscale=False,
                        colorbar=dict(title='Elevation'),
                        zmin=global_zmin, 
                        zmax=global_zmax)

    heatmap2 = go.Heatmap(z=data2,     
                        x=np.linspace(extent2[0],extent2[1], num=data2.shape[0]),
                        y=np.linspace(extent2[2],extent2[3], num=data2.shape[1]),
                        hovertemplate='Elevation: %{z}<extra></extra>m',
                        colorscale='Viridis', 
                        showscale=True,
                        colorbar=dict(title='Elevation'),
                        zmin=global_zmin, 
                        zmax=global_zmax)

    fig.add_trace(heatmap1, row=1, col=1)
    fig.add_trace(heatmap2, row=1, col=2)
    fig.update_xaxes(title_text='Longitude', row=1, col=1, matches='x2')
    fig.update_yaxes(title_text='Latitude', row=1, col=1, matches='y2')
    fig.update_xaxes(title_text='Longitude', row=1, col=2)
    return fig

def plot_dem(data,extent):
    """Plot a digital elevation model (DEM) using a heatmap.
    
    Args:
        data (numpy.ndarray): The elevation data to be plotted.
        extent (list): The extent of the data in the form [xmin, xmax, ymin, ymax].
    
    Returns:
        plotly.graph_objects.Figure: The figure object containing the DEM plot.
    """
    fig = make_subplots(rows=1, cols=1)
    heatmap2 = go.Heatmap(z=f,     
                        x=np.linspace(extent[0],extent[1], num=data.shape[0]),
                        y=np.linspace(extent[2],extent[3], num=data.shape[1]),
                        hovertemplate='Elevation: %{z}<extra></extra>m',
                        colorscale='Viridis', 
                        showscale=True,
                        colorbar=dict(title='Elevation'))
    fig.add_trace(heatmap2, row=1, col=1)
    fig.update_xaxes(title_text='Longitude', row=1, col=1)
    fig.update_yaxes(title_text='Latitude', row=1, col=1)
    fig.update_layout(autosize=False, width=800,height=800)
    return fig

def save_raster_gdal(input_ds, filename, array):
    """
    Save a raster from a numpy array 'array' with dimensions (X, Y)
    with the metadata of 'input_ds'
    
    :param object input_ds: input dataset
    :param str filename: output filename
    :param numpy.array array: array containing data to write
    """
    # Create the output raster file 
    driver = gdal.GetDriverByName('GTiff')
    
    out_ds = driver.Create(
        filename,
        input_ds.RasterXSize,
        input_ds.RasterYSize,
        1,
        gdal_array.NumericTypeCodeToGDALTypeCode(array.dtype)
    )
    
    # Set the geo-transform and projection based on the input file
    out_ds.SetGeoTransform(input_ds.GetGeoTransform())
    out_ds.SetProjection(input_ds.GetProjection())
    
    # Write the array data to the raster band
    out_ds.GetRasterBand(1).WriteArray(array)
    
    # Properly close the datasets to flush to disk
    out_ds.FlushCache()
    out_ds = None
    
    print(f"File saved at {filename}")


def save_to_raster_rasterio(data, lon, lat, x_res, y_res,crs, filename):
    """
    Save the provided numpy array 'data' to a GeoTiff file.

    Parameters:
    - data: 2D numpy array to save
    - lon: Longitude of the upper-left corner of the array
    - lat: Latitude of the upper-left corner of the array
    - x_res: Resolution in x direction (longitude) in degrees per pixel
    - y_res: Resolution in y direction (latitude) in degrees per pixel
    - filename: Output file name
    """

    # Define the GeoTransform. This includes the top left coordinates and the resolution.
    transform = from_origin(lon, lat, x_res, y_res)

    # Create the output file. 
    # The 'driver' specifies that we want to use GeoTiff.
    new_dataset = rasterio.open(
        filename,
        'w',
        driver='GTiff',

        # Set the coordinates system to WGS84 (i.e., EPSG:4326)
        #crs='EPSG:4326', 
        crs = crs, #'EPSG:4326',
        # Set the image dimensions and number of bands (1 for grayscale images)
        height=data.shape[0],
        width=data.shape[1],
        count=1,

        # Set the data type
        dtype=str(data.dtype),

        # Set the GeoTransform and data
        transform=transform
    )

    # Write the data to the file
    new_dataset.write(data, 1)

    # Close the file
    new_dataset.close()


def latlon_to_elevation(ds,gt, lons,lats):
    # Convert list of coordinates to numpy arrays
    lons = np.array(lons)
    lats = np.array(lats)

    # Vectorized computation of x and y
    xs = ((lons - gt[0]) / gt[1]) #.astype('int')
    ys = ((lats - gt[3]) / gt[5]) #.astype('int')

    # Initialize elevation array
    elevations = np.empty_like(lons, dtype=np.float32)

    # Read each pixel value. Looping here as GDAL's ReadAsArray does not support vectorized reads.
    for i in range(len(lons)):
        elevations[i] = ds.ReadAsArray(xs[i], ys[i], 1, 1)[0][0]
    return elevations

def visibility_map_target(elevation_grid, point):
    """Determines the visibility map for a target point in an elevation grid.
    
    Args:
        elevation_grid (numpy.ndarray): 2D array representing the elevation grid.
        point (tuple): Tuple containing the x, y, and h coordinates of the target point.
    
    Returns:
        numpy.ndarray: 2D array representing the visibility map, where True indicates visibility and False indicates non-visibility.
    """
    # Which Spots Can See The Target?
    x, y, h = point
    x = int(x)
    y = int(y)
    visible = np.ones_like(elevation_grid, dtype=bool)
    nrows, ncols = elevation_grid.shape

    # Iterate over all points in the grid
    for i in np.arange(nrows):
        for j in np.arange(ncols):
            line = list(bresenham(i, j, x, y))  # Switched order here

            highest_point = elevation_grid[i, j]  # Start with height at point (i,j)

            for xi, yi in line[1:]:  # Skip first point which is (i,j) itself
                if elevation_grid[xi, yi] > highest_point:
                    highest_point = elevation_grid[xi, yi]
                    if highest_point > h:  # If any point on the line is higher than the target, it's not visible
                        visible[i, j] = False
                        break  # No need to check rest of the line

    return visible

def visibility_map_source(elevation_grid, point):
    """Calculates the visibility map for a given elevation grid and target point.
    
    Args:
        elevation_grid (numpy.ndarray): 2D array representing the elevation grid.
        point (tuple): Tuple containing the x, y, and h coordinates of the target point.
    
    Returns:
        numpy.ndarray: 2D boolean array representing the visibility map, where True indicates visible spots and False indicates non-visible spots.
    """
    # Which Spots Can The Target See
    x,y,h = point
    x = int(x)
    y = int(y)
    visible = np.zeros_like(elevation_grid, dtype=bool)
    nrows, ncols = elevation_grid.shape
    for i in np.arange(nrows):
        for j in np.arange(ncols):
            line = list(bresenham(x, y, i, j))
            # check if there is a point taller than our target on the line of sight
            for xi, yi in line:
                if not (h >= elevation_grid[xi, yi]).any():
                    visible[i,j] = True
    return visible

import subprocess

def run_gdal_viewshed(x_index, y_index, a_nodata='-9999', f_format='GTiff', oz_value='0.01', tz_value='0,01', md_value='100', 
                      cc_value='0', mode='NORMAL', input_file='input.tif', output_file='output.tif'):
    cmd = ['gdal_viewshed',
           '-b', '1', 
           '-a_nodata', a_nodata, 
           '-f', f_format,
           '-oz', oz_value,     
           '-tz', tz_value,     
           '-md', md_value,
           '-ox', str(x_index),
           '-oy', str(y_index),    
           '-cc', cc_value,
           '-q',
           '-om', mode,
           input_file,
           output_file]
           
    subprocess.call(cmd)


class Elevation(Datasets):
    def __init__(self,dataset_path,city=None):
        super().__init__(dataset_path,city)
        
        if city is not None:
            self.City = City(city)
    
    def set_dataset(self,dataset='elvis'):
        assert dataset in ['elvis','fabdem'],print("Please use either 'elvis' or 'fabdem'.")
        if dataset == "elvis":
            fread = self.elevation_tif_filename_elvis
        elif dataset == "fabdem":
            fread = self.elevation_tif_filename_FABDEM
        
        self.dataset = dataset
        if os.path.exists(fread):
            self.ds = gdal.Open(fread)
            #self.arr = self.ds.ReadAsArray()
            self.raster_proj = self.ds.GetProjection()
            self.gt = self.ds.GetGeoTransform()
            self.gt_inv = gdal.InvGeoTransform(self.gt)
            self.source_srs = osr.SpatialReference()
            self.source_srs.ImportFromWkt(osr.GetUserInputAsWKT(self.raster_proj)) #"urn:ogc:def:crs:OGC:1.3:CRS84"))

            # define target projection based on the file
            target_srs = osr.SpatialReference()
            target_srs.ImportFromWkt(self.raster_proj)

            # convert 
            self.ct = osr.CoordinateTransformation(self.source_srs, target_srs)

    def get_elevation(self,lons,lats): 
        self.lons = lons
        self.lats = lats
        self.elevations = latlon_to_elevation(self.ds,self.gt,lons,lats)
        
    def make_section(self, lon, lat, box_width_km):
        
        # Convert the provided spatial coordinates into pixel coordinates
        center_x = int((lon - self.gt[0]) / self.gt[1])
        center_y = int((lat - self.gt[3]) / self.gt[5])

        # You have to get the km_per_pixel value from your .tif file's metadata.
        # Get the resolution of pixel in degrees from geotransform object
        x_res_degree = abs(self.gt[1])
        y_res_degree = abs(self.gt[5])

        # Convert resolution in degrees to resolution in km (assuming each degree is about 111km)
        x_res_km = x_res_degree * 111.32
        y_res_km = y_res_degree * 111.32

        # Now, calculate the box width in pixels based on the resolution in km.
        box_width_pixels_x = int(box_width_km / x_res_km)
        box_width_pixels_y = int(box_width_km / y_res_km)

        # Calculate the extent of the bounding box in pixels
        half_box_width_x = int(box_width_pixels_x / 2)
        half_box_width_y = int(box_width_pixels_y / 2)
        
        self.x_start = max(0, center_x - half_box_width_x)
        self.y_start = max(0, center_y - half_box_width_y)
        self.x_end = self.x_start + box_width_pixels_x
        self.y_end = self.y_start + box_width_pixels_y

        # Extract elevation data for this section
        self.elevation_data = self.ds.ReadAsArray(self.x_start, self.y_start, 
                                                  self.x_end-self.x_start, 
                                                  self.y_end-self.y_start)
         # The extent parameter takes bounding box in the form of (left, right, bottom, top)
        lon_min = self.gt[0] + (self.x_start * self.gt[1])
        lon_max = self.gt[0] + (self.x_end * self.gt[1])
        lat_min = self.gt[3] + (self.y_end * self.gt[5])  # Note the swapped y_end and y_start due to pixel origin on top left
        lat_max = self.gt[3] + (self.y_start * self.gt[5])
        self.extent = [lon_min, lon_max, lat_min, lat_max]
        
    #def plot_section_plotly(self):
    def plot_elevation(self,include_points=False,gdf=None):
        # Create a figure and axis to plot on
        fig, ax = plt.subplots(constrained_layout=True)

        # Plot the elevation data
        cax = ax.imshow(self.elevation_data, cmap='viridis', extent=self.extent)

        if include_points:
            for lon,lat in zip(self.lons,self.lats):
                ax.scatter(lon,lat,s=20,c='red')
        
        if gdf is not None:
            gdf.plot(color=None, edgecolor='black',ax=ax)

        # Format the ticks
        ax.xaxis.set_major_formatter(mticker.ScalarFormatter())
        ax.yaxis.set_major_formatter(mticker.ScalarFormatter())

        ax.xaxis.get_major_formatter().set_scientific(False)
        ax.yaxis.get_major_formatter().set_scientific(False)

        ax.xaxis.get_major_formatter().set_useOffset(False)
        ax.yaxis.get_major_formatter().set_useOffset(False)
        plt.xticks(rotation=45, ha='right')
        # Add a colorbar and labels
        fig.colorbar(cax, label='Elevation (m)')
        plt.title('Elevation Section')
        plt.show()

    def plot_plotly_dem(self):
        fig = plot_dem(self.elevation_data,extent=self.extent)
        
    def save_section(self,filename='tmptif.tif'):
        
        x_res_degree = abs(self.gt[1])
        y_res_degree = abs(self.gt[5])

        lon_start = self.gt[0] + self.x_start * self.gt[1]
        lat_start = self.gt[3] + self.y_start * self.gt[5]

        #save_to_raster_rasterio(self.elevation_data,
        #               lon_start,
        ###               lat_start,
        #               x_res_degree,
        #               y_res_degree,self.ds.crs,filename)
        
        save_raster_gdal(self.ds, filename, self.elevation_data)
        
