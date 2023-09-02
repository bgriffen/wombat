import geopandas as gpd
from geopandas.tools import sjoin
from shapely.geometry import Point,Polygon
import wombat.helper as helper
import os
from wombat.datasets import Datasets,City
import glob
import fiona
import networkx as nx
import numpy as np
from collections import deque

def bfs(graph, start_node, depth, direction='successors'):
    queue = deque([(start_node, 0)])
    while queue:
        node, level = queue.popleft()
        
        # We skip when level = 0 (yielding only successors or predecessors)
        if level > 0:
            yield node
            
        if level > depth: 
            return

        neighbors = getattr(graph, direction)(node)
        for neighbor in neighbors:
            queue.append((neighbor, level + 1))


def get_cousins(G, node):
    """Returns a list of cousins of a given node."""
    
    # get parents of the given node
    parents = G.predecessors(node)
    
    # get siblings including the node itself
    siblings = set()
    for parent in parents:
        children_generator = G.successors(parent)
        siblings.update(children_generator)
        
    # remove the node from the siblings set to get its cousins
    siblings.remove(node)
    return siblings

def print_tree(G, node, depth, parents=False, children=True, cousins=False):
    """
    Prints the parents, children and neighbors of a node.
    
    Args:
        G (networkx.Graph): The graph representing the tree.
        node: The target node.
        depth: The max depth to scan parents/children.
    
    
    Returns:
        None
    """
    node_id = node[0]
    node_info = node[1]
    def print_nodes(nodes_to_print, title):
        print(title)
        for n in nodes_to_print:
            node_data = G.nodes[n]
            print(node_data)
            if np.isfinite(node_data['area_sqkm']):
                area = node_data['area_sqkm']
            else:
                area = 0
            str_out = u"> %s (%ikm2)" % (node_data['label'], area)
            print(str_out.ljust(8))
    
       
    # get parents
    if parents:
        parents_generator = bfs(G, node_id, depth, 'predecessors')
        parents = [parent for parent in parents_generator]
        print(node_info)
        print_nodes(parents, "Parents of {}:".format(node_info['label']))

    # get children
    if children:
        children_generator = bfs(G, node_id, depth, 'successors')
        children = [child for child in children_generator]
        print_nodes(children, "\nChildren of {}:".format(node_info['label']))
    
    # get neighbors
    if cousins:
        cousins = get_cousins(G, node_id)
        print_nodes(cousins, "\nCousins of {}:".format(node))

def get_node_by_label(G, target_label):
    """Returns the first node in the graph `G` that has a label matching `target_label`.
    
    Args:
        G (networkx.Graph): The graph to search for nodes.
        target_label (str): The label to search for.
    
    Returns:
        node: The first node found with a matching label, or None if no such node is found.
    """
    
    for node in G.nodes(data=True):
        if 'label' in node[1]:  # node[1] is where data is stored in a Node Tuple
            if node[1]['label'] == target_label:
                return node
    return None

def get_nodes_by_level(G, level):
    """Get nodes by level.
    
    Args:
        G (networkx.Graph): The graph to search for nodes.
        level (int): The level of nodes to retrieve.
    
    Returns:
        list: A list of nodes that belong to the specified level.
    """
    
    matched_nodes = []
    for node in G.nodes:
        if G.nodes[node]['level'] == level:
            matched_nodes.append(node)
    return matched_nodes

def get_subnetwork(G, node, depth):
    """Get the subnetwork of a given node in a graph up to a certain depth.
    
    Args:
        G (networkx.Graph): The input graph.
        node: The node from which to start the subnetwork.
        depth (int): The maximum depth of the subnetwork.
    
    Returns:
        networkx.Graph: The subnetwork of the given node up to the specified depth.
    """
    node_id = node[0]
    sub_G = nx.ego_graph(G, node_id, radius=depth)
    return sub_G

