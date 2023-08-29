"""Top-level package for wombat."""

__author__ = "Brendan Griffen"
__version__ = "0.1.0"
__email__ = "@brendangriffen"

#from wombat.urbanity import Urbanity as Urbanity
from wombat.boundary import Boundary as Boundary
from wombat.wombat import Wombat as Wombat
from wombat.buildings import Buildings as Buildings
from wombat.visualise import Viz as Viz
from wombat.datasets import Datasets as Datasets
from wombat.elevation import Elevation as Elevation
from wombat.datasets import caplatlon as caplatlon
from wombat.datasets import addresses as addresses
from wombat.datasets import capitals as capitals
import os
from wombat.datasets import City as City
import wombat.elevation as elevation

def _in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    import sys

    if "google.colab" in sys.modules:
        return True
    else:
        return False

def _use_folium():
    """Whether to use the folium or ipyleaflet plotting backend."""
    if os.environ.get("USE_MKDOCS") is not None:
        return True
    else:
        return False
