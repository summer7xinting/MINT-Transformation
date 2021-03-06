#!/usr/bin/env python
# coding: utf-8

# # Jupyter Notebook to Prepare TopoFlow Input Files

# This Jupyter notebook demonstrates how to use a collection of TopoFlow utilities to create required input files for the TopoFlow hydrologic model.  These utilities are included as part of the TopoFlow Python package, in topoflow/utils.
#
# It is recommended to install and use the newer Jupyter Lab environment, which has many improvements over a standard Jupyter notebook environment.  This includes the ability to collapse (and "hide" cells).
#
# This notebook has been written with the assumption that the user has access to the MINT Dropbox folder, and it copies many necessary files from there.
#
# This notebook is for TopoFlow pre-processing (preparation of input files).  A separate notebook will show how TopoFlow output files can be visualized as movies or time series plots.
#
# It is possible to choose Run > Run All Cells.

# # Set up a conda environment with all dependencies

# Before you can run the code in this notebook, you will need to install the TopoFlow 3.6 Python package.
#
# It is recommended to use Python 3.7 (or higher) from an Anaconda distribution and to install TopoFlow 3.6 in a conda environment called "tf36".  In Anaconda is already installed, you can use the following commands on Mac or Linux to install TopoFlow.  This helps to isolate it from the rest of your Python environment to avoid potential package conflicts.

# ```
# % conda update -n base conda
# % conda create --name tf36
# % conda activate tf36
# % conda install netCDF4  (Will be installed with TopoFlow otherwise.)
# % conda install gdal (for some utilities)
# NOTE:  Do not use:  conda install -c conda-forge gdal
#
# Download the TopoFlow 3.6 package from GitHub repo "topoflow36".
# Copy it somewhere. Denote this full path as TF36_DIR.
# e.g. TF36_DIR = /Users/peckhams/Dropbox/TopoFlow_3.6
#
# % cd TF36_DIR
# % pip install -e .   (-e is the editable/developer option)
# % cd
#
# If you would like to run the notebook in jupyterlab, also do this.
# % conda install -c conda-forge jupyterlab
# % conda install -c conda-forge nb_conda_kernels (needed for conda envs)
# % jupyter lab
# ```

# Finally, choose <b>TopoFlow_Getting_Started.ipynb</b> in Jupyter Notebook or Jupyter Lab.
# In Jupyter Lab, choose the kernel:  Python [conda evn:tf36].  Whenever you want to run TopoFlow (or a TopoFlow notebook), you will then need to switch to this "tf36" environment with the command: "conda activate tf36".

# # Define information for a specific basin of interest

# TopoFlow uses a <b>site_prefix</b> for all of the filenames in a data set that pertain to the geographic location (the "site").  These files describe static properties of the location, such as topography and soil.  The default site prefix in this notebook is <b>Baro_Gam_1min</b>.
#
# Topoflow uses a <b>case_prefix</b> for all of the filenames in a data set that describe a particular model scenario (the "case" under consideration).  These files describe things that can change from one model run to the next for the same site.  The default case prefix in this notebook is <b>Test1</b>.  Note that component CFG filenames always start with the case prefix.
#
# By simply changing the information in this next code block, this notebook can generate TopoFlow input files for any river basin in Ethiopia.  However, please heed the <b>Important Warning</b> below.
#
# out_bounds = Geographic bounding box for the chosen river basin<br>
# out_xres_sec = the spatial grid cell xsize to use, in arcseconds<br>
# out_yres_sec = the spatial grid cell ysize to use, in arcseconds<br>

# ## Important Warning !!

# Some of the input grid files generated by this notebook are computed using empirical, power-law estimates, based on a grid of <b>total contributing area</b> (TCA).
#
# For these, it is necessary -- <b>at a minimum</b>  -- to know the values of a few key variables at the basin outlet.  These must be determined from the literature or other data sets.  These variables that are specific to a particular river basin have been collected in the next code block.
#
# If these are not set to reasonable values, the resulting predictions will be meaningless.

# # Set the site_prefix, case_prefix & common info

# In[1]:


