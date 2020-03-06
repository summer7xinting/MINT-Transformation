#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO: no gdal installed :/
from .readers.read_func import ReadFunc
from .readers.dcat_read_func import DcatReadFunc
from .readers.dcat_read_no_repr import DcatReadNoReprFunc
# from .trans_unit_func import UnitTransFunc
from .writers.write_func import CSVWriteFunc
from .graph_str2str_func import GraphStr2StrFunc
from .merge_func import MergeFunc
from .trans_cropping_func import CroppingTransFunc
from .aggregations.variable_aggregation_func import VariableAggregationFunc
# from .topoflow.write_topoflow4_climate_func import Topoflow4ClimateWriteFunc, Topoflow4ClimateWritePerMonthFunc
# from .topoflow.write_topoflow4_soil_func import Topoflow4SoilWriteFunc
# from .topoflow.nc2geotiff import NC2GeoTiff
from .dcat_write_func import DcatWriteFunc
# from .calendar_change_func import CalendarChangeFunc
