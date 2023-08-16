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
    def __init__(self,dataset_path,city=None):
        self.dataset_path = dataset_path

        self.footprint_path = os.path.join(dataset_path,"footprints")

        self.boundary_path = os.path.join(dataset_path,"boundary")
        self.elevation_path = os.path.join(dataset_path,"elevation")
        self.school_path = os.path.join(dataset_path,"school")
        self.urbanity_path = os.path.join(dataset_path,"urbanity")
        self.school_path = os.path.join(dataset_path,"school")
        
        self.boundary_path_states_territories = os.path.join(dataset_path,"boundary","STE_2021_AUST_GDA2020.geojson")
        
        # OSM
        self.pbf_path = os.path.join(dataset_path,"pbf")
        self.pbf_filename = os.path.join(dataset_path,"pbf","australia-latest.osm.pbf")

        # Microsoft
        self.msft_path = os.path.join(self.footprint_path,'microsoft_buildings')
        # all school info
        self.school_info_filename = os.path.join(self.school_path,"school-location-2021.xlsx")
        self.school_acara_filename = os.path.join(self.school_path,"school-profile-2021.xlsx")
        
        # Elevation
        self.elevation_tif_filename = os.path.join(self.elevation_path,"srtm-1sec-dems-v1-COG.tif")
        
        if city is not None:
            # Schools
            # catchments
            self.school_junior_path = os.path.join(self.school_path,city,"2022_junior.json")
            self.school_primary_path = os.path.join(self.school_path,city,"2022_primary.json")
            self.school_senior_path = os.path.join(self.school_path,city,"2022_senior.json")
            self.osm_footprint_filename = os.path.join(self.footprint_path,"osm","new",f"{city}.geojson")
            self.msft_footprints_filename = os.path.join(self.footprint_path,"microsoft","SA3",f"{city}.geojson")
            self.combined_footprints_filename = os.path.join(self.footprint_path,"full",f"{city}.geojson")