site_prefix = "Baro_Gam_1min"
# site_prefix = 'Awash-border_60sec'
# site_prefix = 'Shebelle-Imi_60sec'
# site_prefix = 'Ganale-border_60sec'
# site_prefix = 'Guder_30sec'
# site_prefix = 'Muger_30sec'

# --------------------------------------------------------
# For now, keep these the same for all the river basins
# --------------------------------------------------------
case_prefix = "Test1"
channel_width_power = 0.5
max_sinuosity = 1.3  # [m/m]
min_manning_n = 0.03  # [m / s^(1/3)]
max_manning_n = 0.2  # [m / s^(1/3)]
bankfull_depth_power = 0.4
bank_angle = 30.0  # [degrees]


# ## Use info for Baro River at Gambella ?

# In[2]:


if site_prefix == "Baro_Gam_1min":

    out_xres_sec = 60.0  # [arcseconds]
    out_yres_sec = 60.0  # [arcseconds]
    # Set the geographic bounding box and the grid cell size that
    # will be used for the TopoFlow model run, where
    #    Bounds = [ minlon, minlat, maxlon, maxlat ]
    # The bounding box MUST contain the entire watershed polygon.
    out_bounds = [34.22125, 7.3704166666, 36.43791666666, 9.50375]
    max_river_width = 140.0  # [meters]  from Google Maps or Google Earth
    A_out_km2 = 23567.7  # total contributing area at basin outlet [km2]
    Qbase_out = 40.0  # estimated baseflow discharge at basin outlet [m^3 / s]
    max_bankfull_depth = 8.0  # [meters]    # from literature or data


# ## Use info for Awash River at Oromia border ?

# In[3]:


if site_prefix == "Awash-border_60sec":

    out_xres_sec = 60.0  # [arcseconds]
    out_yres_sec = 60.0  # [arcseconds]
    # Bounds = [ minlon, minlat, maxlon, maxlat ]
    # The bounding box MUST contain the entire watershed polygon.
    # out_bounds = [  37.829583333333, 6.657916666666, 39.929583333333,  9.374583333333]  # (for 30 arcseconds)
    # out_bounds = [37.829583333333, 6.657916666666, 39.929583333333,  9.374583333333]  # (for 60 arcseconds)
    out_bounds = [37.829583333333, 6.654583333333, 39.934583333333, 9.374583333333]
    max_river_width = 25.0  # [meters]  from Google Maps or Google Earth
    A_out_km2 = 30679.5  # total contributing area at basin outlet [km2]
    Qbase_out = 10.0  # estimated baseflow discharge at basin outlet [m^3 / s]
    max_bankfull_depth = 4.0  # [meters]    # from literature or data


# ## Use info for Shebelle River at Imi ?

# In[4]:


if site_prefix == "Shebelle-Imi_60sec":

    out_xres_sec = 60.0  # [arcseconds]
    out_yres_sec = 60.0  # [arcseconds]
    # Bounds = [ minlon, minlat, maxlon, maxlat ]
    # The bounding box MUST contain the entire watershed polygon.
    # out_bounds = [ 38.159583333333, 6.324583333333, 43.559583333333, 9.899583333333]  # (for 30 arcseconds)
    out_bounds = [38.159583333333, 6.319583333333, 43.559583333333, 9.899583333333]
    max_river_width = 130.0  # [meters]  from Google Maps or Google Earth
    A_out_km2 = 90662.1  # total contributing area at basin outlet [km2]
    Qbase_out = 50.0  # estimated baseflow discharge at basin outlet [m^3 / s]
    max_bankfull_depth = 7.0  # [meters]    # from literature or data


# ## Use info for Ganale River at border ?

# In[5]:


# Actually, this tributary of the Ganale River is called: Welmel Shet River
# Outlet is at the border with Somali Region

if site_prefix == "Ganale-border_60sec":

    out_xres_sec = 60.0  # [arcseconds]
    out_yres_sec = 60.0  # [arcseconds]
    # Bounds = [ minlon, minlat, maxlon, maxlat ]
    # The bounding box MUST contain the entire watershed polygon.
    out_bounds = [
        39.174583333333,
        5.527916666666,
        41.124583333333,
        7.098749999999,
    ]  # (3 arcseconds)
    max_river_width = 40.0  # [meters]  from Google Maps or Google Earth
    A_out_km2 = 15241.7  # total contributing area at basin outlet [km2]
    Qbase_out = 3.0  # estimated baseflow discharge at basin outlet [m^3 / s]
    max_bankfull_depth = 2.0  # [meters]    # from literature or data


