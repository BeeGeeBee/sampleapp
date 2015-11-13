import csv
from sqlalchemy.sql import func
from models import Components, Base, Locations, Suppliers, Categories, Definitions, Features,\
    DefinedFeatures
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound


__author__ = 'Bernard'
"""
componentsmodule to access data, load data etc in components database
"""

ERRNoFileName = 1
ERRFileNotFound = 2
ERRInvalidTitle = 3
ERRInvalidNumCols = 4
ERRSublocBeforeLoc = 5
ERRValueBeforeFeature = 6
ERRNoNameCol = 7


def createdbsession(dbname=None, sqlecho=None, cleardown=False):
    engine = create_engine(dbname, echo=sqlecho, poolclass=NullPool)
    Base.metadata.bind = engine

    dbsession = sessionmaker()
    dbsession.bind = engine
    session = dbsession()
    # Add the schema
    # If cleardown then drop all first
    if cleardown:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return session


def getnextid(session, qry):
    """
    Get the next ID value.
    :param session: Database session object.
    :param qry: ORM query object to get the ID
    :return: Return an incremented ID or 1 if no IDs are defined.
    """
    nextid = qry.one()
    session.commit()
    data = nextid[0]
    if data is not None:
        return data + 1
    else:
        return 1


def getid(con):
    """

    :param con: Database ORM query object.
    :return: return the ID or 0.

    Given a name get the ID. If Name not found return 0

    """
    try:
        data = con.one()
        return data.ID
    except NoResultFound:
        return 0


# def adddefinition(con, componentid, categoryid, listorder):
#     """
#     Add a new definition to the definitions table
#     :param con:
#     :param componentid:
#     :param categoryid:
#     :param listorder:
#     :return:
#     """
#     try:
#         data = con.query(Definitions.ComponentID).filter(Definitions.ComponentID == componentid).\
#             filter(Definitions.CategoriesID == categoryid).\
#             filter(Definitions.CategoryOrder == listorder).one()
#         return
#     except NoResultFound:
#         add_def = Definitions(ComponentID=str(componentid), CategoriesID=str(categoryid),
#                               CategoryOrder=str(listorder))
#         con.add(add_def)
#         con.commit()
#         return
#
#
# class AddComponent(object):
#     """
#
#     Class to contain a component definition and provide interface.
#
#     """
#
#     def __init__(self, initial_data, session, rowsloaded):
#         """
#
#         :param initial_data:
#         :return:
#         """
#         self.componentid = None
#         self.componentname = None
#         self.description = None
#         self.categoriesid = []
#         self.suppliersid = 0
#         self.currentstock = None
#         self.reorderlevel = None
#         self.locationsid = 0
#         self.datasheet = None
#         self.ordercode = None
#         self.unitprice = None
#         self.rowsloaded = rowsloaded
#         self.loadstatus = ''
#         for column_name, column_value in initial_data:
#             #print '\nAttribute {} - ({})\n'.format(attribute_lookup[column_name], column_value)
#             if not callable(attribute_lookup[column_name][2]):
#                 self.__dict__[attribute_lookup[column_name][1]] = column_value
#             else:
#                 self.__dict__[attribute_lookup[column_name][1]] = \
#                     attribute_lookup[column_name][2](session, attribute_lookup[column_name][0],
#                                                      column_value, self)
#         # Check if the component exists if not create it
#         try:
#             testid = session.query(Components.ID).\
#                 filter(Components.Name == self.componentname).\
#                 filter(Components.CategoriesID == self.categoriesid[0]).\
#                 filter(Components.SuppliersID == self.suppliersid).\
#                 filter(Components.LocationsID == self.locationsid).one()
#             self.loadstatus = '{}{} already exists for this supplier and location.\n'.\
#                 format(self.loadstatus, self.componentname)
#
#         except NoResultFound:
#             new_component = Components(ID=self.componentid, Name=self.componentname,
#                                        Description=self.description,
#                                        CategoriesID=self.categoriesid[0], SuppliersID=self.suppliersid,
#                                        CurrentStock=self.currentstock, ReorderLevel=self.reorderlevel,
#                                        LocationsID=self.locationsid, Datasheet=self.datasheet,
#                                        OrderCode=self.ordercode, UnitPrice=self.unitprice)
#             session.add(new_component)
#             self.rowsloaded += 1
#             self.loadstatus = '{}{} added.\n'.\
#                 format(self.loadstatus, self.componentname)
#
#         session.commit()
#
#
class Category(object):
    """
    Define Category class to keep track of category searches
    """
    def __init__(self):
        self.id = []
        self.name = []
        self.listorder = []
        self.componentid = []

    def reset(self):
        self.id = []
        self.name = []
        self.listorder = []
        self.componentid = []


