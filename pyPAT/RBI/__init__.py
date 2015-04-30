import arcpy, numpy
from arcpy import env
import pyPAT

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
def createOutputs(sumarr,detailarr):
    print env.scratchGDB
    arcpy.da.NumPyArrayToTable(sumarr, env.scratchGDB + r"/pout_table2")



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

    #Targets = [r"C:\pyPAT\TestData\target_polygon_habitats.shp",r"C:\pyPAT\TestData\target_line_habitats.shp",r"C:\pyPAT\TestData\target_point_species.shp"]
    #TargetsIds = ["TARGET_NAM","TARGET_NAM","TARGET_NAM"]
    #PlanningUnits = r"C:\pyPAT\TestData\tydixton_planning_units.shp"
    #PlanningUnitID = "ID"
    #GlobalArea = r"C:\pyPAT\TestData\tydixton_watershed.shp"
    #OutputLocation = r"C:\temp"

    #Targets = [r"C:\pyPAT\TestData\utm18\haiti_benth_habs_12_05_2012_wgs84.shp"]
    #TargetsIds = ["Hab_Name"]
    #PlanningUnits = r"C:\pyPAT\TestData\utm18\IAV_PUs.shp"
    #PlanningUnitID = "Unit_Id"
    #GlobalArea = r"C:\pyPAT\TestData\utm18\IAV_PUs_dissolve.shp"

    TargetRecords = zip(Targets, TargetsIds)

    TargetArrs = []
    nrecs = 0
    for TargetRec in TargetRecords:
        TargetTable = pyPAT.getTargetTable(TargetRec, (PlanningUnits, PlanningUnitID))
        TargetArrs.append(TargetTable)
        #TargetTable  = add_field(TargetTable, [('RBI','<f8')])
        #TargetTable['RBI'] = TargetTable['Amount'] / 3

        nrecs = nrecs + len(TargetTable)

    PUTable = pyPAT.getPUTable((PlanningUnits, PlanningUnitID), GlobalArea)

    noarcmapstart = datetime.datetime.now()
    totalArea = PUTable['Area'].sum()

    arr = numpy.zeros((nrecs,), dtype=[('TID',long),('PUID',TargetArrs[0]['PUID'].dtype),('Amount',float),('RBI',float),('HpArea',float),('HpPU_All',float),('HpPU_WTargets',float),('Rarity_All','b1'),('Rarity_W_Targets','b1')])

    targetSummary = generateTargetIds(TargetArrs)

    nrecs = 0
    for TargetTable in TargetArrs:
        sz = numpy.size(TargetTable)
        #join = numpy.lib.recfunctions.join_by('Target', TargetTable, targetSummary, jointype='leftouter')
        #print join
        #print join.names

        (arr["PUID"][nrecs:nrecs+sz], arr["Amount"][nrecs:nrecs+sz]) = (TargetTable["PUID"], TargetTable["Amount"])

        arr["TID"][nrecs:nrecs+sz] = pyPAT.lup(TargetTable["Target"],targetSummary)

        nrecs = nrecs + len(TargetTable)

    del TargetArrs

    PUIDic = dict(zip(PUTable["PUID"],PUTable["Area"]))
    vals = numpy.unique(arr["TID"])
    tt = numpy.size(vals)
    for val in vals:
        wind = numpy.where(arr["TID"] == val)
        rbiTOP = arr[wind]["Amount"] / arr[wind]["Amount"].sum()
        arr['RBI'][wind] = rbiTOP / (pyPAT.lup(arr[wind]["PUID"],PUIDic) / totalArea)
        arr['HpArea'][wind] = numpy.sqrt(rbiTOP) / numpy.sqrt(numpy.log(pyPAT.lup(arr[wind]["PUID"],PUIDic)) / numpy.log(totalArea))
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

    createOutputs(sumarr, arr)


if __name__ == "__main__":
    TargetList = [r"C:\pyPAT\TestData\target_polygon_habitats.shp",r"C:\pyPAT\TestData\target_line_habitats.shp",r"C:\pyPAT\TestData\target_point_species.shp"]
    TargetsIds = ["TARGET_NAM","TARGET_NAM","TARGET_NAM"]
    PlanningUnits = r"C:\pyPAT\TestData\tydixton_planning_units.shp"
    PlanningUnitID = "ID"
    GlobalArea = r"C:\pyPAT\TestData\tydixton_watershed.shp"
    OutputLocation = r"C:\temp")
    arcpyRBI(TargetList, TargetsIds, PlanningUnits, PlanningUnits, PlanningUnitID, GlobalArea, OutputLocation)
