# coding=utf-8
"""
!/bin/python
-*- coding: utf-8 -*
QGIS Version: QGIS 2.18

### Author ###
 S. Crommelinck, 2017

### Description ###
 This script calculates to what extent line layers overlap. This is done by buffering the line layer to be
 investigated as well as the reference line layer, overlaying both and calculating the confusion matrix. The latter is
 saved as an *.txt file and can be used as input to plot the detection and localization quality.
"""

### Import script in QGIS Python console ###
"""
# add directory with script to Python search path
import sys
sys.path.append(r"D:\path to script")

# import module
import C1_acc_ass

# rerun module after changing the source code
reload(C1_acc_ass)
"""

### Predefine variables ###
# Make sure there exists a column DN set to 1 for all features in each layer to be evaluated
data_dir = r"D:\path to directory"

# Ref_v should contain one column named DN set to 1 for all features
ref_v = r"D:\path to shapefile"

# Number of pixels in width and height of evaluation raster
raster_size = 20000

# Buffer size for input data
buff_dist = 0.05

# Buffer size for reference data
buff_ref = 0.2

# Buffer sizes for localization quality
buff_distances = "0.05,0.1,0.15,0.2"

### Import required modules ###
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.utils import *
import processing

### Main processing part ###
# Change into data directory
os.chdir(data_dir)

# List all files in current directory
files = os.listdir(os.curdir)

# Loop over all .tif files in input directory
for f in files:
    if os.path.splitext(f)[1] == '.shp':

        ### Buffering ###
        # Define output file name
        input_v_buff = os.path.splitext(f)[0] + "_buffered.shp"

        # Buffer vector
        if not os.path.isfile(input_v_buff):
            processing.runalg('qgis:fixeddistancebuffer',
                              {"INPUT": f,
                               "DISTANCE": buff_dist,
                               "SEGMENTS": 1,
                               "DISSOLVE": True,
                               "OUTPUT": input_v_buff})
            print "--> %s has been buffered with a distance of %.2f m to %s\n" % (f, buff_dist, input_v_buff)

        ### Rasterization ###
        # Read buffered layer as QGIS layer
        vlayer = QgsVectorLayer(input_v_buff, "vect", "ogr")

        # Define raster extent
        extent = vlayer.extent()
        xmin = extent.xMinimum()
        xmax = extent.xMaximum()
        ymin = extent.yMinimum()
        ymax = extent.yMaximum()

        # Define output file name
        input_r_buff = os.path.splitext(f)[0] + "_buffered.tif"

        # Run rasterization
        if not os.path.isfile(input_r_buff):
            processing.runalg('gdalogr:rasterize',
                              {"INPUT": input_v_buff,
                               "FIELD": "DN",
                               "DIMENSIONS": 0,
                               "WIDTH": raster_size,
                               "HEIGHT": raster_size,
                               "RAST_EXT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                               "OUTPUT": input_r_buff})
            print "--> %s has been rasterized to %s\n" % (input_v_buff, input_r_buff)

        #########################
        ### Detection Quality ###
        #########################
        ### Buffering of reference data ###
        # Define output file name
        ref_v_buff = str("ref_v_buffsize" + str(buff_ref) + ".shp")

        if not os.path.isfile(ref_v_buff):
            # Buffer vector
            processing.runalg('qgis:fixeddistancebuffer',
                              {"INPUT": ref_v,
                               "DISTANCE": buff_ref,
                               "SEGMENTS": 1,
                               "DISSOLVE": True,
                               "OUTPUT": ref_v_buff})
            print "--> %s has been buffered with a distance of %.2f m to %s.\n" % (ref_v, buff_ref, ref_v_buff)

        ### Rasterization ###
        # Define output file name
        ref_r_buff = str("ref_r_buffsize" + str(buff_ref) + ".tif")

        if not os.path.isfile(ref_r_buff):
            # Run rasterization
            processing.runalg('gdalogr:rasterize',
                              {"INPUT": ref_v_buff,
                               "FIELD": "DN",
                               "DIMENSIONS": 0,
                               "WIDTH": raster_size,
                               "HEIGHT": raster_size,
                               "RAST_EXT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                               "OUTPUT": ref_r_buff})
            print "--> %s has been rasterized to %s.\n" % (ref_v_buff, ref_r_buff)

        ### Kappa calculation ###
        # Define name of accuraccy assessment file
        det_quality = os.path.splitext(f)[0] + "_det_quality.txt"

        if not os.path.isfile(det_quality):
            # Run accuracy assessment (The classified result map layer categories is arranged along the vertical
            # axis of the table, while the reference map layer categories along the horizontal axis)
            processing.runalg('grass:r.kappa', {"classification": input_r_buff,
                                                "reference": ref_r_buff,
                                                "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                                                "output": det_quality})
            print "--> %s and reference layer %s have been compared for accuracy assessment. Results are stored in " \
                  "%s\n" % (input_r_buff, ref_r_buff, det_quality)

        ############################
        ### Localization Quality ###
        ############################

        ### Rasterization ###
        # Define output file name
        ref_r = str("ref_r.tif")

        if not os.path.isfile(ref_r):
            # Run rasterization
            processing.runalg('gdalogr:rasterize',
                              {"INPUT": ref_v,
                               "FIELD": "DN",
                               "DIMENSIONS": 0,
                               "WIDTH": raster_size,
                               "HEIGHT": raster_size,
                               "RAST_EXT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                               "OUTPUT": ref_r})
            print "--> %s has been rasterized to %s.\n" % (ref_v, ref_r)

        ### Buffering ###
        # Buffer rasterized reference data with distances from 0-0.5m
        ref_r_buffsizes = str("ref_r_buffsizes.tif")

        if not os.path.isfile(ref_r_buffsizes):
            processing.runalg('grass7:r.buffer',
                              {"input": ref_r,
                               "distances": buff_distances,
                               "units": 0,
                               "-z": True,
                               "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                               "GRASS_REGION_CELLSIZE_PARAMETER": 0.05,
                               "output": ref_r_buffsizes})
            print "--> %s has been buffered with distances from 0-1m to %s.\n" % (ref_r, ref_r_buffsizes)

        ### Rasterization ###
        # Define output file name
        input_r = os.path.splitext(f)[0] + ".tif"

        # Run rasterization
        if not os.path.isfile(input_r):
            processing.runalg('gdalogr:rasterize',
                              {"INPUT": f,
                               "FIELD": "DN",
                               "DIMENSIONS": 1,
                               "WIDTH": 0.05,
                               "HEIGHT": 0.05,
                               "RAST_EXT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                               "OUTPUT": input_r})
            print "--> %s has been rasterized to %s\n" % (f, input_r)

        ### Kappa calculation ###
        # Define name of accuracy assessment file
        loc_quality = os.path.splitext(f)[0] + "_loc_quality.txt"

        if not os.path.isfile(loc_quality):
            # Run accuracy assessment
            processing.runalg('grass:r.kappa', {"classification": input_r,
                                                "reference": ref_r_buffsizes,
                                                "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                                                "output": loc_quality})
            print "--> %s and reference layer %s.tif have been compared for accuracy assessment. Results are stored " \
                  "in %s\n" % (input_r, ref_r, loc_quality)

# Print final overall message
print "All processing has been finished."

"""
### Notes ###
# QGIS help

import processing
processing.alghelp("gdalogr:rasterize")
"""
