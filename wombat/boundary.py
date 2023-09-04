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
from pyvis.network import Network as pyvisNetwork
import pandas as pd

def has_parent_with_label(G, node, parent_label):
    """Check if node has any parent (up to the root) with the specified label.
    
    Args:
        G(networkx.Graph): The graph to search for nodes.
        node: Node to start from.
        parent_label (any type): The label of the parent to find.
        
    Returns:
        bool: True if any parent with the specified label is found, False otherwise."""
    
    for parent in G.predecessors(node):
        if parent_label in G.nodes[parent]['label']: # == parent_label:
            return True
        elif has_parent_with_label(G, parent, parent_label):  # Recursive call
            return True
    return False

def get_parents_with_label_traverse(G, level, parent_label):
    """Get nodes by level and parent label.
    
    Args:
        G (networkx.Graph): The graph to search for nodes.
        level (int): The level of nodes to retrieve.
        parent_label (any type): The label of the parent node.
    
    Returns:
        list: A list of nodes that belong to the specified level and have parent with the specified label.
    """
    
    matched_nodes = []
    for node in G.nodes:
        # Check if the node is at the given level
        if G.nodes[node]['level'] == level:
            if has_parent_with_label(G, node, parent_label):
                matched_nodes.append(node)
    return matched_nodes

def get_nodes_by_level_and_label(G, level, label):
    """Get nodes by level and parent label.
    
    Args:
        G (networkx.Graph): The graph to search for nodes.
        level (int): The level of nodes to retrieve.
        label (any type): The label of the node.
    
    Returns:
        list: A list of nodes that belong to the specified level and with the specified label.
    """
    
    matched_nodes = []
    for node in G.nodes:
        # Check if the node is at the given level
        if G.nodes[node]['level'] == level and label in G.nodes[node]['label']:
            matched_nodes.append(node)
    return matched_nodes

def get_children_with_level(G, node, child_level):
    """Get all children (successors) of a node at the given level.
    
    Args:
        G(networkx.Graph): The graph to search for nodes.
        node: Node to start from.
        child_level string: The level name of the child node.
        
    Returns:
        list: A list of children nodes with the specified level name.
    """
    
    children = []
    for successor in G.successors(node):
        if G.nodes[successor]['level'] == child_level:
            children.append(successor)
            continue
        else:
            children += get_children_with_level(G, successor, child_level)

    return children

def get_children_with_label(G, node, child_label):
    """Get all children (successors) of a node at the given level.
    
    Args:
        G(networkx.Graph): The graph to search for nodes.
        node: Node to start from.
        child_label string: The level name of the child node.
        
    Returns:
        list: A list of children nodes with the specified level name.
    """
    
    children = []
    for successor in G.successors(node):
        if G.nodes[successor]['label'] == child_label:
            children.append(successor)
            continue
        else:
            children += get_children_with_level(G, successor, child_label)

    return children


def get_parents_with_label(G, level, parent_label,traverse=False):
    """Get nodes by level and parent label.
    
    Args:
        G (networkx.Graph): The graph to search for nodes.
        level (int): The level of nodes to retrieve.
        parent_label (any type): The label of the parent node.
    
    Returns:
        list: A list of nodes that belong to the specified level and have the specified parent node.
    """
    
    matched_nodes = []
    for node in G.nodes:
        # Check if the node is at the given level
        if G.nodes[node]['level'] == level:
            # Check all predecessors (parents) of the node
            parents = G.predecessors(node)
            # Have to think more about how to search back up the tree
            # if traverse:
            #    parents_generator = bfs(G, node_id, depth, 'predecessors')
            #   parents = [parent for parent in parents_generator]
            for parent in parents:
                # If the parent's label matches, add the node to the list
                if parent_label in G.nodes[parent]['label']: # == parent_label:
                    matched_nodes.append(node)
                    break  # we've found a valid parent node so no need to check others
    return matched_nodes