class GeoHierarchy:
    
    def __init__(self, boundary_path,fname_save = "2023_AUS_Boundaries"):
        self.boundary_path = boundary_path
        self.fname_save = fname_save
        self.fileout = os.path.join(boundary_path,"%s.gpickle"%fname_save)
        
        self.G = nx.DiGraph()
        
        self.gpkg_files = ['ASGS_2021_Main_Structure_GDA2020',
                           'ASGS_Ed3_Non_ABS_Structures_GDA2020_updated_2023',
                           'ASGS_2021_SUA_UCL_SOS_SOSR_GPKG_GDA2020',
                           'ASGS_Ed3_2021_Indigenous_Structure_GDA2020']
        
        # initialise root boundary node if graph file does not exist
        if not os.path.exists(self.fileout):
            full_fpath = os.path.join(self.boundary_path,'ASGS_2021_Main_Structure_GDA2020')+".gpkg"
            df = gpd.read_file(full_fpath,layer='AUS_2021_AUST_GDA2020')
            aus_row = df.iloc[0]
            geometry = aus_row['geometry']
            area_sqkm = aus_row['AREA_ALBERS_SQKM']
            uri = aus_row['ASGS_LOCI_URI_2021']
            label = aus_row['AUS_NAME_2021']
            node_id = aus_row['AUS_CODE_2021']
            self.G.add_node(node_id,
                                label=label,
                                uri=uri,
                                geometry=geometry,
                                area_sqkm=area_sqkm,
                                level='AUS')
            
    def construct_full_hierarchy(self):
        for fname in self.gpkg_files:
            self.index = None
            if "Main" in fname:
                self.index = [
                    #{'layer':'AUS_2021_AUST_GDA2020',  'node_col':'AUS_CODE_2021',  'parent_col':'root'},
                    {'layer':'STE_2021_AUST_GDA2020',  'node_col':'STATE_CODE_2021','parent_col':'AUS_CODE_2021'},
                    {'layer':'GCCSA_2021_AUST_GDA2020','node_col':'GCCSA_CODE_2021',  'parent_col':'STATE_CODE_2021'},
                    {'layer':'SA4_2021_AUST_GDA2020',  'node_col':'SA4_CODE_2021',  'parent_col':'STATE_CODE_2021'},
                    {'layer':'SA4_2021_AUST_GDA2020',  'node_col':'SA4_CODE_2021',  'parent_col':'GCCSA_CODE_2021'},
                    {'layer':'SA3_2021_AUST_GDA2020',  'node_col':'SA3_CODE_2021',  'parent_col':'SA4_CODE_2021'},
                    {'layer':'SA2_2021_AUST_GDA2020',  'node_col':'SA2_CODE_2021',  'parent_col':'SA3_CODE_2021'},
                    {'layer':'SA1_2021_AUST_GDA2020',  'node_col':'SA1_CODE_2021',  'parent_col':'SA2_CODE_2021'},
                    {'layer':'MB_2021_AUST_GDA2020',   'node_col':'MB_CODE_2021',   'parent_col':'SA1_CODE_2021'}
                ]
            if "Non_ABS" in fname:
                self.index = [
                    {'layer':'SAL_2021_AUST_GDA2020',  'node_col':'SAL_CODE_2021',  'parent_col':'STATE_CODE_2021'},
                    {'layer':'ADD_2021_AUST_GDA2020',  'node_col':'ADD_CODE_2021',  'parent_col':'AUS_CODE_2021'},
                    {'layer':'TR_2021_AUST_GDA2020',   'node_col':'TR_CODE_2021',   'parent_col':'STATE_CODE_2021'},
                    {'layer':'CED_2021_AUST_GDA2020',  'node_col':'CED_CODE_2021',  'parent_col':'STATE_CODE_2021'},
                    {'layer':'SED_2022_AUST_GDA2020',  'node_col':'SED_CODE_2022',  'parent_col':'STATE_CODE_2021'},
                    {'layer':'DZN_2021_AUST_GDA2020',  'node_col':'DZN_CODE_2021',  'parent_col':'SA2_CODE_2021'},
                    {'layer':'POA_2021_AUST_GDA2020',  'node_col':'POA_CODE_2021',  'parent_col':'AUS_CODE_2021'},
                    {'layer':'LGA_2023_AUST_GDA2020',  'node_col':'LGA_CODE_2023',  'parent_col':'STATE_CODE_2021'}
                ]
            if "Indigenous_Structure" in fname:
                self.index = [
                    {'layer':'IREG_2021_AUST_GDA2020',  'node_col':'IREG_CODE_2021',  'parent_col':'STATE_CODE_2021'},
                    {'layer':'IARE_2021_AUST_GDA2020',  'node_col':'IARE_CODE_2021',  'parent_col':'IREG_CODE_2021'},
                    {'layer':'ILOC_2021_AUST_GDA2020',  'node_col':'ILOC_CODE_2021',  'parent_col':'IARE_CODE_2021'},
                ]
            if "SUA" in fname:
                self.index = [
                    {'layer':'SOS_2021_AUST_GDA2020',  'node_col':'SOS_CODE_2021',  'parent_col':'STATE_CODE_2021'},
                    {'layer':'SOSR_2021_AUST_GDA2020',  'node_col':'SOSR_CODE_2021',  'parent_col':'SOS_CODE_2021'},
                    {'layer':'UCL_2021_AUST_GDA2020',  'node_col':'UCL_CODE_2021',  'parent_col':'SOSR_CODE_2021'},
                    {'layer':'SUA_2021_AUST_GDA2020',  'node_col':'SUA_CODE_2021',  'parent_col':'AUS_CODE_2021'},
                ]       
            self.construct_hierarchy_for_file(fname)
            
    def print_layers(self):
        for fname in self.gpkg_files:
            fpath = os.path.join(self.boundary_path,fname+".gpkg")
            layers = fiona.listlayers(fpath)
            for l in layers:
                print(fpath)
                print(">",l)
                df = gpd.read_file(fpath,layer=l)
                cols = list(df.columns)
                for c in cols:
                    print(" >",c)
                
    def print_layers_specificfile(self,fname):
        fpath = os.path.join(self.boundary_path,fname+".gpkg")
        layers = fiona.listlayers(fpath)
        for l in layers:
            print(fpath)
            print(">",l)
            df = gpd.read_file(fpath,layer=l)
            print(list(df.columns))
            
    def construct_hierarchy_for_file(self,fpath): 
        for idx in self.index:
            layer = idx['layer']
            parent_col = idx['parent_col']
            node_col = idx['node_col']
            full_fpath = os.path.join(self.boundary_path,fpath)+".gpkg"
            print(f"Running: {layer}, assigning {node_col} --> {parent_col}")
            print("Filename:",full_fpath)
            df = gpd.read_file(full_fpath, layer=layer)
            cols = list(df.columns)
            for c in cols:
                print(" >",c)
                
            df = df[df['AUS_CODE_2021'] != "ZZZ"]
            for _, row in df.iterrows():
                geometry = row['geometry']
                area_sqkm = row['AREA_ALBERS_SQKM']
                uri = row['ASGS_LOCI_URI_2021']
                
                level_node = node_col.split("_")[0]
                level_parent = parent_col.split("_")[0]
                
                label = None if node_col in ["SA1_CODE_2021",'MB_CODE_2021','DZN_CODE_2021'] else row[node_col.replace("CODE","NAME")]
                
                parent_node_key = "root" if layer == "AUS_2021_AUST_GDA2020" else (row[parent_col])
                
                if parent_node_key not in self.G.nodes:
                    self.G.add_node(parent_node_key,
                                    label=label,
                                    uri=uri,
                                    geometry=geometry,
                                    area_sqkm=area_sqkm,
                                    level=level_parent)

                current_node_key = row[node_col]

                if current_node_key not in self.G.nodes: 
                    self.G.add_node(current_node_key,
                                    label=label,
                                    uri=uri,
                                    geometry=geometry,
                                    area_sqkm=area_sqkm,
                                    level=level_node)
                    
                self.G.add_edge(parent_node_key, current_node_key)
                
    def save(self):
        nx.write_gpickle(self.G,self.fileout)
        # need to decide if we want to remove geometry
        outG = self.G.copy()
        for nodei in outG.nodes:
            if "geometry" in subG.nodes[nodei]:
                del subG.nodes[nodei]['geometry']
        nx.write_gexf(outG, "%s.gexf"%self.fileout)
        
    def load(self):
        if os.path.exists(self.fileout):
            self.G = nx.read_gpickle(self.fileout)

    def print_tree(self,node,depth=1,children=True,parents=False,cousins=False):
        print_tree(self.G,node,depth,children=children,parents=parents,cousins=cousins)
        
    def get_nodes_by_level(self,level):
        return get_nodes_by_level(self.G,level)
    
    def get_node_by_label(self,label):
        return get_node_by_label(self.G,label)
    
    def get_subnetwork(self, node, depth):
        return get_subnetwork(self.G,node,depth)
    
    def get_parents(self,node,depth=1):
        return bfs(self.G, node[0], depth=depth, direction='successors')
             
    def get_children(self,node,depth=1):
        return bfs(self.G, node[0], depth=depth, direction='predecessors')

