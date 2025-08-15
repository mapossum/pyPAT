import arcpy, numpy
from arcpy import env
#import __init__ as pyPAT
import datetime, sys
import numpy.lib.recfunctions

env.overwriteOutput = True

def generateTargetIds(TargetArrs):
    outdic = {}
    x = 0
    for TargetTable in TargetArrs:
        valstoadd = numpy.unique(TargetTable["Target"])
        for val in valstoadd:
            x = x + 1
            outdic[val] = x
    return outdic

#def createOutputs(PAs,OuputLocation,sumarr,detailarr):
def createOutputs(sumarr,detailarr, OutputLocation):
    if (OutputLocation[-4:] == ".dbf"):
        OutputLocation2 = OutputLocation[:-4] + "_detail.dbf"
    else:
        OutputLocation2 = OutputLocation + "_detail"
    arcpy.da.NumPyArrayToTable(sumarr, OutputLocation)
    arcpy.da.NumPyArrayToTable(detailarr, OutputLocation2)


def findRare(a):
    if a > 1:
        return 1
    else:
        return 0

isRare = numpy.vectorize(findRare)


#### SET INPUTS
def arcpyRBI(Targets, TargetsIds, PlanningUnits, PlanningUnitsID, GlobalArea, OutputLocation):
    if (arcpy.env.scratchGDB == ""):
        print "Please set the scratch workspace"
        return

    TargetRecords = zip(Targets, TargetsIds)

    TargetArrs = []
    nrecs = 0
    for TargetRec in TargetRecords:
        TargetTable = getTargetTable(TargetRec, (PlanningUnits, PlanningUnitID))
        TargetArrs.append(TargetTable)
        #TargetTable  = add_field(TargetTable, [('RBI','<f8')])
        #TargetTable['RBI'] = TargetTable['Amount'] / 3

        nrecs = nrecs + len(TargetTable)

    PUTable = getPUTable((PlanningUnits, PlanningUnitID), GlobalArea)

    noarcmapstart = datetime.datetime.now()
    totalArea = PUTable['Area'].sum()

    arr = numpy.zeros((nrecs,), dtype=[('TID',long),('Target', TargetArrs[0]['Target'].dtype),('PUID',TargetArrs[0]['PUID'].dtype),('Amount',float),('RBI',float),('HpArea',float),('HpPU_All',float),('HpPU_WTargets',float),('Rarity_All','b1'),('Rarity_W_Targets','b1')])

    targetSummary = generateTargetIds(TargetArrs)

    nrecs = 0
    for TargetTable in TargetArrs:
        sz = numpy.size(TargetTable)
        #join = numpy.lib.recfunctions.join_by('Target', TargetTable, targetSummary, jointype='leftouter')
        #print join
        #print join.names
        arr["Target"][nrecs:nrecs+sz] = TargetTable["Target"]
        
        (arr["PUID"][nrecs:nrecs+sz], arr["Amount"][nrecs:nrecs+sz]) = (TargetTable["PUID"], TargetTable["Amount"])

        arr["TID"][nrecs:nrecs+sz] = lup(TargetTable["Target"],targetSummary)
        
        nrecs = nrecs + len(TargetTable)

    del TargetArrs
    
    PUIDic = dict(zip(PUTable["PUID"],PUTable["Area"]))
    vals = numpy.unique(arr["TID"])
    tt = numpy.size(vals)
    for val in vals:
        wind = numpy.where(arr["TID"] == val)
        rbiTOP = arr[wind]["Amount"] / arr[wind]["Amount"].sum()
        arr['RBI'][wind] = rbiTOP / (lup(arr[wind]["PUID"],PUIDic) / totalArea)
        arr['HpArea'][wind] = numpy.sqrt(rbiTOP) / numpy.sqrt(numpy.log(lup(arr[wind]["PUID"],PUIDic)) / numpy.log(totalArea))
        arr['HpPU_All'][wind] = numpy.sqrt(rbiTOP) / math.sqrt(float(numpy.size(arr[wind])) / float(numpy.size(PUTable["PUID"])))
        arr['HpPU_WTargets'][wind] = numpy.sqrt(rbiTOP) / math.sqrt(float(numpy.size(arr[wind])) / float(numpy.size(numpy.unique(arr["PUID"]))))

        #numpy.sqrt(rbiTOP) / numpy.sqrt(numpy.size(arr[wind]) / numpy.size(PUTable["PUID"]))

    arr['Rarity_All'] = isRare(arr['HpPU_All'])
    arr['Rarity_W_Targets'] = isRare(arr['HpPU_WTargets'])

    vals = numpy.unique(arr["PUID"])
    sumarr = numpy.zeros((numpy.size(vals),), dtype=[('PUID',arr['PUID'].dtype),('tRBI',float),('nt1RBI',float),('nt2RBI',float),('tHpArea',float),('tHpPU_All',float),('tHpPU_WTargets',float),('nt1HpArea',float),('nt1HpPU_All',float),('nt1HpPU_WTargets',float),('nt2HpArea',float),('nt2HpPU_All',float),('nt2HpPU_WTargets',float),('Rarity_All',long),('Rarity_W_Targets',long)])

    sumarr["PUID"] = vals

    for val in vals:
        awind = numpy.where(arr["PUID"] == val)
        swind = numpy.where(sumarr["PUID"] == val)
        rbit = arr["RBI"][awind].sum()
        tpu = float(numpy.size(arr[awind]))
        sumarr["tRBI"][swind] = rbit
        sumarr["nt1RBI"][swind] = rbit / float(tt)
        sumarr["nt2RBI"][swind] = rbit / tpu

        sumarr["tHpArea"][swind] = arr["HpArea"][awind].sum()
        sumarr["tHpPU_All"][swind] = arr["HpPU_All"][awind].sum()
        sumarr["tHpPU_WTargets"][swind] = arr["HpPU_WTargets"][awind].sum()

        sumarr["nt2HpArea"][swind] = sumarr["tHpArea"][swind] / tpu
        sumarr["nt2HpPU_All"][swind] = sumarr["tHpPU_All"][swind] / tpu
        sumarr["nt2HpPU_WTargets"][swind] = sumarr["tHpPU_WTargets"][swind] / tpu

        sumarr["Rarity_All"][swind] = arr["Rarity_All"][awind].sum()
        sumarr["Rarity_W_Targets"][swind] = arr["Rarity_W_Targets"][awind].sum()

    sumarr["nt1HpArea"] = sumarr["tHpArea"] / float(tt)
    sumarr["nt1HpPU_All"] = sumarr["tHpPU_All"] / float(tt)
    sumarr["nt1HpPU_WTargets"] = sumarr["tHpPU_WTargets"] / float(tt)

    noarcmapend = datetime.datetime.now()

    td = noarcmapend - noarcmapstart

    print "Non-ArcMap Processing Time: ", td

    createOutputs(sumarr, arr, OutputLocation)

