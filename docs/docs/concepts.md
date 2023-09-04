# Statistical Areas

When working with Australian regions, there is a well defined standards set by the Australian Statistical Geography Standard. It is broadly based on the concep of a "functional area". These functional areas are defined as the area which people commut or travel to access services. These can range from rural towns and it's hinterland, a regional city, an urban commercial zone or a major city. 

In `wombat`, these areas are handled by `wombat.Boundary` and interact with various government datasets pertaining to this hierarchy. 

Much of the following is detailed at the [Australian Bureau of Statistics](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/latest-release#overview). We highlight here the main points relevant to understanding their handling in `wombat`.

## ABS Defined Areas

!!! note

    The following section is lifted from the [ABS website](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/latest-release#overview) and reproduced here for convenience. 


The Main Structure is developed by the ABS and is used to release and analyse a broad range of social, demographic and economic statistics. It is a nested hierarchy of geographies, and each level directly aggregates to the next level, these are as follows:

* Mesh Blocks (MBs) are the smallest geographic areas defined by the ABS and form the building blocks for the larger regions of the ASGS. Most Mesh Blocks contain 30 to 60 dwellings.
* Statistical Areas Level 1 (SA1s) are designed to maximise the geographic detail available for Census of Population and Housing data while maintaining confidentiality. Most SA1s have a population of between 200 to 800 people.
* Statistical Areas Level 2 (SA2s) are medium-sized general purpose areas built to represent communities that interact together socially and economically. Most SA2s have a population range of 3,000 to 25,000 people.
* Statistical Areas Level 3 (SA3s) are designed for the output of regional data and most have populations between 30,000 and 130,000 people.
* Statistical Areas Level 4 (SA4s) are designed for the output of a variety of regional data, and represent labour markets and the functional area of Australian capital cities. Most SA4s have a population of over 100,000 people.
* States and Territories (S/T) are a cartographic representation of legally designated state and territory boundaries.
* Australia (AUS) is the largest region in the ASGS and represents the geographic extent of Australia.

### Indigenous Structures

The Indigenous Structure enables the publication and analysis of statistics for the Aboriginal and Torres Strait Islander population of Australia. 

* Indigenous Locations (ILOCs) represent small Aboriginal and Torres Strait Islander communities (urban and rural) with a minimum population of about 90 people.
* Indigenous Areas (IAREs) are medium sized geographical areas designed to facilitate the release of more detailed statistics for Aboriginal and Torres Strait Islander people.
* Indigenous Regions (IREGs) are large geographical areas based on historical boundaries. The larger population of Indigenous Regions enables highly detailed analysis.

### Urban Centres and Localities, and Section of State Structure

Urban Centres and Localities and Section of State represent areas of concentrated urban development. 

* Urban Centres and Localities (UCLs) are aggregations of SA1s which meet population density criteria or contain other urban infrastructure. As populations and urban areas change, these UCLs are also designed to change, and areas can come into or out of the classification. This ensures meaningful data is available for urban areas and there are accurate comparisons over time.
* Section of State (SOS) groups the UCLs into classes of urban areas based on population size. SOS does not explicitly define rural Australia, however any population not contained in a UCL is considered to be rural. 
* Section of State Range (SOSR) provides a more detailed classification than SOS. This enables statistical comparison of differently sized urban centres and rural areas.

### Remoteness Structure

Remoteness Areas divide Australia and the states and territories into 5 classes of remoteness on the basis of their relative access to services. Remoteness Areas are based on the Accessibility/Remoteness Index of Australia Plus (ARIA+), produced by the Hugo Centre for Population and Migration Studies.

### Greater Capital City Statistical Area Structure

Greater Capital City Statistical Areas (GCCSAs) represent the functional area of each of the eight state and territory capital cities.

### Significant Urban Area Structure

Significant Urban Areas (SUAs) represent individual Urban Centres or clusters of related Urban Centres with a core urban population of over 10,000 people.
Non ABS Structures

### The Non ABS Structures consist of eight geographies:

* Local Government Areas are an ABS Mesh Block representation of gazetted Local Government boundaries as defined by each state and territory.
* State Electoral Divisions are an ABS Mesh Block approximation of state electoral districts.
* Commonwealth Electoral Divisions are an ABS Mesh Block approximation of the Australian Electoral Commission (AEC) federal electoral division boundaries.
* Postal Areas are an ABS Mesh Block approximation of a general definition of postcodes.
* Tourism Regions are an ABS SA2 approximation of tourism regions as provided by Tourism Research Australia.
* Australian Drainage Divisions are an ABS Mesh Block approximation of drainage divisions as provided through Australian Hydrological Geospatial Fabric.
* Suburbs and Localities (formerly State Suburbs) are an ABS Mesh Block approximation of gazetted localities.
* Destination Zones are co-designed with state and territory transport authorities for the analysis of Place of Work Census of Population and Housing data, commuting patterns and the development of transport policy.

<figure markdown>
  ![Australian Statistical Geographic Areas](/img/concepts/ASGS_Diagram_2021.png)
  <figcaption>Various ABS and Non ABS Structures, their component regions and how they interrelate. Australian Statistical Geography Standard <br> Source:
<a href="https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/latest-release#overview">ASGS</a></figcaption>
</figure>

There is also additional information and nice visuals explaining how changes are handled at the [ABS website here](https://www.abs.gov.au/AUSSTATS/abs@.nsf/Lookup/1270.0.55.001Main+Features10018July%202016?OpenDocument).


## Implementation In Wombat
 
The structure of hierarchical statistical areas with multiple nestings shown in the diagram above, includingthe layers of metadata lends itself well to a [network graph structure](https://en.wikipedia.org/wiki/Network_theory). Graphs are very flexbile structures that can capture inbound and outbound relationship information and enable fast lookups for queries of interest.

`wombat` adopts the widely used Python library, `networkx` ([link](https://networkx.org/)), to construct a graph of the full hierachy of geometries, including non-ABS and indigenous structures. Each of these areas reflect `levels` in the hierarchy which are an attribute of each node with outbound edges to it's parent. The levels in `wombat` are coded as follows: 

![img](/img/boundary/ASGS_Diagram_2021_wombat.png)

!!! note 

    There is a [convenient API available via the ASGS](https://asgs.linked.fsdf.org.au/dataset/asgsed3/collections), but for our bulk analyses, such as that in `wombat`, we require rapid and immediate access to all levels of the hierarchy without incumberances on I/O performance. It is for that reason a graph structure has been implemented.

More details on how to access the data attached to these areas can be found in [Chapter 1 of the Getting Started section on Boundaries](/Boundaries/).