def polygons_within_radius(gdf,lat,lon,radius):
    """Find polygons within a given radius of a center point.
    
    Args:
        gdf (GeoDataFrame): A GeoDataFrame containing polygons.
        lat (float): The latitude of the center point.
        lon (float): The longitude of the center point.
        radius (float): The radius in kilometers.
    
    Returns:
        GeoDataFrame: A GeoDataFrame containing polygons that intersect with the buffered center point.
    """
    center_point = gpd.GeoDataFrame(geometry=gpd.points_from_xy([lon],[lat]), crs='EPSG:4326')
    
    # Ensure that GeoJSON is in same CRS as the center point
    gdf = gdf.to_crs(center_point.crs)

    # Buffer center point by 10km radius (assuming the CRS is in degrees, 
    # if it's in meters, adjust the buffer value accordingly)
    center_point.geometry = center_point.geometry.buffer(radius/111.32) # Rough conversion from km to degrees

    # Use spatial join to find polygons that intersect with buffered center point
    polygons_in_radius = sjoin(gdf, center_point, op='intersects')
    return polygons_in_radius 

def load_statistical_area(filename,layer,column_name=None,filter_value=None):
    gdf = gpd.read_file(filename,layer=layer)
    if column_name is not None:
        assert column_name in gdf.columns, print("Only these columns are available:",list(gdf.columns))
        subset_vals = gdf[column_name]
        unique_vals = sorted(list(set(subset_vals)))
        assert filter_value in unique_vals, print("Only these columns are available:",unique_vals)
        return gdf[subset_vals == filter_value]
    return gdf

