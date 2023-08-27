import pyrosm
import os
import geopandas as gpd
import wombat.tools_buildings as tools_buildings

capitals = ['Brisbane',
            'Sydney',
            'Melbourne',
            'Hobart',
            'Adelaide',
            'Darwin',
            'Canberra',
            'Perth']

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
city2state = {
    "Sydney": "NSW",
    "Melbourne": "VIC",
    "Brisbane": "QLD",
    "Perth": "WA",
    "Adelaide": "SA",
    "Hobart": "TAS",
    "Canberra": "ACT",
    "Darwin": "NT",
}

addresses = {
    "Sydney": "Sydney, New South Wales, Australia",
    "Melbourne": "Melbourne, Victoria, Australia",
    "Brisbane": "Brisbane, Queensland, Australia",
    "Perth": "Perth, Western Australia, Australia",
    "Adelaide": "Adelaide, South Australia, Australia",
    "Hobart": "Hobart, Tasmania, Australia",
    "Canberra": "Canberra, ACT, Australia",
    "Darwin": "Darwin, Northern Territory, Australia",
}

class City:
    def __init__(self,name):
        self.name = name
        self.lat = caplatlon[name][0]
        self.lon = caplatlon[name][1]
        self.address = addresses[name]
        self.state = city2state[name]
        
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
        
        # OSMNX
        self.osmnx_path = os.path.join(dataset_path,"osmnx")
        self.osmnx_path_cache = os.path.join(dataset_path,"osmnx","cache")

        # Microsoft
        self.msft_path = os.path.join(self.footprint_path,'microsoft_buildings')
        
        # all school info
        self.school_info_filename = os.path.join(self.school_path,"school-location-2021.xlsx")
        self.school_acara_filename = os.path.join(self.school_path,"school-profile-2021.xlsx")
        self.school_acara_all_filename = os.path.join(self.school_path,"school-profile-2008-2021.xlsx")
        
        #self.fname_locations = dpath + "school-location-2021.xlsx"
        #self.fname_profiles = dpath + "school-profile-2021.xlsx"
        #self.fname_profiles_all = dpath + "school-profile-2008-2021.xlsx"
        #self.primary_boundaries = dpath + "primary_catchments_2022.json"
        #self.junior_secondary_boundaries = dpath + "junior_secondary_catchments_2022.json"
        #self.senior_boundaries = dpath + "senior_secondary_catchmets_2022.json"

        # Elevation
        self.elevation_tif_filename_elvis = os.path.join(self.elevation_path,"srtm-1sec-dems-v1-COG.tif")
        self.elevation_tif_filename_FABDEM = os.path.join(self.elevation_path,"Australia-FABDEM.tif")
        
        if city is not None:
            # Schools
            # catchments
            #self.school_junior_path = os.path.join(self.school_path,city,"2022_junior.json")
            #self.school_primary_path = os.path.join(self.school_path,city,"2022_primary.json")
            #self.school_senior_path = os.path.join(self.school_path,city,"2022_senior.json")
            fname_primary = None
            if city == "Adelaide":
                fname_primary = "PrimarySchoolZones2023EY.shp"
                fname_secondary = "HighSchoolZones2023EY.shp"
            elif city == "Brisbane":
                fname_primary = "2023-primary-catchments.kml"
                fname_secondary = "2023-senior-secondary-catchments.kml"
            elif city == "Sydney":
                fname_primary = "catchments_primary.shp"
                fname_secondary = "catchments_secondary.shp"
            elif city == "Melbourne":
                fname_secondary = "Standalone_seniorsec_2022.geojson "
                fname_primary = "Standalone_juniorsec_2022.geojson"
        
            if fname_primary is not None:
            #self.school_junior_path = os.path.join(self.school_path,city2state[city],"2023-junior-secondary-catchment.kml")
                self.school_primary_path = os.path.join(self.school_path,city2state[city],fname_primary)
                self.school_secondary_path = os.path.join(self.school_path,city2state[city],fname_secondary)
            
            self.osm_footprint_filename = os.path.join(self.footprint_path,"osm","new",f"{city}.geojson")
            self.msft_footprints_filename = os.path.join(self.footprint_path,"microsoft","SA3",f"{city}.geojson")
            self.combined_footprints_filename = os.path.join(self.footprint_path,"full",f"{city}.geojson")
            self.City = City(city)