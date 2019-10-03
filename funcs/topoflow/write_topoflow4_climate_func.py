#!/usr/bin/python
# -*- coding: utf-8 -*-
from pathlib import Path

import numpy as np
from typing import Union

from dtran.argtype import ArgType
from dtran.ifunc import IFunc
from os.path import join

import gdal, osr  ## ogr
import glob
from scipy.special import gamma

from funcs.topoflow.rti_files import generate_rti_file


class Topoflow4ClimateWriteFunc(IFunc):
    id = "topoflow4_climate_write_func"
    inputs = {
        "input_dir": ArgType.String,
        "output_file": ArgType.FilePath,
        "DEM_bounds": ArgType.String,
        "DEM_xres": ArgType.String,
        "DEM_yres": ArgType.String,
        "DEM_ncols": ArgType.String,
        "DEM_nrows": ArgType.String,
    }
    outputs = {}

    def __init__(self, input_dir: str, output_file: Union[str, Path], DEM_bounds: str, DEM_xres: str, DEM_yres: str,
                 DEM_ncols: str, DEM_nrows: str):
        self.DEM = {
            "bounds": [float(x.strip()) for x in DEM_bounds.split(",")],
            "xres": float(DEM_xres),
            "yres": float(DEM_yres),
            "ncols": float(DEM_ncols),
            "nrows": float(DEM_nrows),
        }
        self.input_dir = str(input_dir)
        self.output_file = str(output_file)

    def exec(self) -> dict:
        create_rts_from_nc_files(self.input_dir, self.output_file, self.DEM)
        return {}

    def validate(self) -> bool:
        return True


def regrid_geotiff_to_dem(in_file=None, out_file=None,
                          DEM_bounds=None, DEM_xres=None, DEM_yres=None):
    # ---------------------------------------------------------------
    # Note:  DEM_bounds = [dem_xmin, dem_ymin, dem_xmax, dem_ymax]
    #        Give xres, yres in decimal degrees for Geographic.
    #        gdal.Warp() clips to a bounding box, and can also
    #        resample to a different resolution.
    #        gdal.Translate() is faster for simple clipping.
    # ---------------------------------------------------------------
    if (in_file == None):
        # -----------------------------------------------------------
        # Use Pongo_30sec DEM as a test, which works well.
        # However,  the soil data has same resolution (xres, yres)
        # as the DEM, of 30 arcseconds.  In addition, grid cells
        # outside of South Sudan have NODATA values.
        # -----------------------------------------------------------
        in_file = 'SLTPPT_M_sl1_1km_South Sudan.tiff'
        out_file = 'Pongo_SLTPPT_sl1.tiff'
        DEM_bounds = [24.079583333333, 6.565416666666, 27.379583333333, 10.132083333333]
        DEM_xres = 1. / 120  # (30 arcsecs = 30/3600 degrees)
        DEM_yres = 1. / 120  # (30 arcsecs = 30/3600 degrees)

    f1 = gdal.Open(in_file, gdal.GA_ReadOnly)
    ## data_xres = f1.RasterXsize
    ### data_yres = f1.RasterYsize
    # print( f1.RasterCount )
    # print( data_xres, data_yres )

    out_unit = gdal.Warp(out_file, f1,
                         format='GTiff',  # (output format string)
                         outputBounds=DEM_bounds, xRes=DEM_xres, yRes=DEM_yres,
                         resampleAlg=gdal.GRA_Bilinear)
    ## resampleAlg = gdal.GRA_NearestNeighbour )
    # (near, bilinear, cubic, cubicspline, lanczos, average, etc.)
    out_unit = None  # Close out_file

    # --------------------------------------------------------
    # Example:  Use gdal.Translate to clip to bounding box.
    # --------------------------------------------------------
    # ds = gdal.Open('original.tif')
    # ds = gdal.Translate('new.tif', ds, projWin = [-75.3, 5.5, -73.5, 3.7])
    # ds = None

    # --------------------------------------------------------
    # This shows some of the other keywords to gdal.Warp.
    # --------------------------------------------------------
    # WarpOptions(options=[], format=None, outputBounds=None,
    # outputBoundsSRS=None, xRes=None, yRes=None, targetAlignedPixels=False,
    # width=0, height=0, srcSRS=None, dstSRS=None, srcAlpha=False,
    # dstAlpha=False, warpOptions=None, errorThreshold=None,
    # warpMemoryLimit=None, creationOptions=None, outputType=GDT_Unknown,
    # workingType=GDT_Unknown, resampleAlg=None, srcNodata=None,
    # dstNodata=None, multithread=False, tps=False, rpc=False,
    # geoloc=False, polynomialOrder=None, transformerOptions=None,
    # cutlineDSName=None, cutlineLayer=None, cutlineWhere=None,
    # cutlineSQL=None, cutlineBlend=None, cropToCutline=False,
    # copyMetadata=True, metadataConflictValue=None,
    # setColorInterpretation=False, callback=None, callback_data=None)
    # 
    # Create a WarpOptions() object that can be passed to gdal.Warp()
    # Keyword arguments are : options --- can be be an array of strings,
    # a string or let empty and filled from other keywords.


