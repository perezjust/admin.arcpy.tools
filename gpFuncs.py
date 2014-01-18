'''Create code re-use library for ArcGIS stuff

    regular class methods take self as the first argument

    class variables shares the data across all instances

    class method (@classmethod above the def statement)can be used to construct python classes in differing ways.  A @classmethod def
    for each constuctor need should use the return cls(parameter) statement to allow the construction of the subclass

    if my class functions don't use self in the logic, it is quite probable that it should be a @staticmethod that needs to
    know nothing about a instance of a class but putting it in the class definition can help users find the method if that's appropriate

    class local method is the dunder method

    @property

    flyweight design pattern supresses the instance dictionary by using __slots__ which don't inherit dict
'''

import arcpy
import os
import string
import sys
import traceback
from os.path import join

sys.path.append(r"\\192.168.201.11\gis\Users\Justin_Perez\EXPTools\Scripts")
import expFuncs as eF
from expFuncs import *


class featureLayer(object):
    '''
    Create a feature class object for arcpy stuff

    '''

    version = '0.1'

    import arcpy

    def __init__(self, path):
        '''Instance variables that would be unique to an instance of featureLayer'''
        self.path = path
        self.shapeType = featureLayer.shapeType(path)
        self.desc = arcpy.Describe(path)
        self.name = self.desc.name
        self.catalog_path = self.desc.catalogPath
        self.spatial_reference = self.desc.spatialReference
        self.oidfieldname = self.desc.OIDFieldName
        self.shapefieldname = self.desc.shapeFieldName
        self.fieldlist = self.desc.fields
        #self.featLyr = featureLayer.makeFeatureLayer(self, loseglobalid)

    def makeFeatureLayer(self, loseglobalid=None):
        #print arcpy.env.workspace
        fieldInfo = arcpy.describe(self.path).fieldInfo
        featLyr = arcpy.CreateUniqueName("featLyr", "in_memory")
        #print featLyr
        if loseglobalid is not None:
            print "lose my globalid!"
        arcpy.MakeFeatureLayer_management(self.path, featLyr, "#", "#", fieldInfo)
        return featLyr

    @staticmethod
    def shapeType(path):
        desc = arcpy.Describe(path)
        return desc.ShapeType

    def intersect(self, intersectFeatLayerPath, intersecttype=None, wkspace=None):
        '''
            return path of derived file
        '''
        if wkspace == None:
            wkspace = "in_memory"
        try:
            arcpy.MakeFeatureLayer_management(self.path, "selfIntersect")
            arcpy.MakeFeatureLayer_management(intersectFeatLayerPath, "not_self")
            inFCs = ["selfIntersect", "not_self"]
            if wkspace == "in_memory":
                intersected = arcpy.CreateUniqueName("intersected", wkspace)
            else:
                intersected = arcpy.CreateUniqueName("intersected.shp", wkspace)
            arcpy.AddMessage(intersected)
            arcpy.Intersect_analysis(inFCs, intersected, "#", "#", intersecttype)
            arcpy.Delete_management("selfIntersect")
            arcpy.Delete_management("not_self")
        except:
            print traceback.format_exc()

        return intersected

    def iterateFeatures(self):
        desc = arcpy.Describe(self.path)
        if desc.hasOID == 1:
            oidField = desc.OIDFieldName
            scur = arcpy.SearchCursor(self.path)
            for srow in scur:
                objId = str(srow.getValue(oidField))
                sql = '"' + oidField + '"' + " = " + objId

    def count(self):
        return int(arcpy.GetCount_management(self.path).getOutput(0))

    def addGUIDField(self):
        import uuid
        codeBlock = '''import uuid
def CalcGUIDO():
    x = uuid.uuid4()
    return '{' + str(x) + '}'
                    '''
        arcpy.AddField_management(self.path, "GUID_O", "Text", "", "")
        arcpy.CalculateField_management(self.path, "GUID_O", "CalcGUIDO()", "PYTHON_9.3", codeBlock)

    def makeQueryListUnique(self, field):
        if len(arcpy.ListFields(self.path, field)) == 0:
            arcMessage("No field called: " + field + ".  function makeQueryListUnique is breaking.")
            return
        queryList=[]
        scur=arcpy.SearchCursor(self.path)
        for row in scur:
            val = row.getValue(field)
            if val not in queryList:
                queryList.append(val)
        return queryList

    def makeSQLFeatureLayer(self, field, value):
        featLyr = arcpy.CreateUniqueName("featLyr", "in_memory")
        sql = '"' + field + '"' + " = " + "'" + value + "'"
        arcpy.MakeFeatureLayer_management(self.path, featLyr, sql)
        return featLyr

    def create_route(self, measlinename, routefield, coordpriority=None):
        '''This should only be used for simple lines'''
        if self.shapeType == "Polyline":
            measlinenamelyr = arcpy.CreateUniqueName(measlinename, "in_memory")
            print coordpriority
            if coordpriority == None:
                coordpriority = "UPPER_RIGHT"
            arcpy.CreateRoutes_lr(self.path, routefield, measlinenamelyr, "LENGTH", "", "", coordpriority, 1)
            return measlinenamelyr

    def getfieldlist(self, returnNames=None):
        fields = arcpy.ListFields(self.path)
        if returnNames == 1:
            fldnamelist = []
            for fld in fields:
                fldnamelist.append(fld.name)
            return fldnamelist
        else:
            return fields

