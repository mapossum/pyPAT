from .. import defaults
print defaults.useOS

def osHexgen(inputDataset, outputDataset, inputSize=0, clipInput=False, inputCount=None):
    pass

def arcpyHexgen(inputDataset, outputDataset, inputSize=0, clipInput=False, inputCount=None):
    pass


def hexgen(inputDataset, outputDataset, inputSize=0, clipInput=False, inputCount=None, force=None):
    pass



# Import system modules
import sys, string, os, time, string, math
from osgeo import ogr
import datetime

starttime = datetime.datetime.now()

extentlayer = r'D:\dev\pyPAT_folder\TestData\tydixton_watershed.shp' #sys.argv[1]
output_tot =  r"D:\dev\shape88.shp"
hexareastr = 2  #sys.argv[3]
hexarea = float(hexareastr) * float(10000)

triarea = hexarea / 6
oneside = math.sqrt((triarea * 4) / math.sqrt(3))
halfside = oneside / 2
onehi = math.sqrt((oneside * oneside) - ((halfside) * (halfside)))
longway = oneside * 2
shortway = onehi * 2

#Find Extents
inDriver = ogr.GetDriverByName("ESRI Shapefile")
extentFC = inDriver.Open(extentlayer, 0)
inLayer = extentFC.GetLayer()
extent = inLayer.GetExtent()

print extent

minx = extent[0]
miny = extent[2]
maxx = extent[1]
maxy = extent[3]
xrange = maxx - minx
yrange = maxy - miny

# Create the output shapefile
outDriver = ogr.GetDriverByName("ESRI Shapefile")
outDataSource = outDriver.CreateDataSource(output_tot)
outLayer = outDataSource.CreateLayer("shape", geom_type=ogr.wkbPolygon)

inLayerDefn = inLayer.GetLayerDefn()
for i in range(0, inLayerDefn.GetFieldCount()):
    fieldDefn = inLayerDefn.GetFieldDefn(i)
    outLayer.CreateField(fieldDefn)

extentFC.Destroy()

outLayerDefn = outLayer.GetLayerDefn()

distancex = oneside + halfside
distancey = shortway

th = int((xrange + longway + oneside + 0.02) / distancex)* int((yrange + shortway + shortway) / distancey)
oum = str(th) + " Will Cover the Extent Area"
print oum

featureList = []

for xc in range(int((xrange + longway + oneside + 0.02) / distancex)):
    centerx = (minx + (xc * distancex)) - 0.01
    if (xc%10) == 0:
        print "    On row " + str(xc) + " of " + str(int((xrange + shortway) / distancex))
    if (xc%2) == 0:
        ystart = miny
    else:
        ystart = miny - onehi
    for yc in range(int((yrange + shortway + shortway) / distancey)):
        centery = ystart + (yc * distancey)
        #Hex Generation

        ring = ogr.Geometry(ogr.wkbLinearRing)

        ring.AddPoint(centerx + halfside, centery + onehi)
        ring.AddPoint(centerx + oneside, centery)
        ring.AddPoint(centerx + halfside, centery - onehi)
        ring.AddPoint(centerx - halfside, centery - onehi)
        ring.AddPoint(centerx - oneside, centery)
        ring.AddPoint(centerx - halfside, centery + onehi)
        ring.AddPoint(centerx + halfside, centery + onehi)

        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)

        outFeature = ogr.Feature(outLayerDefn)
        outFeature.SetGeometry(poly)
        outLayer.CreateFeature(outFeature)

        #print poly.ExportToWkt()

outDataSource.Destroy()

endtime = datetime.datetime.now()

td = endtime - starttime

print "Total Processing Time: ", td


















# Create an empty Geometry object
#
#g = arcpy.Geometry()

# Run the CopyFeatures tool, setting the output to the geometry object.  GeometryList
#  is returned as a list of geometry objects.
#
#geometryList = arcpy.CopyFeatures_management(r"C:\pyPAT\TestData\tydixton_planning_units.shp", g)