#    regrid_geotiff_to_dem()
# -------------------------------------------------------------------
# def download_data():
# 
#     from pydap.client import open_url
#     from pydap.cas.urs import setup_session
#     dataset_url = 'http://server.example.com/path/to/dataset'
#     session = setup_session(username, password, check_url=dataset_url)
#     dataset = open_url(dataset_url, session=session)
# 
# #    download_data()
# -------------------------------------------------------------------
def read_nc_grid(nc_file=None, var_name='HQprecipitation',
                 REPORT=False):
    if (nc_file == None):
        nc_file = 'TEST.nc4'

    ds = gdal.Open("NETCDF:{0}:{1}".format(nc_file, layer_name))
    grid = ds.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize)
    ds = None  # (close ds)

    if (REPORT):
        print('grid.min() =', grid.min())
        print('grid.max() =', grid.max())
        print('grid.shape =', grid.shape)

    return grid

    # --------------------
    # This doesn't work
    # --------------------


#     ds = gdal.Open( nc_file )
#     # print( ds.RasterCount )
#     # print( ds.RasterYSize, ds.RasterXsize )
#     data = ds.ReadAsArray()
#     # print( data.shape )
#     print( data.min() )
#     print( data.max() )
#     ds = None  # (close ds)

#   read_nc_grid()
# -------------------------------------------------------------------
# def read_nc_as_array( nc_file=None, var_name='HQprecipitation',
#                       REPORT=False):
#                       
#     ds = gdal.Open( nc_file )
#     if (ds is None):
#         print( 'Open failed.')
#          sys.exit()
#     
#     if (ds.GetSubDatasets() >= 1):
#         subdataset = 'NETCDF:"' + nc_file + '":' + var_name
#         ds_sd = gdal.Open( subdataset )
#         NDV   = ds_sd.GetRasterBand(1).GetNoDataValue()
#         ncols = ds_sd.RasterXsize
#         nrows = ds_sd.RasterYsize
#         GeoT  = ds_sd.GetGeoTransform()
#         ds    = None
#         ds_sd = None  
#   
# #   read_nc_as_array()
# -------------------------------------------------------------------
def gdal_open_nc_file(nc_file, var_name, VERBOSE=False):
    ### ds_in = gdal.Open("NETCDF:{0}:{1}".format(nc_file, var_name), gdal.GA_ReadOnly )
    ds_in = gdal.Open("NETCDF:{0}:{1}".format(nc_file, var_name))
    band = ds_in.GetRasterBand(1)
    nodata = band.GetNoDataValue()

    g1 = band.ReadAsArray()
    ## g1 = ds_in.ReadAsArray(0, 0, ds_in.RasterXSize, ds_in.RasterYSize)

    if (VERBOSE):
        print('grid1: min =', g1.min(), 'max =', g1.max())
        print('grid1.shape =', g1.shape)
        print('grid1.dtype =', g1.dtype)
        print('grid1 nodata =', nodata)
        w = np.where(g1 > nodata)
        nw = w[0].size
        print('grid1 # data =', nw)
        print(' ')

    return (ds_in, g1, nodata)


