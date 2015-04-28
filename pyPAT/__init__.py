

_GDALOK = True
_SHPLYOK = True
_FIONAOK = True
_RRIOOK = True
_ARCOK = True
_SAOK = True

#Check for Open Source Software Packages
try:
    import gdal
    import ogr
    print "gdal/ogr imported"
except:
    print "gdal/ogr not found"
    _GDALOK = False

try:
    import shapely
    print "shapely imported"
except:
    print "shapely not found"
    _SHPLYOK = False

try:
    import fiona
    print "fiona imported"
except:
    print "fiona not found"
    _FIONAOK = False

try:
    import rasterio
    print "rasterio imported"
except:
    print "rasterio not found"
    _RRIOOK = False

#Check for Arcpy and Extentions
try:
    import arcpy
    print "arcpy imported"
except:
    print "arcpy not found"
    _ARCOK = False

if arcpy.CheckExtension("Spatial") <> "Available":
    print "No Spatial Analysit Extention Available"
    _SAOK = False


class ppSettings:
    def __init__(self):
        self.useOS = True
        print _ARCOK

defaults = ppSettings()