class HtmlMenu(object):
    def __init__(self, title):
        self.title = title
        self.url = []
        self.label = []


def filecheck(fn):
    try:
        open(fn, "r")
        return 1
    except IOError:
        return 0


class BaseObject(object):
    def __init__(self, dbsession, table):
        self.ID = None
        self.Name = None
        self.Description = None
        self.dbsession = dbsession
        self.new = None
        self.table = table
        self.rowsparsed = 0
        self.rowsloaded = 0

    def setid(self):
        qry = self.dbsession.query(self.table).filter(self.table.Name == self.Name)
        self.ID = getid(qry)
        if self.ID == 0:
            qry = self.dbsession.query(func.max(self.table.ID))
            self.ID = getnextid(self.dbsession, qry)
            self.new = True
#            print '{} New ID is {}\n'.format(self.Name, self.ID)
        else:
            self.new = False

    def parsename(self, value):
        self.Name = value

    def parsedescription(self, value):
        self.Description = value


class SupplierObject(BaseObject):
    def __init__(self, dbsession, table):
        BaseObject.__init__(self, dbsession, table)
        self.Website = None

    def checkcomplete(self):
        if self.Name is not None and \
                self.Description is not None and \
                self.Website is not None:
            if self.ID is None:
                self.setid()

    def parsewebsite(self, value):
        self.Website = value
        self.checkcomplete()

    def add(self):
        if self.Description is None:
            self.Description = self.Name
        add_supplier = Suppliers(ID=self.ID, Name=self.Name, Description=self.Description,
                                 Website=self.Website)
        self.dbsession.add(add_supplier)
        self.dbsession.commit()
        return 'Adding supplier {} - {}, {}, {}\n'.format(self.ID, self.Name,
                                                          self.Description, self.Website)


class LocationObject(BaseObject):
    def __init__(self, dbsession, table):
        BaseObject.__init__(self, dbsession, table)
        self.Sublocation = None

    def checkcomplete(self):
        if self.Name is not None and \
                self.Description is not None and \
                self.Sublocation is not None:
            if self.ID is None:
                self.setid()

    def parsesublocation(self, value):
        self.Sublocation = value
        self.checkcomplete()

    def add(self):
        if self.Description is None:
            self.Description = self.Name
        add_location = Locations(ID=self.ID, Name=self.Name, Description=self.Description,
                                 Sublocation=self.Sublocation)
        self.dbsession.add(add_location)
        self.dbsession.commit()
        return 'Adding location {} - {}, {}, {}\n'.format(self.ID, self.Name,
                                                          self.Description, self.Sublocation)


class FeatureObject(BaseObject):
    def __init__(self, dbsession, table):
        BaseObject.__init__(self, dbsession, table)
        self.strvalue = None
        self.intvalue = None
        self.newname = self.Name

    def setid(self):
        qry = self.dbsession.query(self.table).filter(self.table.Name == self.Name).\
            filter(self.table.StrValue == self.strvalue).\
            filter(self.table.IntValue == self.intvalue)
        self.ID = getid(qry)
        if self.ID == 0:
            qry = self.dbsession.query(func.max(self.table.ID))
            self.ID = getnextid(self.dbsession, qry)
            self.new = True
        else:
            self.new = False

    def parsename(self, value):
        if self.Name is not None:
            self.newname = value
        else:
            self.Name = value
        return 'Feature'

    def parsestrvalue(self, value):
        self.strvalue = value

    def parseintvalue(self, value):
        self.intvalue = value

    def add(self):
        if self.Description is None:
            self.Description = self.Name
        add_feature = Features(ID=self.ID, Name=self.Name, Description=self.Description,
                               StrValue=self.strvalue, IntValue=self.intvalue)
        self.dbsession.add(add_feature)
        self.dbsession.commit()
        return 'Adding feature {} - {}, {}\n'.format(self.ID, self.Name, self.Description)