# ## Use info for Guder River at Blue Nile confluence ?

# In[6]:


if site_prefix == "Guder_30sec":
    out_xres_sec = 30.0  # [arcseconds]
    out_yres_sec = 30.0  # [arcseconds]
    # Bounds = [ minlon, minlat, maxlon, maxlat ]
    # The bounding box MUST contain the entire watershed polygon.
    out_bounds = [37.149583333333, 8.596250000000, 38.266250000000, 9.904583333333]
    max_river_width = 20.0  # [meters]  from Google Maps or Google Earth
    A_out_km2 = 6487.8  # total contributing area at basin outlet [km2]
    Qbase_out = 2.0  # estimated baseflow discharge at basin outlet [m^3 / s]
    max_bankfull_depth = 2.0  # [meters]    # from literature or data


# ## Use info for Muger River at Blue Nile confluence ?

# In[7]:


if site_prefix == "Muger_30sec":
    out_xres_sec = 30.0  # [arcseconds]
    out_yres_sec = 30.0  # [arcseconds]
    # Bounds = [ minlon, minlat, maxlon, maxlat ]
    # The bounding box MUST contain the entire watershed polygon.
    out_bounds = [37.807916666667, 8.929583333333, 39.032916666667, 10.112916666667]
    max_river_width = 45.0  # [meters]  from Google Maps or Google Earth
    A_out_km2 = 6924.12  # total contributing area at basin outlet [km2]
    Qbase_out = 3.0  # estimated baseflow discharge at basin outlet [m^3 / s]
    max_bankfull_depth = 2.0  # [meters]    # from literature or data


# # Create some directories in your home directory

# In[8]:


import glob
import os, os.path
import shutil

home_dir = os.path.expanduser("~")
test_dir = home_dir + "/TF_Tests"
basin_dir = test_dir + "/" + site_prefix
soil_dir = basin_dir + "/soil_data"
if not (os.path.exists(test_dir)):
    os.mkdir(test_dir)
if not (os.path.exists(basin_dir)):
    os.mkdir(basin_dir)
if not (os.path.exists(soil_dir)):
    os.mkdir(soil_dir)

os.chdir(basin_dir)


# # Copy a DEM into the new Basin directory

# A DEM for the entire country of Ethiopia, saved in GeoTIFF format and with a grid cell size of 3 arcseconds can be found in a shared Dropbox folder called MINT.  Copy this file into the basin directory you just created.

# In[9]:


src_dir = home_dir + "/Dropbox/MINT/Data/DEMs/Ethiopia/"
dem_file = "Ethiopia_MERIT_DEM.tif"
src_file = src_dir + dem_file
dst_file = dem_file
shutil.copyfile(src_file, dst_file)


# # Copy a set of CFG files into new Basin directory

# In[10]:


cfg_dir = src_dir + "cfg_files/"
os.chdir(cfg_dir)
cfg_file_list = sorted(glob.glob("*.cfg"))
os.chdir(basin_dir)
for cfg_file in cfg_file_list:
    shutil.copyfile(cfg_dir + cfg_file, cfg_file)

# Copy the default "provider_file"
provider_file = case_prefix + "_providers.txt"
shutil.copyfile(cfg_dir + provider_file, provider_file)


# # Copy an "outlets file" into new Basin dictory

# In[11]:


# This is not automated yet.  This file must be generated by a human with GIS softare.


# # Create a new "path_info" CFG file

# In[12]:


cfg_file = case_prefix + "_path_info.cfg"
cfg_unit = open(cfg_file, "w")

d1 = "~/TF_Tests/" + site_prefix
d2 = d1
cp = case_prefix
sp = site_prefix
bar = (
    "#===============================================================================\n"
)
cfg_unit.write(bar)
cfg_unit.write("# TopoFlow Config File for: Path_Information\n")
cfg_unit.write(bar)
L1 = "in_directory  | XX | string | input directory".replace("XX", d1)
L2 = "out_directory | XX | string | output directory".replace("XX", d2)
L3 = "site_prefix   | XX | string | file prefix for the study site".replace("XX", sp)
L4 = "case_prefix   | XX | string | file prefix for the model scenario".replace(
    "XX", cp
)
cfg_unit.write(L1 + "\n")
cfg_unit.write(L2 + "\n")
cfg_unit.write(L3 + "\n")
cfg_unit.write(L4 + "\n")
cfg_unit.close()