def get_parents_with_level(G, level, parent_level):
    """Get nodes by level and parent label.
    
    Args:
        G (networkx.Graph): The graph to search for nodes.
        level (int): The level of nodes to retrieve.
        parent_label (any type): The label of the parent node.
    
    Returns:
        list: A list of nodes that belong to the specified level and have the specified parent node.
    """
    
    matched_nodes = []
    for node in G.nodes:
        # Check if the node is at the given level
        if G.nodes[node]['level'] == level:
            # Check all predecessors (parents) of the node
            parents = G.predecessors(node)
            # Have to think more about how to search back up the tree
            # if traverse:
            #parents = bfs(G, node, depth, 'predecessors')
            #   parents = [parent for parent in parents_generator]
            for parent in parents:
                # If the parent's label matches, add the node to the list
                if parent_level == G.nodes[parent]['level']: # == parent_label:
                    matched_nodes.append(node)
                    break  # we've found a valid parent node so no need to check others
    return matched_nodes

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
            if target_label in node[1]['label']: # == target_label:
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


def get_subnetwork(G, node, depth,remove_geometry=False):
    """Get the subnetwork of a given node in a graph up to a certain depth.
    
    Args:
        G (networkx.Graph): The input graph.
        node: The node from which to start the subnetwork.
        depth (int): The maximum depth of the subnetwork.
    
    Returns:
        networkx.Graph: The subnetwork of the given node up to the specified depth.
    """
    node_id = str(node.index[0])
    sub_G = nx.ego_graph(G, node_id, radius=depth)
    if remove_geometry:
        for nodei in sub_G.nodes:
            if "geometry" in sub_G.nodes[nodei]:
                del sub_G.nodes[nodei]['geometry']
    return sub_G

def build_index(G,index_type):
    index = {}
    for node in G.nodes:
        idx = G.nodes[node].get(index_type)
        if idx not in index:
            index[idx] = []
        index[idx].append(node)
    return index
    
def count_nodes_in_levels(level_index):
    """Counts nodes at each level in level_index.

    Args:
        level_index (dict): Dictionary where keys are levels and values are lists of nodes.

    Returns:
        dict: A dictionary where keys are levels and values are the count of nodes at that level.
    """
    level_counts = {level: len(nodes) for level, nodes in level_index.items()}
    return level_counts