Australia_BoundingBox = {
    'minx': 112.9519424,
    'miny': -43.7405093,
    'maxx': 153.9933464,
    'maxy': -9.1870234
}
#
Australia_BoundingBox_geom = Polygon([(Australia_BoundingBox['minx'],Australia_BoundingBox['miny']), 
                                      (Australia_BoundingBox['minx'],Australia_BoundingBox['maxy']), 
                                      (Australia_BoundingBox['maxx'],Australia_BoundingBox['maxy']),
                                      (Australia_BoundingBox['maxx'],Australia_BoundingBox['miny'])])

g = gpd.GeoSeries([Australia_BoundingBox_geom],crs="EPSG:4326")

class StatisticalArea:
    def __init__(self,filename,layer):
        self.filename = filename
        self.layer = layer
        # https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files
        
class Boundary(Datasets):
    def __init__(self,dataset_path):
        super().__init__(dataset_path)
        self.dataset_path = dataset_path
        
        self.graph = GeoHierarchy(self.boundary_path)
        self.graph.load()
        
        files = glob.glob(os.path.join(self.boundary_path,"*.gpkg"))
        self.Areas = {}
        for filei in files:
            layers = fiona.listlayers(filei)
            for l in layers:
                self.Areas[l.split("_")[0]] = {'filename':filei,'layer':l}

        self.Australia_BoundingBox_Poly = gpd.GeoDataFrame(geometry=g)

    def set_area(self,statistical_area,column_name=None,filter_value=None):
        """_summary_
        Args:
            statistical_area (str): Statistical Area name
            column_name (str, optional): Column of the statistical area (e.g. "SA_NAME21"). Defaults to None.
            filter_value (str, optional): Value to filter over (e.g. "Greater Brisbane"). Defaults to None.
        """ 
        filename = self.Areas[statistical_area]['filename']
        layer = self.Areas[statistical_area]['layer']
        self.gdf = load_statistical_area(filename,
                                         layer,
                                         column_name=column_name,
                                         filter_value=filter_value)
        self.gdf = self.gdf[~self.gdf['geometry'].isna()]
        if "SA4_NAME_2021" in self.gdf.columns:
            self.sa4s = sorted(list(set(self.gdf['SA4_NAME_2021'])))
        if "SA3_NAME_2021" in self.gdf.columns:
            self.sa3s = sorted(list(set(self.gdf['SA3_NAME_2021'])))
        if "STATE_NAME_2021" in self.gdf.columns:
            self.state = sorted(list(set(self.gdf['STATE_NAME_2021'])))
        if "GCCSA_NAME_2021" in self.gdf.columns:
            self.gccsa = sorted(list(set(self.gdf['GCCSA_NAME_2021'])))

    def load_states_territories(self):
        self.gdf_states_territories = gpd.read_file(self.boundary_path_states_territories,engine='pyogrio')
        
    def set_radius(self,radius=10):
        self.gdf = polygons_within_radius(self.gdf,self.City.lat,self.City.lon,radius)

class OpenStreetMap:
    def __init__(self,dataset_path):
        self.dataset_path = dataset_path
        self.pbf_path = os.path.join(dataset_path,"pbf")
    
    def generate_pbf_per_city(self):
        for city in helper.caplatlon.keys():
            print("Running...",city)
            boundary = Boundary(self.dataset_path)
            boundary.load()
            boundary.set_radius(20)
            boundary.gdf.to_file(os.path.join(self.pbf_path,city.name+".geojson"), driver='GeoJSON',engine='pyogrio')