# # Import some utilities from TopoFlow

# In[13]:


from topoflow.utils import regrid
from topoflow.utils import import_grid
from topoflow.utils import fill_pits
from topoflow.utils import rtg_files
from topoflow.utils import rti_files
from topoflow.utils import parameterize
from topoflow.utils import init_depth
from topoflow.utils import pedotransfer

from topoflow.components import d8_global
from topoflow.components import smooth_DEM


# # Clip a source DEM to a bounding box and Resample

# Here, we use the TopoFlow <b>regrid</b> utility to <b>clip</b> a DEM for the entire country of Ethiopia to the geographic bounding box for a particular river basin in Ethiopia.  This utility uses the gdal.warp() function in the GDAL Python package.  For this example, we use the Baro River basin which lies mostly in the Oromia region but drains past the town of Gambella into the Gambella region.
#
# At the same time, we <b>resample</b> (via spatial bilinear interpolation) the resulting DEM to a different, coarser spatial resolution.  The source DEM has a grid cell size of 3 arcseconds (roughly 90 meters), while the new DEM has a grid cell size of 60 arcseconds (roughly 1800 meters).  Both the source DEM and new DEM are stored in GeoTIFF format.  Resampling typically causes the bounding box to change slightly.

# In[14]:


in_file = "Ethiopia_MERIT_DEM.tif"
out_file = site_prefix + "_rawDEM.tif"

### in_nodata = ????
### out_nodata = -9999.0

regrid.regrid_geotiff(
    in_file=in_file,
    out_file=out_file,
    out_bounds=out_bounds,
    out_xres_sec=out_xres_sec,
    out_yres_sec=out_yres_sec,
    ### in_nodata=None, out_nodata=None,
    RESAMPLE_ALGO="bilinear",
    REPORT=True,
)


# # Import a DEM from a GeoTIFF file

# Here we import a DEM in GeoTIFF format.  Note that NetCDF (.nc) and RiverTools Grid (RTG) formats can also be imported.
#
# Most of the TopoFlow utilities use grids saved in the RiverTools Grid (RTG) format, which is a generic, binary, row-major format.  Georeferencing information for the grid is stored in a small, separate text file in RiverTools Info (RTI) format.  When the rti_file argument is specified, georeferencing information is also saved in the RTI file format for later use.

# In[15]:


tif_file = site_prefix + "_rawDEM.tif"
rti_file = site_prefix + ".rti"
DEM = import_grid.read_from_geotiff(tif_file, REPORT=True, rti_file=rti_file)

grid_info = rti_files.read_info(rti_file)


# # Import a DEM from an RTG file (with RTI file)

# <b>This shows how to alternately import a DEM in RTG format, but is commented out for now.</b>

# In[16]:


# rtg_file = site_prefix + '_rawDEM.rtg'
# DEM = import_grid.read_from_rtg( rtg_file, REPORT=True)
# grid_info = rti_files.read_info( rtg_file )


# # Import a DEM from a netCDF file

# <b>This shows how to alternately import a DEM in netCDF format, but is commented out for now.</b>

# In[17]:


# nc_file = site_prefix + '_rawDEM.nc'
# DEM = import_grid.read_from_netcdf( nc_file, REPORT=True)


# # Create a DEM with smoother longitudinal profiles

# <b>This step is optional and has been commented out for now.</b>
#
# For so-called <b>mature</b> landscapes this "profile smoothing" algorithm works well, and results in a DEM with smoothly decreasing, nonzero channel slopes everywhere.  However, the landscape of the Baro River basin is not a good candidate because it is not mature.

# In[18]:


# c = smooth_DEM.DEM_smoother()
# c.DEBUG = True
# case_prefix = 'Test1'
# cfg_file = case_prefix + '_dem_smoother.cfg'
# c.initialize( cfg_file=cfg_file, mode='driver')
# c.update()


