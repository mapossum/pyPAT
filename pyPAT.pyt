import arcpy
import os
import csv
from collections import defaultdict

# === HELPER FUNCTIONS ===

def create_bound_dat(planning_unit_fc, pu_id_field, output_folder, boundary_units):
    print("Generating bound.dat...")
    intersect_output = os.path.join("memory", "pu_boundaries")
    arcpy.PairwiseIntersect_analysis([planning_unit_fc, planning_unit_fc], intersect_output, "ALL", "", "LINE")

    # Add fields for id1, id2, and boundary length
    arcpy.AddField_management(intersect_output, "id1", "LONG")
    arcpy.AddField_management(intersect_output, "id2", "LONG")
    arcpy.AddField_management(intersect_output, "boundary", "DOUBLE")

    # Calculate IDs and boundary length
    with arcpy.da.UpdateCursor(intersect_output, ["{}".format(pu_id_field), "{}_1".format(pu_id_field), "id1", "id2", "SHAPE@LENGTH", "boundary"]) as cursor:
        for row in cursor:
            row[2] = row[0]
            row[3] = row[1]
            row[5] = row[4] / 1000.0 if boundary_units.upper() == "KILOMETERS" else row[4]
            cursor.updateRow(row)

    # Export to CSV
    bound_path = os.path.join(str(output_folder), "bound.dat")
    with open(bound_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id1", "id2", "boundary"])
        rows = sorted(arcpy.da.SearchCursor(intersect_output, ["id1", "id2", "boundary"]), key=lambda x: (x[0], x[1]))
        writer.writerows(rows)

def create_pu_dat(planning_unit_fc, pu_id_field, cost_field, status_field, output_folder, doPAoverlay, protected_Areas, paThreshold):
    print("Generating pu.dat...")
    pu_path = os.path.join(output_folder, "pu.dat")

    if doPAoverlay == True:
        pudis_output = os.path.join(r"memory", f"temp_pu_dis")
        pusummary = os.path.join(r"memory", f"temp_pu_summary")   
      
        arcpy.analysis.PairwiseDissolve(
            in_features=protected_Areas,
            out_feature_class=pudis_output,
            dissolve_field=None,
            statistics_fields=None,
            multi_part="MULTI_PART",
            concatenation_separator=""
        )

        arcpy.analysis.SummarizeWithin(
            in_polygons="{}".format(planning_unit_fc),
            in_sum_features="{}".format(pudis_output),
            out_feature_class=pusummary,
            keep_all_polygons="KEEP_ALL",
            sum_fields=None,
            sum_shape="ADD_SHAPE_SUM",
            shape_unit="SQUAREKILOMETERS",
            group_field=None,
            add_min_maj="NO_MIN_MAJ",
            add_group_percent="ADD_PERCENT",
            out_group_table=None
        )

        arcpy.management.CalculateGeometryAttributes(
            in_features=pusummary,
            geometry_property="SQKMAREA AREA",
            length_unit="",
            area_unit="SQUARE_KILOMETERS",
            coordinate_system=None,
            coordinate_format="SAME_AS_INPUT"
        )

        arcpy.management.CalculateField(
            in_table=pusummary,
            field="{}".format(status_field),
            expression="((!sum_Area_SQUAREKILOMETERS! / !SQKMAREA!) > {}) * 2".format(paThreshold),
            expression_type="PYTHON3",
            code_block="",
            field_type="SHORT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        pufc = pusummary
    else:
        pufc = planning_unit_fc
    
    with open(pu_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "cost", "status"])
        rows = sorted(arcpy.da.SearchCursor(pufc, [pu_id_field, cost_field, status_field]), key=lambda x: int(x[0]))
        writer.writerows(rows)

def summarize_species(planning_unit_fc, species_fc_list, pu_id_field, species_id_field, output_folder, outputTspec, feature_field, tsName, tsName_field, spf_field):
    print("Generating puvspr.dat...")
    from collections import defaultdict
    agg = defaultdict(float)
    speclist = []

    splist_list = species_fc_list.exportToString().split(';')

    for species_fc in splist_list:
        arcpy.AddMessage(species_fc)
        species_name = os.path.splitext(os.path.basename(species_fc))[0]
        desc = arcpy.Describe(species_fc)
        geom_type = desc.shapeType.upper()

        if geom_type == "POINT":
            amountf = "Point_Count"
            shapeunit = ""
        elif geom_type == "POLYLINE":
            amountf = "sum_Length_KILOMETERS"
            shapeunit = "KILOMETERS"
        elif geom_type == "POLYGON":
            amountf = "sum_Area_SQUAREKILOMETERS"
            shapeunit = "SQUAREKILOMETERS"

        if outputTspec == True:

            specFnames = ["id", "name"]
            ofields = [species_id_field,feature_field]
            #arcpy.AddMessage(tsName)
            #arcpy.AddMessage(tsName_field)
            #arcpy.AddMessage(spf_field)
            if tsName_field != "None":
                ofields.append(tsName_field)
                specFnames.append(tsName)

            if spf_field != "None":
                ofields.append(spf_field)
                specFnames.append("spf")
            
            spectemp_output = os.path.join(r"memory", f"dissolve_{species_name}")

            arcpy.analysis.Statistics(
                in_table=species_fc,
                out_table=spectemp_output,
                statistics_fields="{} FIRST".format(species_id_field),
                case_field=ofields,
                concatenation_separator=""
            )
            with arcpy.da.SearchCursor(spectemp_output, ofields) as cursor:
                for row in cursor:
                    if row[0] == None:
                        idout = 0
                        arcpy.AddWarning("*Warning Species/Features With Null Values Present*")
                        arcpy.AddMessage(str(row[0]) + ", " + str(row[1]))
                        arcpy.AddWarning("*These will most likely cause errors in the output files*")
                        nlist = []
                        nlist.append(idout)
                        nlist.append(row[1:])
                        speclist.append(nlist)
                    else:
                        speclist.append(row)

        temp_output = os.path.join(r"memory", f"summarize_{species_name}")
        tempTable_output = os.path.join(arcpy.env.scratchGDB, f"summarizeT_{species_name}")

        arcpy.analysis.SummarizeWithin(
            in_polygons=planning_unit_fc,
            in_sum_features=species_fc,
            out_feature_class=temp_output,
            keep_all_polygons="KEEP_ALL",
            sum_fields="{} Sum".format(species_id_field),
            sum_shape="ADD_SHAPE_SUM",
            shape_unit=shapeunit,
            group_field="{}".format(species_id_field),
            add_min_maj="NO_MIN_MAJ",
            add_group_percent="NO_PERCENT",
            out_group_table=tempTable_output
        )

        arcpy.management.JoinField(
            in_data=tempTable_output,
            in_field="Join_ID",
            join_table=temp_output,
            join_field="Join_ID",
            fields="{}".format(pu_id_field),
            fm_option="NOT_USE_FM",
            field_mapping=None,
            index_join_fields="NO_INDEXES"
        )

        fields = [pu_id_field, species_id_field, amountf]
        with arcpy.da.SearchCursor(tempTable_output, fields) as cursor:
            for row in cursor:
                pu_id = row[0]
                species_id = row[1]
                amount = row[2]
                if species_id is not None:
                    agg[(species_id, pu_id)] += amount

    # Write to CSV
    puvspr_path = os.path.join(output_folder, "puvspr.dat")
    with open(puvspr_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["species", "pu", "amount"])
        sorted_rows = sorted([(int(k[0]), k[1], v) for k, v in agg.items()], key=lambda x: (x[1], x[0]))
        writer.writerows(sorted_rows)

    if outputTspec == True:
        sorted_spec = sorted(speclist, key=lambda x: x[0])
        spec_path = os.path.join(output_folder, "spec.dat")
        with open(spec_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(specFnames)
            writer.writerows(sorted_spec)        

class Toolbox(object):
    def __init__(self):
        self.label = "pyPat v0.0.2"
        self.alias = "marxan_tools"
        self.tools = [GenerateMarxanFilesTool]

class GenerateMarxanFilesTool(object):
    def __init__(self):
        self.label = "Create Marxan Input Files"
        self.description = "Generates bound.dat, pu.dat, and puvspr.dat for Marxan analysis from ArcGIS feature classes."
        self.canRunInBackground = False

    def updateParameters(self, parameters):
        if parameters[0].altered and not parameters[0].hasBeenValidated:
            try:
                if parameters[7].value == False:
                    fields = [f.name for f in arcpy.ListFields(parameters[0].valueAsText)]
                    parameters[3].filter.list = fields  # This populates dropdown
                else:
                    parameters[3].filter.list = []
            except:
                parameters[3].filter.list = []
                
        if parameters[7].altered:
            if parameters[7].value == False:
                fields = [f.name for f in arcpy.ListFields(parameters[0].valueAsText)]
                parameters[3].filter.list = fields  # This populates dropdown
            else:
                parameters[3].filter.list = []
                
        return

    def getParameterInfo(self):
        # Planning Unit Feature Class
        param0 = arcpy.Parameter(
            displayName="Planning Unit Feature Class",
            name="planning_unit_fc",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polygon"]

        # PU ID Field
        param3 = arcpy.Parameter(
            displayName="Planning Unit ID Field",
            name="pu_id_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        
        param3.parameterDependencies = [param0.name]
        #param3.filter.list = ["Short","Long","Double","Float"]

        # Species Feature Classes
        param1 = arcpy.Parameter(
            displayName="Species Feature Classes",
            name="species_fc_list",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        # Cost Field
        param4 = arcpy.Parameter(
            displayName="Cost Field",
            name="cost_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")

        param4.parameterDependencies = [param0.name]

        # Status Field
        param5 = arcpy.Parameter(
            displayName="Status Field",
            name="status_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param5.parameterDependencies = [param0.name]

        # Boundary Units
        param6 = arcpy.Parameter(
            displayName="Boundary Units",
            name="boundary_units",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        param6.value = "KILOMETERS"
        param6.filter.list = ["METERS", "KILOMETERS", "MILES", "FEET", "US_SURVEY_FEET", "NAUTICAL_MILES"]

        # Do PA Overlay
        param7 = arcpy.Parameter(
            displayName="Protected Area Overlay?",
            name="doPAoverlay",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        param7.value = True

        # Protected Areas Feature Class
        param8 = arcpy.Parameter(
            displayName="Protected Areas Feature Class",
            name="protected_Areas",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param8.filter.list = ["Polygon"]

        # Protected Area Threshold
        param9 = arcpy.Parameter(
            displayName="Protected Area Threshold (0-1)",
            name="paThreshold",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        param9.value = 0.5
        
        # Output Tspec
        param10 = arcpy.Parameter(
            displayName="Output spec. file?",
            name="outputTspec",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        param10.value = True
        
        # Species ID Field
        param11 = arcpy.Parameter(
            displayName="Species ID Field",
            name="species_id_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")

        param11.parameterDependencies = [param1.name]

        # Feature Field (for Tspec.dat)
        param12 = arcpy.Parameter(
            displayName="Feature Name Field (for spec.dat)",
            name="feature_field",
            datatype="Field",
            parameterType="Optional",
            direction="Input")

        param12.parameterDependencies = [param1.name]

        # Output Folder
        param2 = arcpy.Parameter(
            displayName="Output Folder",
            name="output_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Output")

        # Parameter 1: Dropdown list for "target", "prop", or empty string
        param20 = arcpy.Parameter(
            displayName="Specify Target or Prop in spec.dat",
            name="selection_type",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )  
        # Set the default value to "prop"
        param20.value = "prop"
        param20.filter.list = [" ", "target", "prop"]

        # Species ID Field
        param21 = arcpy.Parameter(
            displayName="Prop or Target Field",
            name="prop_field",
            datatype="Field",
            parameterType="Optional",
            direction="Input")

        param21.parameterDependencies = [param1.name]

        # Species ID Field
        param22 = arcpy.Parameter(
            displayName="SPF Field",
            name="spf_field",
            datatype="Field",
            parameterType="Optional",
            direction="Input")

        param22.parameterDependencies = [param1.name]
        
        return [param0, param3, param4, param5, param1, param11, param6, param7, param8, param9, param10, param12, param20, param21, param22, param2]

    def execute(self, parameters, messages):
        """The source code of the tool."""

        arcpy.AddMessage("{0}".format(parameters[1].value))

        # === USER INPUTS ===
        planning_unit_fc = parameters[0].value #r"C:\Marxan_working\Marxan\Cost_Geo\Carib_Deep_Ocean_Features_Aug2025.gdb\pus_deep_ocean"
        #Features to summarize
        species_fc_list = parameters[4].value

        #[
        #    r"C:\Marxan_working\Marxan\Carib_Deep_Ocean_Features_Aug2025.gdb\seafloor_deep_ocean_habitats",
        #    r"C:\Marxan_working\Marxan\Carib_Deep_Ocean_Features_Aug2025.gdb\seamounts_area_depth",
        #    r"C:\Marxan_working\Marxan\Carib_Deep_Ocean_Features_Aug2025.gdb\deep_corals_sponges",
        #    r"C:\Marxan_working\Marxan\Carib_Deep_Ocean_Features_Aug2025.gdb\seafloor_rugged",
        #    r"C:\Marxan_working\Marxan\Carib_Deep_Ocean_Features_Aug2025.gdb\knolls_area_depth"
        #]

        doPAoverlay = parameters[7].value #True #status layer
        protected_Areas = parameters[8].value #r"C:\Marxan_working\Marxan\car_poli_protectedareas_2023.shp"
        paThreshold = parameters[9].value #0.5

        pu_id_field = str(parameters[1].value) #"PUID"
        cost_field = str(parameters[2].value) #"Cost"
        status_field = str(parameters[3].value) #"Status"
        species_id_field = str(parameters[5].value) #"ID"
        output_folder = str(parameters[15].value) #r"C:\Marxan_working\Marxan"
        boundary_units = parameters[6].value #"KILOMETERS"  # Default unit

        outputTspec = parameters[10].value #True
        feature_field = str(parameters[11].value) #"Feature"

        tsName = parameters[12].value
        tsName_field = str(parameters[13].value)
        spf_field = str(parameters[14].value)

        if not os.path.exists(str(output_folder)):
            os.makedirs(str(output_folder))
            
        arcpy.env.overwriteOutput = True
        create_bound_dat(planning_unit_fc, pu_id_field, output_folder, boundary_units)
        create_pu_dat(planning_unit_fc, pu_id_field, cost_field, status_field, output_folder, doPAoverlay, protected_Areas, paThreshold)
        summarize_species(planning_unit_fc, species_fc_list, pu_id_field, species_id_field, output_folder, outputTspec, feature_field, tsName, tsName_field, spf_field)

        print("All MARXAN input files generated successfully.")

        return