def add_field(a, descr):
    if a.dtype.fields is None:
        raise ValueError, "`A' must be a structured numpy array"
    b = numpy.empty(a.shape, dtype=a.dtype.descr + descr)
    for name in a.dtype.names:
        b[name] = a[name]
    return b

def getTimeStamp():
    ptime = datetime.datetime.now()
    timestamp =  str(ptime)
    timestamp = timestamp.replace("-"," ").replace(":"," ").replace("."," ").replace(" ","")[:17]
    return timestamp

def getTargetTable(inTarget,inPUs):
    #### Intersect Target with PU
    intersectedOutput = env.scratchGDB + r"\TARI_" + getTimeStamp()
    arcpy.Intersect_analysis([inTarget[0],inPUs[0]], intersectedOutput)

    #### Dissolve Output of Intersect
    DissolveOutput = env.scratchGDB + r"\TARD_" + getTimeStamp()
    dissolveFields = [inTarget[1],inPUs[1]]
    arcpy.Dissolve_management(intersectedOutput, DissolveOutput, dissolveFields, "", "MULTI_PART")

    desc = arcpy.Describe(DissolveOutput)

    if (desc.shapeType == "Polygon"):
        calval = '!shape.area!'
    elif (desc.shapeType == "Polyline"):
        calval = '!shape.length!'
    else:
        calval = '!shape.partCount!'


    arcpy.AddField_management(DissolveOutput, "Amount", "DOUBLE")

    arcpy.CalculateField_management(DissolveOutput, "Amount",calval,"PYTHON")

    arr = arcpy.da.FeatureClassToNumPyArray(DissolveOutput, (inTarget[1], inPUs[1], 'Amount'))

    if (arr.dtype.names[0] == inTarget[1]):
        arr.dtype.names = ('Target', 'PUID', 'Amount')
    else:
        arr.dtype.names = ('PUID', 'Target', 'Amount')

    return arr

def getPUTable(inPUs,gbl):
    intersectedOutput = env.scratchGDB + r"\PUI_" + getTimeStamp()
    arcpy.Intersect_analysis([gbl,inPUs[0]], intersectedOutput)

    DissolveOutput = env.scratchGDB + r"\PUD_" + getTimeStamp()
    dissolveFields = [inPUs[1]]
    arcpy.Dissolve_management(intersectedOutput, DissolveOutput, dissolveFields, "", "MULTI_PART")

    arr = arcpy.da.FeatureClassToNumPyArray(DissolveOutput, (inPUs[1], 'Shape_Area'))

    arr.dtype.names = ('PUID', 'Area')

    return arr

def lookup(a,indic):
    return indic[a]

lup = numpy.vectorize(lookup)


if __name__ == "__main__":

    firstTarget = sys.argv[1]
    oTargets = sys.argv[2]

    if (oTargets == "#"):
        targets = []
    else:
        targets = oTargets.split(";")

    targets.append(firstTarget)

    tids = []
    for target in targets:
        tids.append(sys.argv[3])

    TargetList = targets
    TargetsIds = tids 
    PlanningUnits = sys.argv[4]
    PlanningUnitID = sys.argv[5]
    GlobalArea = sys.argv[6]
    OutputLocation = sys.argv[7] 
    arcpyRBI(TargetList, TargetsIds, PlanningUnits, PlanningUnitID, GlobalArea, OutputLocation)