class GeoHierarchy:
    def __init__(self, boundary_path,fname_save = "2023_AUS_Boundaries"):
        self.boundary_path = boundary_path
        self.fname_save = fname_save
        self.fileout = os.path.join(boundary_path,"%s.gpickle"%fname_save)
        self.fileout_gexf = os.path.join(boundary_path,"%s.gexf"%fname_save)
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
            
    def get_nodes(self,level=None, label=None):
        if level is not None:
            nodes_level = set(self.level_index.get(level, []))
        if label is not None:
            nodes_label = set(self.label_index.get(label, []))
        
        if level is not None and label is not None:
            return list(nodes_level & nodes_label)
        if level is None and label is not None:
            return list(nodes_label)
        if level is not None and label is None:
            return list(nodes_level)
   
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
                
    def save(self,gpickle=True,gexf=False):
        if gpickle:
            nx.write_gpickle(self.G,self.fileout)
            
        if gexf:
            outG = self.G.copy()
            for nodei in outG.nodes:
                if "geometry" in outG.nodes[nodei]:
                    del outG.nodes[nodei]['geometry']
            nx.write_gexf(outG, "%s.gexf"%self.fileout_gexf)
        
    def load(self):
        if os.path.exists(self.fileout):
            self.G = nx.read_gpickle(self.fileout)
            # Then you can use this index for quick lookups:
            self.level_index = build_index(self.G,'level')
            #nodes_at_level_x = level_index.get(x)
            self.label_index = build_index(self.G,'label')
            self.level_counts = count_nodes_in_levels(self.level_index)
            
    def print_tree(self,node,depth=1,children=True,parents=False,cousins=False):
        nodex = self.G.nodes[node.index]
        print_tree(self.G,nodex,depth,children=children,parents=parents,cousins=cousins)
    
    def get_parents_with_label(self,label,parent_label):
        return get_parents_with_label(self.G, label, parent_label)
    
    def get_parents_with_level(self,label,parent_level):
        return get_parents_with_level(self.G, label, parent_level)
                     
    def get_subnetwork(self, node, depth,remove_geometry=False):
        return get_subnetwork(self.G,node,depth,remove_geometry)
    
    def get_parents(self,node,depth=1):
        parents = bfs(self.G, node[0], depth=depth, direction='predecessors')
        return list(parents) #[self.G.nodes[n] for n in parents]
    
    def get_children(self,node,depth=1):
        children =  bfs(self.G, node[0], depth=depth, direction='successors')
        return list(children) #[self.G.nodes[c] for c in children]
    
    def get_children_with_level(self,node,child_level_label):
        children_at_level = get_children_with_level(self.G,node,child_level_label)
        return list(children_at_level) #[self.G.nodes[c]['id'] for c in children_at_level]

    def search_nodes(self, level, parent_label=None): #, traverse=False):
        if parent_label is not None:
            node_ids = get_parents_with_label_traverse(self.G, level, parent_label)
            assert len(node_ids) > 0, print("No areas were found, please fix search.")
        else:
            node_ids = self.level_index[level]
        return node_ids #node_to_gdf(self.G,node_ids)
    
    def query(self, string_query, belonging_to=None, as_gdf=True):
        if belonging_to is not None:
            node_ids = self.search_nodes(level=string_query,parent_label=belonging_to)
        else:
            node_ids = self.get_nodes(level=string_query)
        assert len(node_ids)>0, print("No objects found (node_ids)!!")
        if as_gdf:
            return node_to_gdf(self.G,node_ids)
        else:
            return node_ids

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
        
class BoundaryJSON(Datasets):
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