# # Fill depressions in DEM

# In[19]:


# data_type = 'FLOAT'
# shp = DEM.shape
# nrows = shp[0]
# ncols = shp[1]

data_type = grid_info.data_type  # e.g. "INTEGER" or "FLOAT"
ncols = grid_info.ncols
nrows = grid_info.nrows

fill_pits.fill_pits(DEM, data_type, ncols, nrows, SILENT=False)


# # Save depression-filled DEM to a file

# In[20]:


new_DEM_file = site_prefix + "_DEM.rtg"
rtg_files.write_grid(DEM, new_DEM_file, grid_info, SILENT=False)


# # Create a grid of D8 flow direction codes

# TopoFlow includes a component called <b>d8_global</b> that can compute a grid of D8 flow direction codes (Jenson 1984 convention), as well as several additional, related grids such as a grid of total contributing area (TCA).  TopoFlow components are configured through the use of configuration files, which are text files with the extension ".cfg".  Therefore, we now need to copy 2 CFG files into our working directory, called:  <i>Test1_path_info.cfg</i> (for path information) and <i>Test1_d8_global.cfg</i>.

# In[21]:


d8 = d8_global.d8_component()
d8.DEBUG = False
cfg_file = case_prefix + "_d8_global.cfg"
time = 0.0
d8.initialize(cfg_file=cfg_file, SILENT=False, REPORT=True)
d8.update(time, SILENT=False, REPORT=True)


# # Save a grid of D8 flow codes

# In[22]:


rti_file = site_prefix + ".rti"
grid_info = rti_files.read_info(rti_file, REPORT=True)

d8_code_file = site_prefix + "_flow.rtg"
rtg_files.write_grid(d8.d8_grid, d8_code_file, grid_info, RTG_type="BYTE")


# # Save the D8 total contributing area (TCA) grid

# In[23]:


d8_area_file = site_prefix + "_d8-area.rtg"
rtg_files.write_grid(d8.A, d8_area_file, grid_info, RTG_type="FLOAT", SILENT=False)


# # Compute and save the D8 slope grid

# In[24]:


d8.update_slope_grid()
d8_slope_file = site_prefix + "_slope.rtg"
rtg_files.write_grid(d8.S, d8_slope_file, grid_info, RTG_type="FLOAT", SILENT=False)


# # Compute and save the D8 "aspect" grid

# In[25]:


d8.update_aspect_grid()
d8_aspect_file = site_prefix + "_aspect.rtg"
rtg_files.write_grid(
    d8.aspect, d8_aspect_file, grid_info, RTG_type="FLOAT", SILENT=False
)


# # Create a grid of estimated channel widths

# First, use Google Maps or Google Earth to estimate the width of the river at the outlet to your river basin, in meters.  Here, we'll assume that width equals 140 meters.
#
# The idea is to estimate the channel widths throughout the basin (as a grid with the same dimensions as the DEM), using an empirical power law of the form:  $w = c \, A^p$
# where A is the total contributing area (TCA) that we computed as a grid above and saved into "d8_area_file".  A typical value of p is 0.5.  The value that w should have where A is maximum (e.g. the river outlet) is specified as g1.

# In[26]:


# Should be specified at the top of this notebook.
# max_river_width = 140.0  # [meters]
# channel_width_power = 0.5

cfg_dir = ""
width_file = site_prefix + "_chan-w.rtg"
parameterize.get_grid_from_TCA(
    site_prefix=site_prefix,
    cfg_dir=cfg_dir,
    area_file=d8_area_file,
    out_file=width_file,
    g1=max_river_width,
    p=channel_width_power,
)


# # Create a grid of estimated "Manning's n" values

# In order to compute grids of river flow velocity and discharge (volume flow rate), a very well-known, empirical formula known as <b>Manning's formula</b> (see Wikipedia) is the method used by default within TopoFlow.  This formula includes a parameter called <b>Manning's n</b>, that characterizes the roughness of the channel bed and resulting frictional loss of momentum.  Typical values in larger river channels range between 0.03 and 0.05.  Manning's formula can also be used for non-channelized, overland flow, but then a much larger value of 0.2 to 0.3 should be used.
#
# The following code uses a power-law estimate of the form:  $n = c \, A^p$, where A is the total contributing area (TCA) grid, to create a grid of Manning's n values.  The value that n should have where A is maximum (e.g. the river outlet) is set as <b>g1</b>.  Similarly, the value that n should have where A is minimum (e.g. on a ridge) is set as <b>g2</b>.  The coefficient, c, and power, p, are then set to match these constraints.

