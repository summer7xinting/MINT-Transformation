#!/usr/bin/python
# -*- coding: utf-8 -*-
import glob
import re
from os.path import join
from pathlib import Path
from typing import Union, List, Optional, Dict

import gdal  # # ogr
import numpy as np
import os
import osr

from dtran.metadata import Metadata
from funcs.topoflow.nc2geotiff import nc2geotiff
from tqdm import tqdm
from zipfile import ZipFile

from dtran.argtype import ArgType
from dtran.ifunc import IFunc, IFuncType
from funcs.topoflow.rti_files import generate_rti_file


class Topoflow4ClimateWriteFunc(IFunc):
    id = "topoflow4_climate_write_func"
    description = ''' A reader-transformation-writer multi-adapter.
    Creates a zip file of RTS (and RTI) file from NetCDF (climate) files.
    '''
    inputs = {
        "input_dir": ArgType.String,
        "temp_dir": ArgType.String,
        "output_file": ArgType.String,
        "var_name": ArgType.String,
        "DEM_bounds": ArgType.String,
        "DEM_xres_arcsecs": ArgType.String,
        "DEM_yres_arcsecs": ArgType.String,
    }
    outputs = {"output_file": ArgType.String}
    friendly_name: str = "Topoflow Climate"
    func_type = IFuncType.MODEL_TRANS
    example = {
        "input_dir": "$.my_dcat_read_func.data",
        "temp_dir": "/data/mint/sample_grid_baro",
        "output_file": "/data/mint/sample_baro/climate_all.zip",
        "var_name": "HQprecipitation",
        "DEM_bounds": "34.221249999999, 7.362083333332, 36.446249999999, 9.503749999999",
        "DEM_xres_arcsecs": "30",
        "DEM_yres_arcsecs": "30"
    }

    def __init__(self, input_dir: str, temp_dir: str, output_file: Union[str, Path], var_name: str, DEM_bounds: str, DEM_xres_arcsecs: str, DEM_yres_arcsecs: str):
        self.DEM = {
            "bounds": [float(x.strip()) for x in DEM_bounds.split(",")],
            "xres": float(DEM_xres_arcsecs) / 3600.0,
            "yres": float(DEM_yres_arcsecs) / 3600.0,
        }
        self.var_name = var_name
        self.input_dir = str(input_dir)
        self.temp_dir = str(temp_dir)
        self.output_file = str(output_file)

    def exec(self) -> dict:
        for path in [self.input_dir, self.temp_dir]:
            Path(path).mkdir(exist_ok=True, parents=True)

        Path(self.output_file).parent.mkdir(exist_ok=True, parents=True)

        create_rts_from_nc_files(self.input_dir, self.temp_dir, self.output_file, self.DEM, self.var_name, IN_MEMORY=True)
        return {"output_file": self.output_file}

    def validate(self) -> bool:
        return True


class Topoflow4ClimateWritePerMonthFunc(IFunc):
    id = "topoflow4_climate_write_per_month_func"
    description = ''' A reader-transformation-writer multi-adapter.
    Creates RTS (and RTI) files per month from NetCDF (climate) files.
    '''
    inputs = {
        "grid_dir": ArgType.String,
        "date_regex": ArgType.String,
        "output_file": ArgType.FilePath,
    }
    outputs = {}
    friendly_name: str = "Topoflow Climate Per Month"
    func_type = IFuncType.MODEL_TRANS
    example = {
        "grid_dir": f"/data/mint/gpm_grid_baro",
        "date_regex": '3B-HHR-E.MS.MRG.3IMERG.(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})',
        "output_file": f"/data/mint/baro/climate.rts",
    }

    def __init__(self, grid_dir: str, date_regex: str, output_file: Union[str, Path]):
        self.grid_dir = str(grid_dir)
        self.date_regex = re.compile(str(date_regex))
        self.output_file = str(output_file)

    def exec(self) -> dict:
        grid_files_per_month = {}
        for grid_file in glob.glob(join(self.grid_dir, '*.npz')):
            month = self.date_regex.match(Path(grid_file).name).group('month')
            if month not in grid_files_per_month:
                grid_files_per_month[month] = []
            grid_files_per_month[month].append(grid_file)

        for month in sorted(grid_files_per_month.keys()):
            grid_files = grid_files_per_month[month]
            print(">>> Process month", month, "#files=", len(grid_files))
            output_file = Path(self.output_file).parent / f"{Path(self.output_file).stem}.{month}.rts"
            write_grid_files_to_rts(grid_files, output_file)
        return {}

    def validate(self) -> bool:
        return True

    def change_metadata(self, metadata: Optional[Dict[str, Metadata]]) -> Dict[str, Metadata]:
        return metadata


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
                            RESAMPLE_ALGO='bilinear'):
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
    # gdal_bbox = [DEM_bounds[0], DEM_bounds[2], DEM_bounds[1], DEM_bounds[3]]
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