# gdal_open_nc_file()
# -------------------------------------------------------------------
def get_raster_bounds(ds, VERBOSE=False):
    # -------------------------------------------------------------
    # Note:  The bounds depend on the map projection and are not
    # necessarily a Geographic bounding box of lons and lats.    
    # -------------------------------------------------------------
    # See:
    # https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html
    # and search on "geotransform".  An example of gdal.SetGeoTransform
    # gives: [xmin, pixel_size, 0, ymax, 0, -pixel_size].
    # Also says args are:
    # [ulx, xDist, rtnX, uly, yDist, rtnY]
    # This is consistent with information below.
    # -------------------------------------------------------------
    # ulx = upper left x  = xmin
    # uly = upper left y  = ymax
    # lrx = lower right x = xmax
    # lry = lower right y = ymin
    # -----------------------------

    # ----------------------------------------------------------
    # Notice the strange order or parameters here is CORRECT.
    # It is not:  ulx, xres, xskew, uly, yres, yskew
    # ----------------------------------------------------------
    ulx, xres, xskew, uly, yskew, yres = ds.GetGeoTransform()
    lrx = ulx + (ds.RasterXSize * xres)
    lry = uly + (ds.RasterYSize * yres)

    if (VERBOSE):
        print('ulx, uly   =', ulx, uly)
        print('lrx, lry   =', lrx, lry)
        print('xres, yres = ', xres, yres)
        print('xskew, yskew =', xskew, yskew)
        print('----------------------------------')

    #########################################################
    # Bounding box reported by gdal.info does not match
    # what the GES DISC website is saying.  The result is
    # that gdal.Warp gives all nodata values in output. 
    #########################################################
    return [ulx, lry, lrx, uly]  # [xmin, ymin, xmax, ymax]

    #########################################################
    # Bounding box reported by gdal.info does not match
    # what the GES DISC website is saying.  Reversing lats
    # and lons like this doesn't fix the problem.
    #########################################################    
    ## return [lry, ulx, uly, lrx]


#   get_raster_bounds()
# -------------------------------------------------------------------
def fix_raster_bounds(ds, VERBOSE=False):
    # ------------------------------------------------------------
    # Note:  NetCDF files downloaded from the GES DISC website
    #        have corner coordinate lons and lats reversed.
    #        I checked with multiple files for which bounding
    #        box was known that when gdalinfo reports Corner
    #        Coordinates, it uses (lon, lat) vs. (lat, lon).
    #        Here, we use SetGeoTransform to fix the bounding
    #        box, so that gdal.Warp() and other gdal functions
    #        will work correctly.  (8/14/2019)
    # ------------------------------------------------------------
    ulx, xres, xskew, uly, yskew, yres = ds.GetGeoTransform()
    lrx = ulx + (ds.RasterXSize * xres)
    lry = uly + (ds.RasterYSize * yres)

    ulx2 = lry
    uly2 = lrx
    lrx2 = uly
    lry2 = ulx
    # lrx2 = ulx2 + (ds.RasterXsize * xres)
    # Note:  (xres > 0, yres < 0)

    if (VERBOSE):
        # -----------------------------------------------------
        # These print out correctly, but the reported corner
        # coordinates are now really messed up.
        # Need to close or flush to make new info "stick" ?
        # -----------------------------------------------------
        print('in_bounds  =', ulx, lry, lrx, uly)  # (2,20,15,40)
        print('out_bounds =', ulx2, lry2, lrx2, uly2)  # (20,2,40,15)
        print(' ')

    ds.SetGeoTransform((ulx2, xskew, xres, uly2, yskew, yres))


#   fix_raster_bounds()
# -------------------------------------------------------------------
def bounds_disjoint(bounds1, bounds2, VERBOSE=False):
    # -----------------------------------------------------------
    # Note.  Assume both bounds are in same spatial reference
    #        system (SRS), e.g. Geographic lons and lats.
    # ------------------------------------------------------------------
    # https://gamedev.stackexchange.com/questions/586/
    # what-is-the-fastest-way-to-work-out-2d-bounding-box-intersection
    # ------------------------------------------------------------------
    b1_xmin = bounds1[0]
    b1_xmax = bounds1[2]
    b2_xmin = bounds2[0]
    b2_xmax = bounds2[2]
    #     x_overlap1 = (b1_xmin < b2_xmin) and (b2_xmin < b1_xmax)
    #     x_overlap2 = (b2_xmin < b1_xmin) and (b1_xmin < b2_xmax)
    #     x_overlap  = (x_overlap1 or x_overlap2)

    b1_ymin = bounds1[1]
    b1_ymax = bounds1[3]
    b2_ymin = bounds2[1]
    b2_ymax = bounds2[3]
    #     y_overlap1 = (b1_ymin < b2_ymin) and (b2_ymin < b1_ymax)
    #     y_overlap2 = (b2_ymin < b1_ymin) and (b1_ymin < b2_ymax)
    #     y_overlap  = (y_overlap1 or y_overlap2)
    #     return not(x_overlap and y_overlap)

    disjoint = (b2_xmin > b1_xmax) or (b2_xmax < b1_xmin) or \
               (b2_ymax < b1_ymin) or (b2_ymin > b1_ymax)

    return disjoint