class CategoryObject(BaseObject):
    def __init__(self, dbsession, table):
        BaseObject.__init__(self, dbsession, table)
        self.newname = self.Name

    def parsename(self, value):
        if self.Name is not None:
            self.newname = value
        else:
            self.Name = value
        return 'Category'

    def add(self):
        if self.Description is None:
            self.Description = self.Name
        add_category = Categories(ID=self.ID, Name=self.Name, Description=self.Description)
        self.dbsession.add(add_category)
        self.dbsession.commit()
        return 'Adding category {} - {}, {}\n'.format(self.ID, self.Name, self.Description)


class ComponentObject(BaseObject):
    def __init__(self, dbsession, table):
        BaseObject.__init__(self, dbsession, table)
        self.currentstock = None
        self.reorderlevel = None
        self.unitprice = None
        self.ordercode = None
        self.datasheet = None
        self.locationsid = 0
        self.suppliersid = 0
        self.categoriesid = 0
        self.featuresid = []
        self.new = None

    def setid(self):
        qry = self.dbsession.query(self.table.ID).filter(self.table.Name == self.Name).\
            filter(self.table.LocationsID == self.locationsid).\
            filter(self.table.SuppliersID == self.suppliersid).\
            filter(self.table.CategoriesID == self.categoriesid)
        self.ID = getid(qry)
        if self.ID == 0:
            qry = self.dbsession.query(func.max(self.table.ID))
            self.ID = getnextid(self.dbsession, qry)
            self.new = True
        else:
            self.new = False

    def parsename(self, value):
        self.Name = value
        # See if a category already exists for this name
        try:
             categoriesid = self.dbsession.query(Categories.ID).\
                 filter(Categories.Name == self.Name).one()
        except NoResultFound:
             category = CategoryObject(self.dbsession, Categories)
             category.parsename(value)
             qry = self.dbsession.query(func.max(Categories.ID))
             category.ID = getnextid(self.dbsession, qry)
             category.add()
             self.categoriesid = category.ID
             return 'Component'

    def parseid(self, value):
        pass

    def parsecurrentstock(self, value):
        self.currentstock = value

    def parsereorderlevel(self, value):
        self.reorderlevel = value

    def parseunitprice(self, value):
        self.unitprice = value

    def parseordercode(self, value):
        self.ordercode = value

    def parsedatasheet(self, value):
        self.datasheet = value

    def add(self):
        if self.Description is None:
            self.Description = self.Name
        add_component = Components(ID=self.ID, Name=self.Name, Description=self.Description,
                                   CategoriesID=self.categoriesid, SuppliersID=self.suppliersid,
                                   CurrentStock=self.currentstock, ReorderLevel=self.reorderlevel,
                                   LocationsID=self.locationsid, Datasheet=self.datasheet,
                                   OrderCode=self.ordercode, UnitPrice=self.unitprice)
        self.dbsession.add(add_component)
        self.dbsession.commit()
        self.rowsloaded += 1
        return 'Adding Component {} - {}, {} {} {}\n'.format(self.ID, self.Name,
                                                             self.Description,
                                                             self.suppliersid,
                                                             self.locationsid)


