import os
import tempfile
import pyproj
import numpy as np
import pandas as pd
from tqdm import tqdm
import geopandas as gpd
import mercantile
import shapely.geometry
from functools import partial
from shapely.geometry import Point
from shapely.ops import transform
import wombat.helper as helper

"""
# Australian City Building Footprints Extraction Script

This script allows the extraction of building footprints for major Australian cities. It obtains data from a 
remote source, filters it by location (Australia), and iterates through predefined city coordinates.

For each city, it defines a polygonal 'area of interest' (AOI), and generates associated quad keys to define tiles within the AOI. 
The number and list of quad keys is printed for reference. 

The script combines rows of information specific to these tiles, then writes this data to a GeoJSON file 
named `{city}_building_footprints.geojson`, where {city} is the name of the current city being processed.

Please update the dictionary 'australian_capitals' if the list of cities or coordinates needs to be changed.

Output files will be saved in the same directory as the script.

"""

def create_buffer(lat, lon, radius=20):
    """
    Function to create a circular buffer around a given point in geographic coordinates.

    :param float lat: Latitude of the point.
    :param float lon: Longitude of the point.
    :param int radius: Radius of the buffer in kilometers. Default is 20 km.
    
    :return: A list of tuples each containing (Longitude, Latitude) of a point on the buffer circumference.
    :rtype: list of tuple
    
    :Example:

    >>> create_buffer(52.5200, 13.4050, radius=10)
    [(13.4050, 52.5308), (13.3953, 52.5216), ..., (13.4050, 52.5200)]
    """
    point = Point(lon, lat)
    proj_wgs84 = pyproj.Proj(init="epsg:4326")
    aeqd_proj = "+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0"
    project = partial(pyproj.transform, pyproj.Proj(aeqd_proj.format(lat=lat, lon=lon)), proj_wgs84)
    buffer = point.buffer(radius * 1000)  
    buffer = transform(project, buffer).exterior.coords[:]
    return buffer

def generate_geom(coords):
    """
    Function to generate a geometry dictionary representing a polygon. The input coordinates are expected
    in the form of a list of tuples each containing (Longitude, Latitude).

    :param list coords: List of tuples containing (Longitude, Latitude) coordinates for each point in the polygon.
    
    :return: Dictionary representing the Geometry of the polygon.
    :rtype: dict
    
    :Example:

    >>> generate_geom([(13.4050, 52.5200), (13.4550, 52.5400), (13.4050, 52.5600)])
    {'coordinates': [[(13.4050, 52.5200), (13.4550, 52.5400), (13.4050, 52.5600)]], 'type': 'Polygon'}
    """

    coord_l = [[[l[0], l[1]] for l in coords]]
    aoi_geom = {
        "coordinates": coord_l,
        "type": "Polygon",
    }
    return aoi_geom

def combine_rows(df, quad_keys, aoi_shape):
    """
    Function to combine rows from given dataframe based on provided QuadKeys. 
    It also filters rows based on their geometric relationship with `aoi_shape`.

    :param df: DataFrame containing mapping data.
        This DataFrame must contain column named "QuadKey" and "Url".
    :type df: pandas.DataFrame

    :param quad_keys: List of unique QuadKeys.
        Each QuadKey corresponds to a row in the dataframe.
    :type quad_keys: list of int

    :param aoi_shape: Shapely shape object that we check if it contains our geometries.
    :type aoi_shape: shapely.geometry.BaseGeometry

    :raises ValueError: If a QuadKey is found more than once or not at all in dataset.

    :return: List of dictionaries, each containing an 'id' and the corresponding 'geometry'.
    :rtype: list of dict

    :Example:

    >>> df = pd.DataFrame({'QuadKey': [1, 2], 'Url': ['url1', 'url2']})
    >>> quad_keys = [1, 2]
    >>> aoi_shape = Point(1, 1).buffer(1)
    >>> combine_rows(df, quad_keys, aoi_shape)
    [{'id': 0, 'geometry': <shapely.geometry.point.Point object at 0x7f5fbce41a90>}]
    """
    combined_rows = []
    idx = 0
    for quad_key in tqdm(quad_keys):
        rows = df[df["QuadKey"] == quad_key]
        if rows.shape[0] == 1:
            url = rows.iloc[0]["Url"]
            df2 = pd.read_json(url, lines=True)
            df2["geometry"] = df2["geometry"].apply(shapely.geometry.shape)

            for _, row in df2.iterrows():
                shape = row['geometry']
                if aoi_shape.contains(shape):
                    combined_rows.append({"id": idx, "geometry": shape})
                    idx += 1
        elif rows.shape[0] > 1:
            raise ValueError(f"Multiple rows found for QuadKey: {quad_key}")
        else:
            raise ValueError(f"QuadKey not found in dataset: {quad_key}")

    return combined_rows

def make_footprints(city, dataset_path):
    df = pd.read_csv("https://minedbuildings.blob.core.windows.net/global-buildings/dataset-links.csv")
    df = df[df["Location"] == "Australia"]
        
    coordinates = helper.caplatlon[city]
    lat, lon = coordinates
    polygon = create_buffer(lat, lon) # Assuming these two functions are defined elsewhere.
    aoi_geom = generate_geom(list(polygon))
    print(f"The coordinates for {city} are: {polygon}")

    aoi_shape = shapely.geometry.shape(aoi_geom)
    
    # Find bounds.
    minx, miny, maxx, maxy = aoi_shape.bounds
    # Generate quad keys using list comprehension instead of a loop.
    quad_keys = [int(mercantile.quadkey(tile)) for tile in mercantile.tiles(minx, miny, maxx, maxy, zooms=9)]

    print(f"The input area spans {len(quad_keys)} tiles: {quad_keys}")

    combined_rows = combine_rows(df, quad_keys, aoi_shape)

    # Combine writting into file.
    print(f"Saving file for {city}")
    schema = {"geometry": "Polygon", "properties": {"id": "int"}}
    fout = os.path.join(dataset_path,f"{city}_building_footprints.geojson") 
    with fiona.open(
        fout,"w",
        driver="GeoJSON",
        crs="EPSG:4326",
        schema=schema
    ) as f:
        f.write({"geometry": row["geometry"], "properties": {"id": row["id"]}} for row in combined_rows)

class Buildings:
    def __init__(self,city,dataset_path):
        self.city = city
        self.dataset_path = dataset_path
        
    def make_footprints(self):
        make_footprints(city=self.city,dataset_path=self.dataset_path)
        