#   bounds_disjoint()
# -------------------------------------------------------------------
def gdal_regrid_to_dem_grid(ds_in, tmp_file,
                            nodata, DEM_bounds, DEM_xres, DEM_yres,
                            RESAMPLE_ALGO='bilinear', VERBOSE=False):
    # -----------------------------------
    # Specify the resampling algorithm
    # -----------------------------------
    algo_dict = {
        'nearest': gdal.GRA_NearestNeighbour,
        'bilinear': gdal.GRA_Bilinear,
        'cubic': gdal.GRA_Cubic,
        'cubicspline': gdal.GRA_CubicSpline,
        'lanczos': gdal.GRA_Lanczos,
        'average': gdal.GRA_Average,
        'min': gdal.GRA_Min,
        'max': gdal.GRA_Max,
        'mode': gdal.GRA_Mode,
        'med': gdal.GRA_Med}

    resample_algo = algo_dict[RESAMPLE_ALGO]

    # --------------------------------------------------
    # Use gdal.Warp to clip and resample to DEM grid
    # then save results to a GeoTIFF file (tmp_file).
    # --------------------------------------------------
    ds_tmp = gdal.Warp(tmp_file, ds_in,
                       format='GTiff',  # (output format string)
                       outputBounds=DEM_bounds, xRes=DEM_xres, yRes=DEM_yres,
                       srcNodata=nodata,  ########
                       ### dstNodata=nodata,  ########
                       resampleAlg=resample_algo)

    grid = ds_tmp.ReadAsArray()

    ds_tmp = None  # Close tmp_file

    return grid


#   gdal_regrid_to_dem_grid()
# -------------------------------------------------------------------
def resave_grid_to_geotiff(ds_in, new_file, grid1, nodata):
    new_nodata = -9999.0
    grid1[grid1 <= nodata] = new_nodata

    ##### raster = gdal.Open( nc_file )
    raster = ds_in
    ncols = raster.RasterXSize
    nrows = raster.RasterYSize

    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(new_file, ncols, nrows, 1, gdal.GDT_Float32)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(grid1)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


#   resave_grid_to_geotiff()
# -------------------------------------------------------------------
def fix_gpm_file_as_geotiff(nc_file, var_name, out_file,
                            out_nodata=0.0, VERBOSE=False):
    ### raster = gdal.Open("NETCDF:{0}:{1}".format(nc_file, var_name), gdal.GA_ReadOnly )
    raster = gdal.Open("NETCDF:{0}:{1}".format(nc_file, var_name))
    band = raster.GetRasterBand(1)
    ncols = raster.RasterXSize
    nrows = raster.RasterYSize
    proj = raster.GetProjectionRef()
    bounds = get_raster_bounds(raster)  ######
    nodata = band.GetNoDataValue()
    array = band.ReadAsArray()
    ## array = raster.ReadAsArray(0, 0, ds_in.RasterXSize, ds_in.RasterYSize)
    # ----------------------------------------------
    # Get geotransform for array in nc_file
    # Note:  These look strange, but are CORRECT.
    # ----------------------------------------------
    geotransform = raster.GetGeoTransform()
    ulx = geotransform[0]
    xres = geotransform[1]
    xrtn = geotransform[2]
    # -----------------------
    uly = geotransform[3]
    yrtn = geotransform[4]  # (not yres !!)
    yres = geotransform[5]  # (not yrtn !!)
    raster = None  # Close the nc_file

    if (VERBOSE):
        print('array: min  =', array.min(), 'max =', array.max())
        print('array.shape =', array.shape)
        print('array.dtype =', array.dtype)
        print('array nodata =', nodata)
        w = np.where(array > nodata)
        nw = w[0].size
        print('array # data =', nw)
        print(' ')

    # ----------------------------------------------
    # Rotate the array; column major to row major
    # a           = [[7,4,1],[8,5,2],[9,6,3]]
    # np.rot90(a) = [[1,2,3],[4,5,6],[7,8,9]]
    # ----------------------------------------------
    ### array2 = np.transpose( array )
    array2 = np.rot90(array)  ### counter clockwise
    ncols2 = nrows
    nrows2 = ncols

    # -------------------------
    # Change the nodata value
    # -------------------------
    array2[array2 <= nodata] = out_nodata

    # -----------------------------------------
    # Build new geotransform & projectionRef
    # -----------------------------------------
    lrx = bounds[2]
    lry = bounds[1]
    ulx2 = lry
    uly2 = lrx
    xres2 = -yres
    yres2 = -xres
    xrtn2 = yrtn
    yrtn2 = xrtn
    geotransform2 = (ulx2, xres2, xrtn2, uly2, yrtn2, yres2)
    proj2 = proj

    if (VERBOSE):
        print('geotransform  =', geotransform)
        print('geotransform2 =', geotransform2)

    # ------------------------------------
    # Write new array to a GeoTIFF file
    # ------------------------------------
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(out_file, ncols2, nrows2, 1, gdal.GDT_Float32)
    outRaster.SetGeoTransform(geotransform2)
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array2)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(proj2)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

    # ---------------------
    # Close the out_file
    # ---------------------
    outRaster = None