def node_to_gdf(G,node_ids,level=None,label=None):
    #return gpd.GeoDataFrame(nodes,crs="EPSG:4326").sort_values(['level','label'])
    gdf = gpd.GeoDataFrame([G.nodes[c] for c in node_ids],crs="EPSG:4326")
    gdf.index = node_ids
    gdf = gdf.sort_values(['level','label'])
    gdf = gdf[~gdf['geometry'].isna()]
    if level is not None:
        gdf = gdf[gdf['level'] == level]
    if label is not None:
        gdf = gdf[gdf['label'] == label]
    return gdf


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
         
        info = {'ADD':"Australian Drainage Divisions are an ABS Mesh Block approximation of drainage divisions as provided through Australian Hydrological Geospatial Fabric.",
                'ALL':"None",
                'AUS':"Australia (AUS) is the largest region in the ASGS and represents the geographic extent of Australia.",
                'CED':"Commonwealth Electoral Divisions are an ABS Mesh Block approximation of the Australian Electoral Commission (AEC) federal electoral division boundaries.",
                'DZN':"Destination Zones are co-designed with state and territory transport authorities for the analysis of Place of Work Census of Population and Housing data, commuting patterns and the development of transport policy.",
                'GCCSA':"Greater Capital City Statistical Areas (GCCSAs) represent the functional area of each of the eight state and territory capital cities.",
                'IARE':"Indigenous Areas (IAREs) are medium sized geographical areas designed to facilitate the release of more detailed statistics for Aboriginal and Torres Strait Islander people.",
                'ILOC':"Indigenous Locations (ILOCs) represent small Aboriginal and Torres Strait Islander communities (urban and rural) with a minimum population of about 90 people.",
                'IREG':"Indigenous Regions (IREGs) are large geographical areas based on historical boundaries. The larger population of Indigenous Regions enables highly detailed analysis.",
                'LGA':"Local Government Areas are an ABS Mesh Block representation of gazetted Local Government boundaries as defined by each state and territory.",
                'MB':"Mesh Blocks (MBs) are the smallest geographic areas defined by the ABS and form the building blocks for the larger regions of the ASGS. Most Mesh Blocks contain 30 to 60 dwellings.",
                'POA':"Postal Areas are an ABS Mesh Block approximation of a general definition of postcodes.",
                'SA1':"Statistical Areas Level 1 (SA1s) are designed to maximise the geographic detail available for Census of Population and Housing data while maintaining confidentiality. Most SA1s have a population of between 200 to 800 people.",
                'SA2':"Statistical Areas Level 2 (SA2s) are medium-sized general purpose areas built to represent communities that interact together socially and economically. Most SA2s have a population range of 3,000 to 25,000 people.",
                'SA3':"Statistical Areas Level 3 (SA3s) are designed for the output of regional data and most have populations between 30,000 and 130,000 people.",
                'SA4':"Statistical Areas Level 4 (SA4s) are designed for the output of a variety of regional data, and represent labour markets and the functional area of Australian capital cities. Most SA4s have a population of over 100,000 people.",
                'SAL':"Suburbs and Localities (formerly State Suburbs) are an ABS Mesh Block approximation of gazetted localities.",
                'SED':"State Electoral Divisions are an ABS Mesh Block approximation of state electoral districts.",
                'SOS':"Section of State (SOS) groups the UCLs into classes of urban areas based on population size. SOS does not explicitly define rural Australia, however any population not contained in a UCL is considered to be rural.",
                'SOSR':"Section of State Range (SOSR) provides a more detailed classification than SOS. This enables statistical comparison of differently sized urban centres and rural areas.",
                'STATE':"States and Territories (S/T) are a cartographic representation of legally designated state and territory boundaries.",
                'SUA':"Significant Urban Areas (SUAs) represent individual Urban Centres or clusters of related Urban Centres with a core urban population of over 10,000 people. Non ABS Structures",
                'TR':"Tourism Regions are an ABS SA2 approximation of tourism regions as provided by Tourism Research Australia.",
                "UCL":"Urban Centres and Localities (UCLs) are aggregations of SA1s which meet population density criteria or contain other urban infrastructure. As populations and urban areas change, these UCLs are also designed to change, and areas can come into or out of the classification. This ensures meaningful data is available for urban areas and there are accurate comparisons over time."
                }      
        #"Remoteness Areas divide Australia and the states and territories into 5 classes of remoteness on the basis of their relative access to services. Remoteness Areas are based on the Accessibility/Remoteness Index of Australia Plus (ARIA+), produced by the Hugo Centre for Population and Migration Studies.",                           
        self.info = pd.Series(info) #,columns=['Code','Description'])

    def get_boundaries_down(self,node,level=None,label=None):
        node_ids = self.graph.get_children(node,depth=1)
        gdf = node_to_gdf(self.graph.G,node_ids,level=level,label=label)
        return gdf
    
    def get_boundaries_up(self,node,level=None,label=None):
        node_ids = self.graph.get_parents(node,depth=1)
        return node_to_gdf(self.graph.G,node_ids)
    
    def get_boundary(self,level,label,belonging_to=None,as_gdf=True):
        if belonging_to is not None:
            return self.graph.search_nodes(level=level,parent_label=belonging_to)
        node_ids = self.graph.get_nodes(level=level,label=label)
        if as_gdf:
            return node_to_gdf(self.graph.G,node_ids)
        else:
            return node_ids
        
    def get_country(self,as_gdf=True):
        return self.graph.query("AUS", None, as_gdf)
    
    def get_state(self,state,as_gdf=True):
        node_ids = self.graph.get_nodes(label=state,level="STATE")
        return node_to_gdf(self.graph.G,node_ids)
        
    def get_states(self,as_gdf=True):
        return self.graph.query("STATE", None, as_gdf)
    
    def get_indigenous_regions(self,parent_label=None,as_gdf=True):
        return self.graph.query("IREG", parent_label, as_gdf)
    
    def get_indigenous_areas(self,parent_label=None,as_gdf=True):
        return self.graph.query("IREA", parent_label, as_gdf)
    
    def get_lgas(self,parent_label=None,as_gdf=True):
        return self.graph.query("LGA", parent_label, as_gdf)
    
    def get_electoral_divisions(self,parent_label=None,as_gdf=True):
        return self.graph.query("CED", parent_label, as_gdf)
    
    def get_meshblocks(self,parent_label=None,as_gdf=True):
        return self.graph.query("MB", parent_label, as_gdf)
    
    def get_gccs(self,as_gdf=True):
        node_ids = get_nodes_by_level(self.graph.G,"GCCSA")
        if as_gdf:
            gdf = node_to_gdf(self.graph.G,node_ids)
            gdf = gdf[~gdf['label'].str.contains("Rest of")]
            gdf = gdf[~gdf['label'].str.contains("Other")]
            return gdf
        else:
            return node_ids
    
    def get_gcc(self,city):
        #node_ids = get_nodes_by_level_and_label(self.graph.G,level="GCCSA",label=city)
       # node_ids = self.graph.get_nodes(level="GGCSA",label=city)
        #return self.graph.query("SA3", city, as_gdf=True)
        return self.get_sa3(belonging_to=city)
        
        #gdf = node_to_gdf(node_ids)
        #gdf = gdf[~gdf['label'].str.contains("Rest of")]
        #return gdf
    
    def get_sa1(self,belonging_to=None,as_gdf=True):
        return self.graph.query("SA1", belonging_to, as_gdf)
    
    def get_sa2(self,belonging_to=None,as_gdf=True):
        return self.graph.query("SA2", belonging_to, as_gdf)
    
    def get_sa3(self,belonging_to=None,as_gdf=True):
        return self.graph.query("SA3", belonging_to, as_gdf)
    
    def get_sa4(self,belonging_to=None,as_gdf=True):
        return self.graph.query("SA4", belonging_to, as_gdf)
    
    def get_tr(self,belonging_to=None,as_gdf=True):
        return self.graph.query("TR", belonging_to, as_gdf)
    
    def get_sua(self,belonging_to=None,as_gdf=True):
        return self.graph.query("SUA", belonging_to, as_gdf)
    
    def get_full_df(self,column_name=None,filter_value=None):
        list_nodes = list(self.graph.G.nodes(data=True))
        node_ids = [n[0] for n in list_nodes]
        node_meta = [n[1] for n in list_nodes]
        df = gpd.GeoDataFrame(node_meta,index=node_ids,crs='EPSG:4326')
        if column_name is not None and filter_value is not None:
            gdf = gdf[gdf[column_name] == filter_value]
        return gdf

    #def set_radius(self,radius=10):
    #    self.gdf = polygons_within_radius(self.gdf,self.City.lat,self.City.lon,radius)
    
    def get_parents_with_level_recursive(self, node, level):
        return get_parents_with_level(node,parent_level=level)
    
    def get_parents_with_label_recursive(self, node, label):
        return get_parents_with_label(node,parent_label=label)
    
    def get_children_with_level_recursive(self, node, level):
        node_ids = self.graph.get_children_with_level(node,child_level=level)
        return node_to_gdf(self.graph.G,node_ids)
    
    def get_children_with_label_recursive(self,node, label):
        node_ids = self.graph.get_children_with_label(node,child_label=label)
        return node_to_gdf(self.graph.G,node_ids)
    
    def pyvis(self,subG):
        nt = pyvisNetwork('500px', '100%')
        nt.from_nx(subG)
        return nt
                     
    def get_subnetwork(self, node, depth,remove_geometry=True):
        return self.graph.get_subnetwork(node,depth,remove_geometry)
    
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