##    def addfield(self, fieldname, fieldtype, precision=none, scale=none):
##        if len(arcpy.ListFields(self.path, fieldname)) == 0:
##            arcpy.AddField_management(self.path, fieldname, fieldtype, "", "")


    def cursor_to_dicts(self):
        '''
        yields a generator of a dict, so once this object
        is iterated through it will be empty
        '''
        fieldlist_with_shapetoken = featureLayer.cursor_field_parameter_helper(self, "SHAPE@")
        cursor = arcpy.da.SearchCursor(self.path, fieldlist_with_shapetoken)
        for row in cursor:
            row_dict = {}
            for field in fieldlist_with_shapetoken:
                if field == "SHAPE@":
                    val = row[featureLayer.get_field_index(self, field, fieldlist_with_shapetoken)]
                else:
                    val = row[featureLayer.get_field_index(self, field)]
                row_dict[field] = getattr(val, '__geo_interface__', val)
            yield row_dict


    def cursor_field_parameter_helper(self, special_cursor_token):
        cursor_field_list = []
        for i in self.fieldlist:
            cursor_field_list.append(str(i.name))
        cursor_field_list.append(special_cursor_token)
        return cursor_field_list



    def get_field_index(self, field_name, helper_field_list=None):
        count = 0
        if helper_field_list == None:
            for i in self.fieldlist:
                if i.name == field_name:
                    return count
                count += 1
        else:
            for i in helper_field_list:
                if i == field_name:
                    return count
                count += 1


    def set_gp_workspace(self, setworkspace):
        if setworkspace == None:
            gp_workspace = "in_memory"
        else:
            gp_workspace = setworkspace
        return gp_workspace


    def feature_vertices_to_points(self, workspace=None):
        setworkspace = featureLayer.set_gp_workspace(self, workspace)
        arcpy.env.workspace = setworkspace
        featVerticesPnts = arcpy.CreateUniqueName("featVerticesPnts", setworkspace)
        try:
            arcpy.CreateFeatureclass_management(os.path.dirname(featVerticesPnts), os.path.basename(featVerticesPnts), "POINT", self.path, "#", "#", self.path)
            cursor_list = list(featureLayer.cursor_to_dicts(self))#check out the comments on cursor_to_dicts
            icur_field_param_list = []
            for icur_field in cursor_list[0].keys():
                icur_field_param_list.append(icur_field)


            with arcpy.da.InsertCursor(featVerticesPnts,  icur_field_param_list) as icur:
                for feature_row_dicts in cursor_list:
                    shapes_dicts = feature_row_dicts["SHAPE@"]
                    for coords_tup in shapes_dicts["coordinates"]:
                        for coords in coords_tup:
                            coords_list = str(coords)[1:-1].split(",")
                            insert_param_list = []
                            insert_point = arcpy.Point()
                            insert_point.X = coords_list[0]
                            insert_point.Y = coords_list[1]
                            pointGeom = arcpy.PointGeometry(insert_point)
                            for insert_value_key in icur_field_param_list:
                                if insert_value_key == self.shapefieldname:
                                    insert_param_list.append(coords)
                                elif insert_value_key == "SHAPE@":
                                    insert_param_list.append(pointGeom)
                                else:
                                    insert_param_list.append(feature_row_dicts[insert_value_key])
                            arcpy.AddMessage(insert_param_list)
                            icur.insertRow(insert_param_list)


        except:
            arcpy.AddMessage(traceback.format_exc())
            print traceback.format_exc()

        return featVerticesPnts


    def featureVerticesToPoints(self, featureid, workspace=None, first_and_last=None, mark_ordinal=None):
        if workspace == None:
            setworkspace = "in_memory"
        else:
            setworkspace = workspace
        arcpy.env.workspace = setworkspace
        featVerticesPnts = arcpy.CreateUniqueName("featVerticesPnts", setworkspace)
        arcpy.AddMessage(featVerticesPnts)
        try:
            arcpy.CreateFeatureclass_management(os.path.dirname(featVerticesPnts), os.path.basename(featVerticesPnts), "POINT", "#", "#", "#", self.path)
            outputFields = arcpy.ListFields(featVerticesPnts)
            inPolylineRows = arcpy.SearchCursor(self.path)
            arcpy.AddField_management(featVerticesPnts, featureid, "Text", "", "")
            outPointRows = arcpy.InsertCursor(featVerticesPnts)
            for inPolylineRow in inPolylineRows:
                    inPolyline =  inPolylineRow.getValue(arcpy.Describe(featVerticesPnts).shapeFieldName)
                    infeatureid = inPolylineRow.getValue(featureid)
                    partCount = inPolyline.partCount
                    partNum = 0
                    while partNum < partCount:
                            pntArray = inPolyline.getPart(partNum)
                            pntCount = pntArray.count
                            pntNum = 0
                            if first_and_last == "true":
                                arcpy.AddField_management(featVerticesPnts, "Ordinal", "Text", "", "")
                                for iPntCount in range(0, pntCount):
                                    arcpy.AddMessage(str(pntNum) + " " + str(pntCount))
                                    if pntNum == 0 or pntNum + 1 == pntCount:
                                        arcpy.AddMessage(pntNum)
                                        outPointRow = outPointRows.newRow()
                                        outPointRow.setValue("Shape", pntArray.getObject(pntNum))
                                        outPointRow.setValue(featureid, infeatureid)
                                        if pntNum == 0:
                                            outPointRow.setValue("Ordinal", "Start")
                                        elif pntNum + 1 == pntCount:
                                            outPointRow.setValue("Ordinal", "End")
    ##                                    for field in outputFields:
    ##                                            if field.type <> "Geometry" and field.type <> "OID":
    ##                                                    outPointRow.setValue(field.name, inPolylineRow.getValue(field.name))
                                        outPointRows.insertRow(outPointRow)
                                    pntNum = pntNum + 1
                            else:
                                while pntNum < pntCount:
                                    outPointRow = outPointRows.newRow()
                                    outPointRow.setValue("Shape", pntArray.getObject(pntNum))
                                    outPointRow.setValue(featureid, infeatureid)