def get_tiff_file(temp_bin_dir, ncfile):
    return os.path.join(temp_bin_dir, f"{Path(ncfile).stem}.tif")


def extract_grid_data(args):
    output_dir, nc_file, var_name, rts_nodata, DEM_bounds, DEM_nrows, DEM_ncols, DEM_xres, DEM_yres, VERBOSE, IN_MEMORY = args
    if IN_MEMORY:
        tif_file1 = f'/vsimem/{Path(nc_file).stem}.tmp.tif'
        tif_file2 = f'/vsimem/{Path(nc_file).stem}.tmp.2.tif'
    else:
        tif_file1 = f'/tmp/{Path(nc_file).stem}.tmp.tif'
        tif_file2 = f'/tmp/{Path(nc_file).stem}.tmp.2.tif'

    nc2geotiff(nc_file, var_name, tif_file1,
                                no_data=rts_nodata)

    ds_in = gdal.Open(tif_file1)
    grid1 = ds_in.ReadAsArray()
    gmax = grid1.max()
    band = ds_in.GetRasterBand(1)
    nc_nodata = band.GetNoDataValue()

    if (VERBOSE):
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
    BAD_FILE = False
    if (bounds_disjoint(ds_bounds, DEM_bounds)):
        print('###############################################')
        print('WARNING: Bounding boxes do not overlap.')
        print('         New grid will contain only nodata.')
        print('###############################################')
        print('file  =', nc_file)
        print('ds_bounds  =', ds_bounds)
        print('DEM_bounds =', DEM_bounds)
        print(' ')
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
        grid2 = gdal_regrid_to_dem_grid(ds_in, tif_file2,
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

        if IN_MEMORY:
            gdal.Unlink(tif_file2)
        else:
            os.remove(tif_file2)
    else:
        grid2 = np.zeros((DEM_nrows, DEM_ncols), dtype='float32')
        grid2 += rts_nodata

    if IN_MEMORY:
        gdal.Unlink(tif_file1)
    else:
        os.remove(tif_file1)

    grid2 = np.float32(grid2)
    np.savez_compressed(os.path.join(output_dir, f"{Path(nc_file).stem}.npz"), grid=grid2)
    # grid2.tofile(os.path.join(output_dir, f"{Path(nc_file).stem}.bin"))
    return gmax, BAD_FILE, grid2.shape


def write_grid_files_to_rts(grid_files: List[str], rts_output_file: str):
    """
    grid_files need to be sorted in time-order
    """
    rts_unit = open(rts_output_file, 'wb')
    grid_files = sorted(grid_files)
    for grid_file in tqdm(grid_files):
        # grid = np.fromfile(grid_file, dtype=np.float32)
        grid = np.load(grid_file)['grid']
        grid.tofile(rts_unit)
    rts_unit.close()

#   fix_gpm_file_as_geotiff()
# -------------------------------------------------------------------
def create_rts_from_nc_files(nc_dir_path, temp_bin_dir, zip_file, DEM_info: dict,
                             var_name,
                             IN_MEMORY=False, VERBOSE=False):
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
    #######################################################

    # ------------------------------------------------
    # Get list of all nc files in working directory
    # ------------------------------------------------
    nc_file_list = sorted(glob.glob(join(nc_dir_path, '*.nc4')))
    if len(nc_file_list) == 0:
        # couldn't find .NC4, look for .NC
        nc_file_list = sorted(glob.glob(join(nc_dir_path, '*.nc')))

    count = 0
    bad_count = 0
    BAD_FILE = False
    #### rts_nodata = -9999.0    #################
    rts_nodata = 0.0  # (good for rainfall rates; not general)
    Pmax = -1

    # ------------------------
    # BINH: run multiprocessing
    from multiprocessing import Pool
    pool = Pool()

    # print(">>> preprocessing geotiff files")
    # nc_file_list_need_tif = [
    #     (fpath, get_tiff_file(temp_bin_dir, fpath), var_name, rts_nodata)
    #     for fpath in nc_file_list if not Path(get_tiff_file(temp_bin_dir, fpath)).exists()
    # ]
    # for _ in tqdm(pool.imap_unordered(fix_gpm_file_as_geotiff_wrap, nc_file_list_need_tif), total=len(nc_file_list_need_tif)):
    #     pass
    # print(">>> finish geotiff files")
    # ------------------------

    gmax, bad_file, shp = extract_grid_data(((temp_bin_dir, nc_file_list[0], var_name, rts_nodata, DEM_bounds, 100, 100, DEM_xres, DEM_yres, False, False)))
    assert not bad_file
    DEM_nrows, DEM_ncols = shp[0], shp[1]

    args = [
        # output_dir, nc_file, var_name, rts_nodata, DEM_bounds, DEM_nrows, DEM_ncols, DEM_xres, DEM_yres, VERBOSE, IN_MEMORY
        (temp_bin_dir, nc_file, var_name, rts_nodata, DEM_bounds, DEM_nrows, DEM_ncols, DEM_xres, DEM_yres, False, IN_MEMORY)
        for nc_file in nc_file_list
        # skip generated files
        if not os.path.exists(os.path.join(temp_bin_dir, f"{Path(nc_file).stem}.npz"))
    ]
    for gmax, bad_file, _ in tqdm(pool.imap_unordered(extract_grid_data, args), total=len(args)):
    # for gmax, bad_file in tqdm((extract_grid_data(a) for a in args), total=len(args)):
        count += 1
        Pmax = max(Pmax, gmax)
        if bad_file:
            bad_count += 1

        # -------------------------
        # Write grid to RTS file
        # -------------------------
        # grid2 = np.float32(grid2)
        # grid2.tofile(rts_unit)
        # count += 1

    # -------------------------
    # Open RTS file to write
    # -------------------------
    print(">>> write to files")
    file_name = os.path.basename(zip_file)
    rts_file = f"{temp_bin_dir}/{file_name.replace('.zip', '.rts')}"
    grid_files = sorted(glob.glob(join(temp_bin_dir, '*.npz')))
    write_grid_files_to_rts(grid_files, rts_file)

    # Generate RTI file
    rti_fname = f"{temp_bin_dir}/{file_name.replace('.zip', '.rti')}"
    generate_rti_file(rts_file, rti_fname, DEM_ncols, DEM_nrows, DEM_xres, DEM_yres, pixel_geom=0)

    print(' ')
    print('Max precip rate =', Pmax)
    print('bad_count =', bad_count)
    print('n_grids   =', count)
    print('Finished saving data to rts file and generating a matching rti file.')
    print(' ')

    print(f'Zipping {rts_file} and {rti_fname}...')
    with ZipFile(zip_file, 'w') as z:
        z.write(rts_file, os.path.basename(rts_file))
        z.write(rti_fname, os.path.basename(rti_fname))
    print(f"Zipping is complete. Please check {zip_file}")
