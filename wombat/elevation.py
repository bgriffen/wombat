from wombat.datasets import Datasets,City
from osgeo import gdal, osr, gdal_array
import pandas as pd
from pyproj import Transformer
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mticker
from rasterio.transform import from_origin


import rasterio
from rasterio.transform import from_origin

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
    
class Elevation(Datasets):
    def __init__(self,dataset_path,city=None):
        super().__init__(dataset_path,city)
        
        self.ds = gdal.Open(self.elevation_tif_filename)
        if city is not None:
            self.City = City(city)
        
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

    def plot_elevation(self,include_points=False,gdf=None):
        # Create a figure and axis to plot on
        fig, ax = plt.subplots(constrained_layout=True)

        
         # The extent parameter takes bounding box in the form of (left, right, bottom, top)
        lon_min = self.gt[0] + (self.x_start * self.gt[1])
        lon_max = self.gt[0] + (self.x_end * self.gt[1])
        lat_min = self.gt[3] + (self.y_end * self.gt[5])  # Note the swapped y_end and y_start due to pixel origin on top left
        lat_max = self.gt[3] + (self.y_start * self.gt[5])

        # Plot the elevation data
        cax = ax.imshow(self.elevation_data, cmap='viridis', extent=[lon_min, lon_max, lat_min, lat_max])

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