##                                    for field in outputFields:
##                                            if field.type <> "Geometry" and field.type <> "OID":
##                                                    outPointRow.setValue(field.name, inPolylineRow.getValue(field.name))

                                    outPointRows.insertRow(outPointRow)
                                    pntNum = pntNum + 1
                            partNum = partNum + 1
        except:
            arcpy.AddMessage(traceback.format_exc())
        return featVerticesPnts




def make_table_querylist_unique(fc, field):
    if len(arcpy.ListFields(fc, field)) == 0:
        arcMessage("No field called: " + field + ".  function makeQueryListUnique is breaking.")
        return
    queryList=[]
    scur=arcpy.da.SearchCursor(fc, str(field))
    for row in scur:
        val = row[0]
        if val not in queryList:
            queryList.append(val)
    return queryList



class ESRI_DBBrowser(object):
    import arcpy

    def __init__(self, path):
        self.path = path
        #this does nothing right now
        desc = arcpy.Describe(path)
        dbtype = desc.workspaceFactoryProgID
        if dbtype == "esriDataSourcesGDB.SdeWorkspaceFactory.1":
            print "sde"
        self.dbname = arcpy.Describe(path).connectionProperties.database

    def exporttofolder(self, folder, fclist=None):
        if not os.path.exists(folder):
            os.mkdir(folder)
        if not os.path.exists(join(folder, self.dbname)):
            os.mkdir(join(folder, self.dbname))
        if fclist is None:
            fclist = self.build_db_catalog()
        print fclist
        for fc in fclist:

            fcname = arcpy.Describe(fc).name.split(".")[-1]
            print fcname
            destination = ""
            #the feature class does not reside in a feature dataset
            if os.path.dirname(fc) == os.path.basename(self.path):
                destination = join(folder, self.dbname)
            else:
                datasetname = arcpy.Describe(os.path.dirname(fc)).name.split(".")[-1]
                destination = join(folder, self.dbname, datasetname)
            if not os.path.exists(destination):
                os.mkdir(destination)
            print destination
            arcpy.CopyFeatures_management(fc, join(destination, fcname))

    def build_db_catalog(self):
        featureclasslist = []
        arcpy.env.workspace = self.path
        for fc in arcpy.ListFeatureClasses():
            #print arcpy.Describe(fc).catalogPath
            #print join(self.path, fc)
            featureclasslist.append(join(self.path, fc))
        del(fc)
        for ds in arcpy.ListDatasets():
            arcpy.env.workspace = join(self.path, ds)
            #dataset_name = ds.split(".")[-1]
            for fc in arcpy.ListFeatureClasses():
                featureclasslist.append(join(join(self.path, ds), fc))
        return featureclasslist

    def iterfeaturedataset(self, dataset):
        featureclasslist = []
        arcpy.env.workspace = join(self.path, dataset)
        for fc in arcpy.ListFeatureClasses():
            featureclasslist.append(fc)
        return featureclasslist



class ESRI_FolderBrowser(object):
    import arcpy

    def __init__(self, path):
        self.path = path
        #this does nothing right now
        desc = arcpy.Describe(path)
        workspacetype = desc.workspaceType
        if workspacetype == "FileSystem":
            print "File System"

    def build_fs_catalog(self):
        featureclasslist = []
        folder = str(self.path)
        arcpy.env.workspace = self.path
        for root,dir,files in os.walk(folder):
            filelist = [ os.path.join(root,fi) for fi in files if fi.endswith(".shp")]
            for f in filelist:
                    featureclasslist.append(f)
        return featureclasslist

