#print type(geometryList)


# Import system modules
import sys, string, os, time, string, math, arcpy
from arcpy import env
import datetime

starttime = datetime.datetime.now()

env.overwriteOutput = True

extentlayer = r'D:\dev\pyPAT_folder\TestData\tydixton_watershed.shp' #sys.argv[1]
output_tot =  env.scratchGDB + r"/outputhex"  #sys.argv[2]
hexareastr = 0.05  #sys.argv[3]
hexarea = float(hexareastr) * float(10000)

triarea = hexarea / 6
oneside = math.sqrt((triarea * 4) / math.sqrt(3))
halfside = oneside / 2
onehi = math.sqrt((oneside * oneside) - ((halfside) * (halfside)))
longway = oneside * 2
shortway = onehi * 2

desc = arcpy.Describe(extentlayer)
sr = desc.spatialreference

minx = desc.extent.XMin
miny = desc.extent.YMin
maxx = desc.extent.XMax
maxy = desc.extent.YMax
xrange = maxx - minx
yrange = maxy - miny

distancex = oneside + halfside
distancey = shortway

th = int((xrange + longway + oneside + 0.02) / distancex)* int((yrange + shortway + shortway) / distancey)
oum = str(th) + " Will Cover the Extent Area"
print oum
arcpy.AddMessage(oum)
arcpy.AddMessage("Generating Hexagons...")

featureList = []

for xc in range(int((xrange + longway + oneside + 0.02) / distancex)):
    centerx = (minx + (xc * distancex)) - 0.01
    if (xc%10) == 0:
        arcpy.AddMessage("    On row " + str(xc) + " of " + str(int((xrange + shortway) / distancex)))
        print "    On row " + str(xc) + " of " + str(int((xrange + shortway) / distancex))
    if (xc%2) == 0:
        ystart = miny
    else:
        ystart = miny - onehi
    for yc in range(int((yrange + shortway + shortway) / distancey)):
        centery = ystart + (yc * distancey)
        #Hex Generation
        gonarray = arcpy.Array()

        pt1 = arcpy.Point()
        pt1.X = centerx + halfside
        pt1.Y = centery + onehi
        gonarray.add(pt1)

        pt2 = arcpy.Point()
        pt2.X = centerx + oneside
        pt2.Y = centery
        gonarray.add(pt2)

        pt3 = arcpy.Point()
        pt3.X = centerx + halfside
        pt3.Y = centery - onehi
        gonarray.add(pt3)

        pt4 = arcpy.Point()
        pt4.X = centerx - halfside
        pt4.Y = centery - onehi
        gonarray.add(pt4)

        pt5 = arcpy.Point()
        pt5.X = centerx - oneside
        pt5.Y = centery
        gonarray.add(pt5)

        pt6 = arcpy.Point()
        pt6.X = centerx - halfside
        pt6.Y = centery + onehi
        gonarray.add(pt6)

        pt7 = arcpy.Point()
        pt7.X = centerx + halfside
        pt7.Y = centery + onehi
        gonarray.add(pt7)

        op = arcpy.Polygon(gonarray, sr)
        gonarray.removeAll()

##        featureList.append(op)
##
##tmplay = "in_memory/all_hex" #env.scratchGDB + r"/all_hex"
##arcpy.CopyFeatures_management(featureList, tmplay)
##
##arcpy.MakeFeatureLayer_management(tmplay, 'hexes')
##arcpy.MakeFeatureLayer_management(extentlayer, 'extent')
##arcpy.SelectLayerByLocation_management('hexes', 'intersect', 'extent')
##
##arcpy.CopyFeatures_management('hexes', output_tot)
##
###gp.calculatefield_management(output_tot, "UNIT_ID", "[" + oidnam + "] + 1")
arcpy.AddMessage("HEXGEN Complete")
print "Complete"

del desc
del arcpy

endtime = datetime.datetime.now()

td = endtime - starttime

print "Total Processing Time: ", td