class NewComponent(object):

    def __init__(self, fileobject, data):
        self.fileoject = fileobject
        self.data = data
        self.componentid = None
        self.componentname = None
        self.description = None
        self.categoriesid = []
        self.suppliersid = 0
        self.currentstock = None
        self.reorderlevel = None
        self.locationsid = 0
        self.datasheet = None
        self.ordercode = None
        self.unitprice = None
        self.rowsloaded = 0
        self.loadstatus = ''
        self.categorylist = []
        self.featurelist = []
        self.component = ComponentObject(fileobject.dbsession, Components)
        self.category = CategoryObject(fileobject.dbsession, Categories)
        self.feature = FeatureObject(fileobject.dbsession, Features)
        self.location = LocationObject(fileobject.dbsession, Locations)
        self.supplier = SupplierObject(fileobject.dbsession, Suppliers)
        # this attribute is a dictionary of which object methods to use with which label
        self.attrib = {'Supplier': self.supplier.parsename,
                       'Supplier Description': self.supplier.parsedescription,
                       'Website': self.supplier.parsewebsite,
                       'Location': self.location.parsename,
                       'Location Description': self.location.parsedescription,
                       'Sublocation': self.location.parsesublocation,
                       'Category': self.category.parsename,
                       'Category Description': self.category.parsedescription,
                       'Feature': self.feature.parsename,
                       'Feature Description': self.feature.parsedescription,
                       'StrValue': self.feature.parsestrvalue,
                       'IntValue': self.feature.parseintvalue,
                       'Name': self.component.parsename,
                       'ID': self.component.parseid,
                       'Description': self.component.parsedescription,
                       'UnitPrice': self.component.parseunitprice,
                       'CurrentStock': self.component.parsecurrentstock,
                       'ReorderLevel': self.component.parsereorderlevel,
                       'OrderCode': self.component.parseordercode,
                       'Datasheet': self.component.parsedatasheet
                       }

    def checkid(self, obj):
        if obj.ID is None:
            if obj.Name is not None:
                if obj.Name != '':
                    obj.setid()
        if obj.new:
            return obj.add()
        return

    def parsedata(self):
        # Step through the data and load the various attributes
        logstatus = ''
        for column, value in zip(self.fileoject.titles, self.data):
            try:
                status = self.attrib[column](value)
                if status == 'Feature':
                    if self.feature.newname is not None:
                        checkstatus = self.checkid(self.feature)
                        if checkstatus is not None:
                            logstatus = '{}{}'.format(logstatus, checkstatus)
                        self.featurelist.append(self.feature.ID)
                        self.feature.__init__(self.fileoject.dbsession, Features)
                        self.feature.Name = value
                elif status == 'Category':
                    if self.category.newname is not None:
                        checkstatus = self.checkid(self.category)
                        if checkstatus is not None:
                            logstatus = '{}{}'.format(logstatus, checkstatus)
                        self.categorylist.append(self.category.ID)
                        self.category.__init__(self.fileoject.dbsession, Categories)
                        self.category.Name = value
            except KeyError:
                pass
        checkstatus = self.checkid(self.location)
        if checkstatus is not None:
            logstatus = '{}{}'.format(logstatus, checkstatus)
        checkstatus = self.checkid(self.supplier)
        if checkstatus is not None:
            logstatus = '{}{}'.format(logstatus, checkstatus)
        self.component.suppliersid = self.supplier.ID
        self.component.locationsid = self.location.ID
        checkstatus = self.checkid(self.component)
        if checkstatus is not None:
            logstatus = '{}{}'.format(logstatus, checkstatus)
        # Add the category definitions
        self.category.__init__(self.fileoject.dbsession, Categories)
        self.category.parsename(self.component.Name)
        self.category.add()
        self.categorylist.append(self.category.ID)
        listorder = 0
        for categoryid in self.categorylist:
            if categoryid is not None:
                listorder += 1
                add_definition = Definitions(ComponentID=self.component.ID, CategoriesID=categoryid,
                                             CategoryOrder=listorder)
                self.fileoject.dbsession.add(add_definition)
                self.fileoject.filestatus =  '{}Adding definition {} {} {}\n'.\
                    format(self.fileoject.filestatus, self.component.ID, categoryid, listorder)
            # print self.fileoject.filestatus
        # Add the features
        listorder = 0
        for featureid in self.featurelist:
            if featureid is not None:
                listorder += 1
                add_definition = DefinedFeatures(ComponentID=self.component.ID, FeatureID=featureid,
                                                 ListOrder=listorder)
                self.fileoject.dbsession.add(add_definition)
                self.fileoject.filestatus =  '{}Adding feature definition {} {} {}\n'.\
                    format(self.fileoject.filestatus, self.component.ID, featureid, listorder)
        self.fileoject.dbsession.commit()
        self.rowsloaded += self.component.rowsloaded