# In[27]:


# Should be specified at the top of this notebook.
# min_manning_n = 0.03
# max_manning_n = 0.2

manning_file = site_prefix + "_chan-n.rtg"
parameterize.get_grid_from_TCA(
    site_prefix=site_prefix,
    cfg_dir=cfg_dir,
    area_file=d8_area_file,
    out_file=manning_file,
    g1=min_manning_n,
    g2=max_manning_n,
)


# # Create a grid of estimated channel sinuosity values

# There are different definitions of channel sinuosity.  Here we are referring to the <b>absolute sinuosity</b>, defined as the ratio of the <b><i>along-channel flow distance</i></b> between the two endpoints of a channel and the <b><i>straight-line distance</i></b> between those endpoints.
#
# By this definition, sinuosity is <b>dimensionless</b> \[km/km\], with a minimum possible value of 1.0.  It tends to increase slowly from 1 where TCA is small to a larger value where TCA is big, but typically does not exceed 1.3.
#
# The following code uses a power-law estimate of the form:  $s = c \, A^p$, where A is the total contributing area (TCA) grid, to create a grid of sinuosity values.  The value that s should have where A is maximum (e.g. the river outlet) is set as <b>g1</b>.  Similarly, the value that n should have where A is minimum (e.g. near a ridge) is set as <b>g2</b>.  The coefficient, c, and power, p, are then set to match these constraints.

# In[28]:


# Should be specified at the top of this notebook.
# max_sinuosity = 1.3
min_sinuosity = 1.0  # (BY DEFINITION.  DO NOT CHANGE.)

sinu_file = site_prefix + "_sinu.rtg"
parameterize.get_grid_from_TCA(
    site_prefix=site_prefix,
    cfg_dir=cfg_dir,
    area_file=d8_area_file,
    out_file=sinu_file,
    g1=max_sinuosity,
    g2=min_sinuosity,
)


# # Create a grid of estimated bankfull depth values

# The <b>bankfull depth</b> is the maximum in-channel water depth of a river at a given location.  (It varies throughout a river basin.)  When the depth of water in a river exceeds this depth, <b>overbank flow</b> occurs and water enters the flood plain adjacent to the channel. <b>Overbank flow depth</b>, <b>inundation depth</b> or simply <b>flooding depth</b> are terms that refer to the depth of water on land outside of the river channel.  It is important to know the bankfull depth in order to more accurately predict the flooding depth.
#
# While remote sensing images can be used to estimate a river's bankfull width, the river bed typically cannot be "seen" through the water.  Moreover, bankfull depth is typically only measured at a few locations (e.g. at gauging stations) within a river basin, so accurate values of bankfull depth are difficult to obtain.
#
# The following code uses a power-law estimate of the form:  $d_b = c \, A^p$, where A is the total contributing area (TCA) grid, to create a grid of bankfull depth values.  The value that $d_b$ should have where A is maximum (e.g. the river outlet) is set as <b>g1</b>.  A typical, empirical value for p is 0.4. The coefficient, c, is then set to match these constraints.

# In[29]:


# Should be specified at the top of this notebook.
# max_bankfull_depth = 8.0  #### This must be determined from literature or data.
# bankfull_depth_power = 0.4

dbank_file = site_prefix + "_d-bank.rtg"
parameterize.get_grid_from_TCA(
    site_prefix=site_prefix,
    cfg_dir=cfg_dir,
    area_file=d8_area_file,
    out_file=dbank_file,
    g1=max_bankfull_depth,
    p=bankfull_depth_power,
)


# # Create a grid of estimated initial channel flow depth

