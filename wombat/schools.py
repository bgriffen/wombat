import pandas as pd
from wombat.datasets import Datasets,City
import geopandas as gpd
class Schools(Datasets):
    def __init__(self, dataset_path,city):  
        super().__init__(dataset_path,city)
        self.City = City(city)
        
    def load(self):
        self.df_schools = pd.read_excel(self.school_info_filename,sheet_name='SchoolLocations 2021')
        self.df_acara = pd.read_excel(self.school_acara_filename,sheet_name='SchoolProfile 2021')
        
        self.gdf_junior = gpd.read_file(self.school_junior_path)
        self.gdf_primary = gpd.read_file(self.school_primary_path)
        self.gdf_senior = gpd.read_file(self.school_senior_path)
     