#   fix_gpm_file_as_geotiff()         
# -------------------------------------------------------------------
def create_rts_from_nc_files(nc_dir_path, rts_file, DEM_info: dict,
                             IN_MEMORY=False, VERBOSE=False,
                             NC4=False):
    # ------------------------------------------------------
    # For info on GDAL constants, see:
    # https://gdal.org/python/osgeo.gdalconst-module.html
    # ------------------------------------------------------

    ############### TODO: this is temporary ###############
    # if (rts_file == 'TEST.rts'):
    # -----------------------------------------------------------
    DEM_bounds = DEM_info["bounds"]
    DEM_xres = DEM_info["xres"]
    DEM_yres = DEM_info["yres"]
    DEM_ncols = DEM_info["ncols"]
    DEM_nrows = DEM_info["nrows"]
    #######################################################

    # -----------------------------------------
    # Use a temp file in memory or on disk ?
    # -----------------------------------------
    if (IN_MEMORY):
        tmp_file = '/vsimem/TEMP.tif'
    else:
        tmp_file = '/tmp/TEMP.tif'

    # -------------------------
    # Open RTS file to write
    # -------------------------
    rts_unit = open(rts_file, 'wb')

    # ------------------------------------------------
    # Get list of all nc files in working directory
    # ------------------------------------------------

    suffix = '*.nc'
    if NC4:
        suffix += '4'

    nc_file_list = sorted(glob.glob(join(nc_dir_path, suffix)))
    var_name = "HQprecipitation"  # HQ = high quality;  1/2 hourly, mmph
    count = 0
    bad_count = 0
    BAD_FILE = False
    #### rts_nodata = -9999.0    #################
    rts_nodata = 0.0  # (good for rainfall rates; not general)
    Pmax = -1
    tif_file = '/tmp/TEMP1.tif'

    for nc_file in nc_file_list:
        # -------------------------------
        # Open the original netCDF file
        # --------------------------------
        ## (ds_in, grid1, nodata) = gdal_open_nc_file( nc_file, var_name, VERBOSE=True)

        # ------------------------------------------
        # Option to fix problem with bounding box
        # ------------------------------------------
        ### fix_raster_bounds( ds_in )

        # ------------------------------------------
        # Fix GPM netCDF file, resave as GeoTIFF, 
        # then open the new GeoTIFF file
        # ------------------------------------------
        fix_gpm_file_as_geotiff(nc_file, var_name, tif_file,
                                out_nodata=rts_nodata)
        ds_in = gdal.Open(tif_file)
        grid1 = ds_in.ReadAsArray()
        gmax = grid1.max()
        Pmax = max(Pmax, gmax)
        band = ds_in.GetRasterBand(1)
        nc_nodata = band.GetNoDataValue()

        if (VERBOSE):
            print('===============================================================')
            print('count =', (count + 1))
            print('===============================================================')
            print('grid1: min   =', grid1.min(), 'max =', grid1.max())
            print('grid1.shape  =', grid1.shape)
            print('grid1.dtype  =', grid1.dtype)
            print('grid1 nodata =', nc_nodata)
            w = np.where(grid1 > nc_nodata)
            nw = w[0].size
            print('grid1 # data =', nw)
            print(' ')

        # --------------------------------------
        # Use gdal.Info() to print/check info
        # --------------------------------------
        ## print( gdal.Info( ds_in ) )
        ## print( '===============================================================')

        # -----------------------------------------------
        # Check if the bounding boxes actually overlap
        # -----------------------------------------------
        ds_bounds = get_raster_bounds(ds_in, VERBOSE=False)
        if (bounds_disjoint(ds_bounds, DEM_bounds)):
            print('###############################################')
            print('WARNING: Bounding boxes do not overlap.')
            print('         New grid will contain only nodata.')
            print('###############################################')
            print('count =', count)
            print('file  =', nc_file)
            print('ds_bounds  =', ds_bounds)
            print('DEM_bounds =', DEM_bounds)
            print(' ')
            bad_count += 1
            BAD_FILE = True

        # -------------------------------------------
        # Replace nodata value and save as GeoTIFF
        # -------------------------------------------
        #         new_file = 'TEMP2.tif'
        #         resave_grid_to_geotiff( ds_in, new_file, grid1, nodata )
        #         ds_in = None  # Close the nc_file
        #         ds_in = gdal.Open( new_file )   # Open the GeoTIFF file; new nodata

        # -------------------------------------------
        # Clip and resample data to the DEM's grid
        # then save to a temporary GeoTIFF file.
        # -------------------------------------------
        if not (BAD_FILE):
            grid2 = gdal_regrid_to_dem_grid(ds_in, tmp_file,
                                            rts_nodata, DEM_bounds, DEM_xres, DEM_yres,
                                            RESAMPLE_ALGO='bilinear')
            if (VERBOSE):
                print('grid2: min  =', grid2.min(), 'max =', grid2.max())
                print('grid2.shape =', grid2.shape)
                print('grid2.dtype =', grid2.dtype)
                w = np.where(grid2 > rts_nodata)
                nw = w[0].size
                print('grid2 # data =', nw)
                print(' ')
            ds_in = None  # Close the tmp_file
            if (IN_MEMORY):
                gdal.Unlink(tmp_file)
        else:
            grid2 = np.zeros((DEM_nrows, DEM_ncols), dtype='float32')
            grid2 += rts_nodata

        # -------------------------
        # Write grid to RTS file
        # -------------------------
        grid2 = np.float32(grid2)
        grid2.tofile(rts_unit)
        count += 1

        # --------------------------------------------
        # Read resampled data from tmp GeoTIFF file
        # --------------------------------------------
        # This step shouldn't be necessary. #######
        # --------------------------------------------
    #         ds_tmp = gdal.Open( tmp_file )
    #         ## ds_tmp = gdal.Open( tmp_file, gdal.GA_ReadOnly  )
    #         ## print( gdal.Info( ds_tmp ) )
    #         grid3  = ds_tmp.ReadAsArray()
    #         if (VERBOSE):
    #             print( 'grid3: min, max =', grid3.min(), grid3.max() )
    #             print( 'grid3.shape =', grid3.shape)
    #             print( 'grid3.dtype =', grid3.dtype)
    #             w  = np.where(grid3 > nodata)
    #             nw = w[0].size
    #             print( 'grid3 # data =', nw)
    #         ds_tmp = None   # Close tmp file
    #
    #         if (IN_MEMORY):
    #             gdal.Unlink( tmp_file )
    #         #-------------------------
    #         # Write grid to RTS file
    #         #-------------------------
    #         grid3 = np.float32( grid3 )
    #         ## rts_unit.write( grid3 )  # (doesn't work)
    #         grid3.tofile( rts_unit )
    #         count += 1

    #         if (count == 300):  ##################################
    #             break

    # ---------------------
    # Close the RTS file
    # ---------------------
    rts_unit.close()

    # Generate RTI file
    rti_fname = rts_file.replace('.rts', '.rti')
    generate_rti_file(rts_file, rti_fname, DEM_ncols, DEM_nrows, DEM_xres, DEM_yres)

    print(' ')
    print('Max precip rate =', Pmax)
    print('bad_count =', bad_count)
    print('n_grids   =', count)
    print('Finished saving data to rts file and generating a matching rti file.')
    print(' ')