# Here we attempt to estimate the initial depth of water for every channel in the river network.  This is supposed to be the "normal depth" of the river that is maintained by baseflow from groundwater (i.e. due to the groundwater table intersecting the channel bed) and is not attributed to a recent rainfall event.  This is the starting or initial condition for a model run.
#
# This routine uses a <b>grid-based Newton-Raphson</b> iterative scheme to solve a transcendental equation (see Wikipedia) for the initial depth of water in a channel network that results from groundwater baseflow.  The variables involved are:
#
# w = bed bottom width, trapezoid [m]<br>
# A = upstream area [$km^2$]<br>
# S = downstream slope [m/m]<br>
# n = Manning roughness parameter  [$s/m^{1/3}$]<br>
# $\theta$ = bank angle [degrees]<br>
# d = water depth in channel [m]<br>
# $A_c$ = wetted cross-section area [$m^2$]<br>
# P  = wetted cross-section perimeter [m]<br>
# $R_h = (A_c / P)$ = hydraulic radius [m]<br>
# B = spatially-uniform baseflow volume flux [$m s^{-1}$]<br>
#
# The equations used here are: <br>
# $Q = v \, A_c = B \,A$    [$m^3 s^{-1}$] (steady-state) <br>
# $v = (1/n) \, {R_h}^{2/3} \, S^{1/2} \,\,\,$  [SI units] <br>
# $R_h = A_c / P$ <br>
# $A_c = d \, [w + (d \, \tan(\theta))]$ <br>
# $P = w + [2 \, d \, / \cos(\theta)]$ <br>
#
# Note that B can be estimated from a baseflow discharge measured at the basin outlet.
#
# If we are given w, n, theta, A, S and B, then we get an equation for d that cannot be solved in closed form.  However, we can write the equation $v \, A_c = B \, A$ in the form needed to solve for d (in every grid cell) by Newton's method, i.e.:
# $F(d) = [v(d) \, A_c(d)] - (B \, A) = 0$.

# In[30]:


# Should be specified at the top of this notebook.
# A_out_km2 = 23567.7  # TCA at basin outlet of Baro River (at Gambella)  [km2]
# Qbase_out= 40.0      # estimated baseflow discharge at basin outlet [m^3 / s]

B_mps = init_depth.get_baseflow_volume_flux(A_out_km2, Qbase_out, REPORT=True)

d0_file = site_prefix + "_d0.rtg"
init_depth.compute_initial_depth(
    site_prefix=site_prefix,
    cfg_dir=cfg_dir,
    SILENT=False,
    baseflow_rate=B_mps,
    bank_angle=bank_angle,
    # angle_file=angle_file,
    area_file=d8_area_file,
    slope_file=d8_slope_file,
    width_file=width_file,
    manning_file=manning_file,
    sinu_file=sinu_file,
    d0_file=d0_file,
)


# # Download ISRIC soil property grids

# Files in soil_data folder were downloaded from the ISRIC SoilGrids website (https://soilgrids.org/) and span the entire country of Ethiopia.
# They contain soil property variables for each of 7 soil layers,
# with a 1 km grid cell size.

# ```
# Variables:
# BLDFIE = Bulk density [kg / m3]
# BDRICM = Absolute depth to bedrock [cm]
# CLYPPT = Mass fraction of clay [%]
# ORCDRC = Soil organic carbon content (fine earth fraction)  [g / kg]
# SLTPPT = Mass fraction of silt [%]
# SNDPPT = Mass fraction of sand [%]
#
# Layer 1 = sl1 = 0.00 to 0.05 m   (0  to  5 cm)
# Layer 2 = sl2 = 0.05 to 0.15 m   (5  to 15 cm)
# Layer 3 = sl3 = 0.15 to 0.30 m   (15 to 30 cm)
# Layer 4 = sl4 = 0.30 to 0.60 m   (30 to 60 cm)
# Layer 5 = sl5 = 0.60 to 1.00 m   (60 to 100 cm)
# Layer 6 = sl6 = 1.00 to 2.00 m   (100 to 200 cm)
# Layer 7 = sl7 = 2.00 to ??   m   (200 to ??? cm)
# ```

# In[31]:


src_soil_dir = home_dir + "/Dropbox/MINT/Data/DEMs/Ethiopia/soil_data/"
# Copy all TIF files from the shared MINT folder
os.chdir(src_soil_dir)
tif_file_list = sorted(glob.glob("*.tiff"))

