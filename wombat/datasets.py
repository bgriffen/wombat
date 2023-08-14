import pyrosm
import os
import geopandas as gpd
import wombat.tools_buildings as tools_buildings

caplatlon = {
    "Sydney": [-33.8688, 151.2093],
    "Melbourne": [-37.8136, 144.9631],
    "Brisbane": [-27.4698, 153.0251],
    "Perth": [-31.9505, 115.8605],
    "Adelaide": [-34.9285, 138.6007],
    "Hobart": [-42.8821, 147.3272],
    "Canberra": [-35.2809, 149.1300],
    "Darwin": [-12.4634, 130.8456],
}

class City:
    def __init__(self,name):
        self.name = name
        self.lat = caplatlon[name][0]
        self.lon = caplatlon[name][1]

class Datasets:
    def __init__(self,dataset_path,city):
        self.dataset_path = dataset_path
        #self.city = City(city)

        self.footprint_path = os.path.join(dataset_path,"footprints")


        self.boundary_path = os.path.join(dataset_path,"boundary")
        self.elevation_path = os.path.join(dataset_path,"elevation")
        self.school_path = os.path.join(dataset_path,"school")
        self.urbanity_path = os.path.join(dataset_path,"urbanity")

        # OSM
        self.osm_footprint_filename = os.path.join(self.footprint_path,"osm",f"{city}.geojson")
        self.pbf_path = os.path.join(dataset_path,"pbf")
        self.pbf_filename = os.path.join(dataset_path,"pbf","australia-latest.osm.pbf")

        # Microsoft
        self.msft_path = os.path.join(self.footprint_path,'microsoft_buildings')
        self.msft_footprints_filename = os.path.join(self.footprint_path,"microsoft","SA3",f"{city}.geojson")

        self.combined_footprints_filename = os.path.join(self.footprint_path,"full",f"{city}.geojson")