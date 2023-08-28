import os
import pyrosm
os.environ['USE_PYGEOS'] = '0'
import geopandas as gpd
import pandas as pd
import shapely
import wombat.helper as helper
import mercantile
from geopandas.tools import sjoin
import os

def get_or_make_osm_footprints(city,pbf_path,fout):
    if not os.path.exists(fout):
        print("Getting OSM buildings...")
        try:
            osm_data = pyrosm.get_data(city,directory=pbf_path)
        except ValueError:
            print("Couldn't find city!",city)
            return
        osm = pyrosm.OSM(osm_data)
        osm_buildings = osm.get_buildings()
        osm_buildings.to_file(fout,engine='pyogrio')
    else:
        print("Loading OSM building data from file...")
        print(fout)
        osm_buildings = gpd.read_file(fout,engine='pyogrio')
    return osm_buildings

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
            raise print(f"Multiple rows found for QuadKey: {quad_key}")
        #else:
            raise print(f"QuadKey not found in dataset: {quad_key}")

    return combined_rows

def make_footprints(city, dataset_path,gdf=None,radius=None):
    df = pd.read_csv("https://minedbuildings.blob.core.windows.net/global-buildings/dataset-links.csv")
    df = df[df["Location"] == "Australia"]

    if radius is None and gdf is not None:
        aoi_shape = gdf.unary_union
        kind = 'poly'
    else:
        kind = 'radius'
        coordinates = helper.caplatlon[city]
        lat, lon = coordinates
        polygon = helper.create_buffer(lat, lon,30)
        aoi_geom = helper.generate_geom(list(polygon))
        print(f"The coordinates for {city} are: {polygon}")
        aoi_shape = shapely.geometry.shape(aoi_geom)

    # Find bounds.
    minx, miny, maxx, maxy = aoi_shape.bounds
    # Generate quad keys using list comprehension instead of a loop.
    quad_keys = [int(mercantile.quadkey(tile)) for tile in mercantile.tiles(minx, miny, maxx, maxy, zooms=9)]

    print(f"The input area spans {len(quad_keys)} tiles: {quad_keys}")

    crows = combine_rows(df, quad_keys, aoi_shape)
    print("COMBINED ROWS",len(crows))
    # Combine writting into file.
    print(f"Saving file for {city}")
    schema = {"geometry": "Polygon", "properties": {"id": "int"}}
    fout = os.path.join(dataset_path,f"{city}_{kind}_msft_footprints.geojson")
    print(fout)
    gdf = gpd.GeoDataFrame(crows)
    # Set the CRS
    gdf.crs = "EPSG:4326"

    # Write out the GeoJSON
    gdf.to_file(fout, driver='GeoJSON',engine='pyogrio')

#def fix_invalid_geoms(gdf):
#    gdf["geometry"] = gdf.buffer(0)
#    return gdf

def calc_intersection_between_msft_and_osm(buildings_msft_gdf,osm_buildings,fout=None):
    #if os.path.exists(fout) and not recalc:
    #    print("Reading overlaps...",fout)
    #    return gpd.read_file(fout,engine='pyogrio')
    
    print("> [ BUILDINGS ] Calculating overlaps...")
    buildings_msft_gdf['is_osm'] = False
    osm_buildings['is_osm'] = True
    overlaps = sjoin(buildings_msft_gdf, osm_buildings, how='inner', op='intersects')
    print("> [ BUILDINGS ] Calculating non-overlaps...")
    print("> [ BUILDINGS ] Percent Objects Overlap: %3.2f" % (osm_buildings.shape[0]/len(overlaps)))
    msft_not_in_osm = buildings_msft_gdf.loc[~buildings_msft_gdf.index.isin(overlaps.index)][['id','is_osm','geometry']]
    #print(non_overlapping.columns)
    unique_buildings = pd.concat([osm_buildings, msft_not_in_osm])
    #print(unique_buildings.isna().sum())
    #print(unique_buildings.dtypes)
    #fout = os.path.join(dataset_path,f"{city}_{kind}_combined_footprints.geojson")
    #unique_buildings = unique_buildings.apply(fix_invalid_geoms, axis=1)
    #unique_buildings_reduced.to_file('output.geojson', driver='GeoJSON')
    unique_buildings_reduced = unique_buildings[['id','is_osm','geometry']]
    if fout is not None and not os.path.exists(fout):
        print("> [ BUILDINGS ] Saving...")
        unique_buildings_reduced.to_file(fout, driver='GeoJSON',engine='pyogrio')
    return unique_buildings_reduced, msft_not_in_osm


