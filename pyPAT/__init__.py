import logging
#argparse

logger = logging.getLogger('pyPAT')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

#Setup Global Settings Variables
_GDALOK = True
_SHPLYOK = True
_FIONAOK = True
_RRIOOK = True
_ARCOK = True
_SAOK = True
_MPLOK = False
_NUMPYOK = False
_SCIPYOK = False

#Check for Open Source Software Packages
try:
    import gdal
    import ogr
    logger.info("gdal/ogr present")
except:
    logger.warning("gdal/ogr not found")
    _GDALOK = False

try:
    import shapely
    logger.info("shapely present")
except:
    logger.warning("shapely not found")
    _SHPLYOK = False

try:
    import fiona
    logger.info("fiona present")
except:
    logger.warning("fiona not found")
    _FIONAOK = False

try:
    import rasterio
    logger.info("rasterio present")
except:
    logger.warning("rasterio not found")
    _RRIOOK = False

try:
    import matplotlib
    logger.info("matplotlib present")
except:
    logger.warning("matplotlib not found")
    _MPLOK = False

try:
    import numpy
    logger.info("numpy present")
except:
    logger.warning("numpy not found")
    _NUMPYOK = False

try:
    import scipy
    logger.info("scipy present")
except:
    logger.warning("scipy not found")
    _SCIPYOK = False

#Check for Arcpy and Extentions
try:
    import arcpy
    logger.info("arcpy present")
except:
    logger.warning("arcpy not found")
    _ARCOK = False

if arcpy.CheckExtension("Spatial") <> "Available":
    logger.warning("No Spatial Analysit Extention Available")
    _SAOK = False
else:
    logger.info("spatial analyst present")


class ppSettings:
    def __init__(self):
        self._GDALOK = _GDALOK
        self._SHPLYOK = _SHPLYOK
        self._FIONAOK = _FIONAOK
        self._RRIOOK = _RRIOOK
        self._MPLOK = _MPLOK
        self._NUMPYOK = _NUMPYOK
        self._SCIPYOK = _SCIPYOK
        self._ARCOK = _ARCOK
        self._SAOK = _SAOK
        #self.useOS = True


defaults = ppSettings()