# soil_dir was defined at the top, and is local.
os.chdir(soil_dir)
for tif_file in tif_file_list:
    shutil.copyfile(src_soil_dir + tif_file, tif_file)


# # Create grids of soil hydraulic properties

# Here, we first read a set of ISRIC <b>soil property</b> grids for each of 7 soil layers (see above) in GeoTIFF format.  We then regrid them to a chosen geographic bounding box and spatial resolution (grid cell size).  (Typically, we regrid to the TopoFlow model grid.)  Finally, we compute a corresponding set of <b>soil hydraulic property</b> grids that are used to compute infiltration.  These are referenced in the CFG files for the TopoFlow infiltration components.  The REPORT flag can be set to True to see more detailed information about each of the soil property grids.  Any warnings or errors are printed regardless.

# In[32]:


pedotransfer.save_soil_hydraulic_vars(
    site_prefix=site_prefix,
    in_dir=soil_dir,
    out_dir=basin_dir,
    out_bounds=out_bounds,
    REPORT=False,
    out_xres_sec=out_xres_sec,
    out_yres_sec=out_yres_sec,
    RESAMPLE_ALGO="bilinear",
)


# # Create a grid stack with space-time rainfall data

# This capability has been delegated to the MINT data transformation team, but later this section will show how to do it using only TopoFlow utilities.
#
# <b>Note:</b>  Downloading all of the required files can take hours to days.
#
# In addition to space-time rainfall rates, some of the TopoFlow components can make use of other meteorological variables such as:  air temperature, soil temperature, relative humidity, surface wind speed, shortware radiation and longwave radiation.

# # Create an "outlets file" of grid cells to monitor

# In TopoFlow component CFG files, flags can be set to tell TopoFlow to write values of chosen gridded variables to a file, to create a <b>grid stack</b>, indexed by time.  Grids are saved at a time interval set by <b>save_grid_dt</b>.
#
# Other flags in a CFG file can be set to tell TopoFlow to write values of chosen gridded variables to a file, but only at a specified set of grid cells.  These "monitored grid cells" or "virtual gauges" are set in an <b> outlets file</b> named <b>[case_prefix]_outlets.txt</b>.  An example of a TopoFlow outlets file is shown below.
#
# It is not necessary for the Area and Relief columns to contain valid values (they are for reference, but are unused).  However, the column, row, longitude and latitude of each grid cell to be monitored must be specified.  They must match columns and rows in the DEM that is being used for the model run.  Creating an outlets file therefore requires a <b>human in the loop</b>, using interactive GIS (Geographic Information System) software and making intelligent choices.  It cannot be automated.

# ```
# ------------------------------------------------------------
#  Monitored Grid Cell (Outlet) Information
# -------------------------------------------------------------------------------------
#     Column       Row     Area [km^2]      Relief [m]      Lon [deg]     Lat [deg]
# -------------------------------------------------------------------------------------
#         4         79        24647.3         2433.62       34.296250     8.1787500
#        14         76        24011.0         2425.90       34.462917     8.2287500
#        29         79        22972.0         2393.16       34.712917     8.1787500
#        48         59          507.3         1434.04       35.029583     8.5120833
#        48         60        15771.9         1915.20       35.029583     8.4954167
#        45         76         4692.4         1938.31       34.979583     8.2287850
#        44         74        16391.1         2202.76       34.962917     8.2620833
#        56         81         1348.6         1499.01       35.162917     8.1454167
# ```

# In[ ]:


def main(in_file, out_file, out_bounds, out_xres_sec, out_yres_sec):
    """
    Example main function for Topoflow transformation
    :param in_file: Input file
    :param out_file: Output file
    :param out_bounds: bounding box
    :param out_xres_sec: x resolution
    :param out_yres_sec: y resolution
    """
    regrid.regrid_geotiff(
        in_file=in_file,
        out_file=out_file,
        out_bounds=out_bounds,
        out_xres_sec=out_xres_sec,
        out_yres_sec=out_yres_sec,
        ### in_nodata=None, out_nodata=None,
        RESAMPLE_ALGO="bilinear",
        REPORT=True,
    )

    return out_file # need to return output file path
