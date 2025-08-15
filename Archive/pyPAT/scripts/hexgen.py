
import sys, string, os, time, string, math
import datetime

import arcpy
from arcpy import env

def arcpyHexgen(inputDataset, outputDataset, inputSize=1, clipInput=False, inputCount=None):

    starttime = datetime.datetime.now()

    import arcpy
    from arcpy import env

    env.overwriteOutput = True

    extentlayer = inputDataset
    output_tot = outputDataset

    desc = arcpy.Describe(extentlayer)
    sr = desc.spatialreference
    
    hexareastr = inputSize  
    hexarea = float(hexareastr) * float(10000)

    triarea = hexarea / 6
    oneside = math.sqrt((triarea * 4) / math.sqrt(3))
    halfside = oneside / 2
    onehi = math.sqrt((oneside * oneside) - ((halfside) * (halfside)))
    longway = oneside * 2
    shortway = onehi * 2

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

            featureList.append(op)

    if (clipInput):

        tmplay = "in_memory/all_hex"
        arcpy.CopyFeatures_management(featureList, tmplay)

        arcpy.MakeFeatureLayer_management(tmplay, 'hexes')
        arcpy.MakeFeatureLayer_management(extentlayer, 'extent')
        arcpy.SelectLayerByLocation_management('hexes', 'intersect', 'extent')

        arcpy.CopyFeatures_management('hexes', output_tot)

        arcpy.AddMessage("HEXGEN Complete")
        print "Complete"
    else:
        arcpy.CopyFeatures_management(featureList, output_tot)

    desc = arcpy.Describe(output_tot)

    arcpy.AddField_management(output_tot, "UNIT_ID", "LONG")
    arcpy.CalculateField_management(output_tot, "UNIT_ID", "!" + desc.OIDFieldName + "! + 1", "PYTHON")

    del desc
    del arcpy

    endtime = datetime.datetime.now()

    td = endtime - starttime

    print "Total Processing Time: ", td

def _commandline_Run():

    extentlayer = sys.argv[1]
    output_tot =  sys.argv[4]

    hexinput = sys.argv[2]

    if (True):
        inputSize = hexinput
        inputC = None
    else:
        inputSize = None
        inputC = hexinput

    clipit = sys.argv[3]

    arcpyHexgen(extentlayer, output_tot, inputSize, clipit, inputC)


if __name__ == "__main__":

    _commandline_Run()


