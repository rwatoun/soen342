import textwrap
from pathlib import Path

import pytest

from EURailNetwork.loader import read_raw_csv, build_network_from_df
from EURailNetwork.registries import RailNetwork 