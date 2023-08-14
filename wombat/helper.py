import wget
import pyproj
from shapely.geometry import Point
from shapely.ops import transform
from functools import partial
from geopandas.tools import sjoin

def intersect_gdf(gdf_large,gdf_small):
    result = sjoin(gdf_large, gdf_small, how='inner', op='intersects')
    return result[gdf_small.columns]
    
def download_url(params):
    url, output_folder = params
    #print(f"Downloading {url}")
    wget.download(url, out=output_folder)

#def download_urls(list_of_urls, output_folder, num_threads=num_threads):
#    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
#        executor.map(download_url, [(url, output_folder) for url in list_of_urls])


def create_buffer(lat, lon, radius):
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
    print(radius)
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

