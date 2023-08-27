import pandas as pd
from wombat.datasets import Datasets,City
import wombat.calcs as calcs
import geopandas as gpd
import fiona
fiona.supported_drivers['KML'] = 'rw'

class Schools(Datasets):
    """

    Source: https://acara.edu.au/contact-us/acara-data-access

    ACARA Data Access Program

    We collect, analyse and report statistical and related information about schools and the outcomes of schooling, as required by the Education Council under ACARA’s Charter.
    Our work in this area is undertaken under the Council’s Principles and protocols for reporting on schooling in Australia (2009), which guide and inform the use and publication of data generated in the process of measuring the performance of schooling in Australia.
    We provide access to the data collected for third parties under the Data Access Protocols – 2015 revision (PDF 218 kb). Please review the Protocols before submitting a data access application.

    * School Profile 2021 (xlsx, 2 MB) List of all Australian schools, enrolments, ICSEA, LBOTE, SEA
    * School Profile 2008-2021 (xlsx, 21 MB)
    * School Location 2021 (xlsx, 2 MB) List of all Australian schools, Long/Lat, LGA

    """

    def __init__(self, dataset_path,city):  
        super().__init__(dataset_path,city)
        self.City = City(city)
        
        self.schoolcols = ['School Name', 
                            'Suburb', 
                            'Postcode', 
                            'School Sector',
                            'School Type', 
                            'Campus Type',
                            'Year Range', 
                            'ICSEA Percentile', 
                            'Teaching Staff',
                            'Total Enrolments',
                            'Girls Enrolments', 
                            'Boys Enrolments',
                            'Language Background Other Than English - Yes (%)']
        
    def load(self,incl_timeseries=False):
        self.df_schools_all = pd.read_excel(self.school_info_filename,sheet_name='SchoolLocations 2021')
        self.df_acara_all = pd.read_excel(self.school_acara_filename,sheet_name='SchoolProfile 2021')
        
        self.df_schools = self.df_schools_all[self.df_schools_all['State'] == self.City.state]
        self.df_acara = self.df_acara_all[self.df_acara_all['State'] == self.City.state]

        #self.gdf_junior = gpd.read_file(self.school_junior_path,driver='KML')
        self.gdf_primary = gpd.read_file(self.school_primary_path) #,driver='KML')
        self.gdf_secondary = gpd.read_file(self.school_secondary_path) #,driver='KML')

    #def load(self, incl_timeseries=False):
        if incl_timeseries:
            self.df_schools_history = pd.read_excel(self.fname_profiles_all, sheet_name="SchoolProfile 2008-2021")

        school_cols = [
                # "Calendar Year",
                "ACARA SML ID",
                # "Location AGE ID",
                # "School AGE ID",
                "School Name",
                "Suburb",
                "State",
                "Postcode",
                "School Sector",
                "School Type",
                "Campus Type",
                # "Rolled Reporting Description",
                "Latitude",
                "Longitude",
                # "ABS Remoteness Area",
                # "ABS Remoteness Area Name",
                # "Meshblock",
                # "Statistical Area 1",
                # "Statistical Area 2",
                # "Statistical Area 2 Name",
                # "Statistical Area 3",
                # "Statistical Area 3 Name",
                # "Statistical Area 4",
                # "Statistical Area 4 Name",
                # "Local Government Area",
                # "Local Government Area Name",
                # "State Electoral Division",
                # "State Electoral Division Name",
                # "Commonwealth Electoral Division",
                # "Commonwealth Electoral Division Name",
            ]
        
        
        acara_cols = [
                # "Calendar Year",
                "ACARA SML ID",
                # "Location AGE ID",
                # "School AGE ID",
                # "School Name",
                # "Suburb",
                # "State",
                # "Postcode",
                # "School Sector",
                # "School Type",
                # "Campus Type",
                # "Rolled Reporting Description",
                "School URL",
                "Governing Body",
                "Governing Body URL",
                "Year Range",
                # "Geolocation",
                "ICSEA",
                "ICSEA Percentile",
                "Bottom SEA Quarter (%)",
                "Lower Middle SEA Quarter (%)",
                "Upper Middle SEA Quarter (%)",
                "Top SEA Quarter (%)",
                "Teaching Staff",
                "Full Time Equivalent Teaching Staff",
                "Non-Teaching Staff",
                "Full Time Equivalent Non-Teaching Staff",
                "Total Enrolments",
                "Girls Enrolments",
                "Boys Enrolments",
                "Full Time Equivalent Enrolments",
                "Indigenous Enrolments (%)",
                "Language Background Other Than English - Yes (%)",
                "Language Background Other Than English - No (%)",
                "Language Background Other Than English - Not Stated (%)",
            ]
        
        self.dfl_summary = self.df_schools[school_cols].set_index("ACARA SML ID")
        self.dfa_summary = self.df_acara[acara_cols].set_index("ACARA SML ID")

        self.df_all = pd.merge(self.df_schools_all[school_cols].set_index("ACARA SML ID"), 
                               self.df_acara_all[acara_cols].set_index("ACARA SML ID"), 
                               left_index=True, 
                               right_index=True)
        
        
        self.df = pd.merge(self.dfl_summary, self.dfa_summary, left_index=True, right_index=True)
        #self.df = self.dfall[self.dfall['State'] == self.City.state]
        
        type_cmap = {"Combined":"institution","Primary":"child","Secondary":"group","Special":"wheelchair"}
        self.df['icons'] = self.df['School Type'].map(type_cmap)
        
        self.df[['Latitude','Longitude']] = self.df[['Latitude','Longitude']].astype("float32")
        
        m = self.df["School Sector"] == "Government"
        self.df_private_schools = self.df[~m]
        self.df_public_schools = self.df[m]

        mprimary = self.df['School Type'] == "Primary"
        self.df_primary = self.df[mprimary]
        msecondary = self.df['School Type'] == "Secondary"
        self.df_secondary = self.df[msecondary]
        mspecial = self.df['School Type'] == "Primary"
        self.df_special = self.df[mspecial]
        mcombined = self.df['School Type'] == "Combined"
        self.df_combined = self.df[mcombined]
        
    def get_schools_within_latlon_radius(self, radius=20000):
        lat = self.City.lat
        lon = self.City.lon
        rs = calcs.distance(self.df["Latitude"].to_numpy(), self.df["Longitude"].to_numpy(), lat, lon)
        m = rs < radius
        return self.df[m]

    def calc_closest_schools(self, lat, longt, closestN=5):
        want_cols = [
            "School Name",
            "Suburb",
            "Distance",
            "School Sector",
            "School Type",
            "ICSEA Percentile",
            "Longitude",
            "Latitude",
        ]

        schools_public = self.df_public.copy()
        schools_private = self.df_private.copy()

        schools_public["Distance"] = distance(
            lat,
            longt,
            self.df_public["Latitude"].values,
            self.df_public["Longitude"].values,
        )

        schools_private["Distance"] = distance(
            lat,
            longt,
            self.df_private["Latitude"].values,
            self.df_private["Longitude"].values,
        )

        schools_public = schools_public.sort_values("Distance")[want_cols].head(closestN)
        schools_private = schools_private.sort_values("Distance")[want_cols].head(closestN)

        return schools_public, schools_private