#        print logstatus,
        return logstatus


class FileLoad(object):

    def __init__(self, filename=None, session=None):
        self.filestatus = ""
        self.fp = None
        self.status = 0
        self.titles = []
        self.rowsloaded = 0
        self.duplicaterows = 0
        self.csvreader = None
        self.rows = 0
        if filename is None:
            self.filestatus = 'No filename supplied.'
            self.status = ERRNoFileName
        elif not (filecheck(filename)):
            self.filestatus = 'File Not Found. <{}>'.format(filename)
            self.status = ERRFileNotFound
        if self.status == 0:
            if session is None:
                self.filestatus = 'No Database Session Enable.'
                self.status = ERRNoFileName
            else:
                self.dbsession = session

    def loadtitles(self, filep):
        self.csvreader = csv.reader(filep)
        self.titles = self.csvreader.next()
        checkcomponent = NewComponent(self, self.titles)
        # Check for valid column titles
        for title in self.titles:
            try:
                test = checkcomponent.attrib[title]

            except KeyError:
                self.filestatus = '{}Invalid column header <{}>\n'.\
                    format(self.filestatus, title)
                return ERRInvalidTitle
        # Must always have a Name column
        try:
            locationindex = self.titles.index('Name')
        except ValueError:
            self.filestatus = '{}Row must always contain a name column.\n'.\
                    format(self.filestatus)
            return ERRNoNameCol

        # Location must always have been declared before any sublocations
        try:
            locationindex = self.titles.index('Location')
        except ValueError:
            locationindex = len(self.titles) + 1
        try:
            sublocindex = self.titles.index('Sublocation')
        except ValueError:
            sublocindex = -1
        if (sublocindex < locationindex) and (sublocindex >= 0):
                self.filestatus = '{}Sublocation declared before location.\n'.\
                    format(self.filestatus)
                return ERRSublocBeforeLoc

        # Feature must always have been declared before any strvalues or intvalues
        try:
            featureindex = self.titles.index('Feature')
        except ValueError:
            featureindex = len(self.titles) + 1
        try:
            strvalueindex = self.titles.index('StrValue')
        except ValueError:
            strvalueindex = -1
        try:
            intvalueindex = self.titles.index('IntValue')
        except ValueError:
            intvalueindex = -1
        if ((strvalueindex < featureindex) and (strvalueindex >= 0))\
                or ((intvalueindex < featureindex) and (intvalueindex >= 0)):
                self.filestatus = '{}Strvalue or Intvalue declared before any feature.\n'.\
                    format(self.filestatus)
                return ERRValueBeforeFeature
        return 0

    def loaddatarows(self, session):
        self.rows = 0
        status = 0
        for data in self.csvreader:
            self.rows += 1
            if len(data) != len(self.titles):
                self.filestatus = '{}Invalid number of columns in data row <{}>\n'.\
                    format(self.filestatus, self.rows)
                status = ERRInvalidNumCols
            else:
                new_object = NewComponent(self, data)
                loadstatus = new_object.parsedata()
                self.filestatus = '{}{}'.\
                    format(self.filestatus, loadstatus)
                self.rowsloaded += new_object.component.rowsloaded
        self.filestatus = '{}<{}> Data rows successfully loaded. <{}> rows read.\n'.\
            format(self.filestatus, self.rowsloaded, self.rows)
        return status


def loadfile(filename=None, session=None):
    fileloader = FileLoad(filename, session)
    if fileloader.status == 0:
        fileloader.filestatus = 'Loading from file : {}\n'.format(filename)
        with open(filename, mode='r') as fp:
            stat = fileloader.loadtitles(fp)
            if stat == 0:
                stat = fileloader.loaddatarows(session)
                if stat == 0:
                    fileloader.filestatus = '{}File <{}> successfully loaded.\n'.\
                        format(fileloader.filestatus, filename)
                else:
                    fileloader.filestatus = '{}File <{}> load aborted.\n'.\
                        format(fileloader.filestatus, filename)
            else:
                fileloader.filestatus = '{}File <{}> failed loading title row.\n'.\
                    format(fileloader.filestatus, filename)
    return fileloader
