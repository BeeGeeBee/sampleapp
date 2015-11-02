import csv
from sqlalchemy.sql import func
from models import Components, Base, Locations, Suppliers, Categories, Definitions, Features
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


def parsesupplier(con, table, name, self):
    """

    :rtype : object
    :param con:
    :param table:
    :param name:
    :return: integer
    """
    staticid = 0
    if name:
        qry = con.query(Suppliers.ID).filter(Suppliers.Name == name)
        staticid = getid(qry)
        if staticid == 0:
            qry = con.query(func.max(Suppliers.ID))
            staticid = getnextid(con, qry)
            add_supplier = Suppliers(ID=staticid, Name=name, Description=name)
            con.add(add_supplier)
            con.commit()
            self.loadstatus = '{}Adding Supplier {}\n'.format(self.loadstatus, name)
    return staticid


def parselocation(con, table, name, self):
    """

    :rtype : object
    :param con:
    :param table:
    :param name:
    :return: integer
    """
    staticid = 0
    if name:
        qry = con.query(Locations.ID).filter(Locations.Name == name)
        staticid = getid(qry)
        if staticid == 0:
            qry = con.query(func.max(Locations.ID))
            staticid = getnextid(con, qry)
            add_location = Locations(ID=staticid, Name=name, Description=name)
            con.add(add_location)
            con.commit()
            self.loadstatus = '{}Adding Location {}\n'.format(self.loadstatus, name)
    return staticid


def getfeatureid(con, name, self):
    """
        Get a feature id so use categoryid as well as name.
    :param con:
    :param name:
    :return:
    """
    try:
        data = con.query(Features.ID).filter(Features.Name == name).\
            filter(Features.CategoriesID == self.categoriesid[-1]).one()
        con.commit()
        return data[0]
    except NoResultFound:
        return 0


def updatefeature(con, column, strvalue, self):
    """

    :param con:
    :param column:
    :param strvalue:
    :return:
    """
    if strvalue:
        if column == 'StrValue':
            con.query(Features).update({Features.StrValue: strvalue,
                                        Features.CategoriesID: self.categoriesid[-1]})
        else:
            con.query(Features).update({Features.IntValue: strvalue,
                                        Features.CategoriesID: self.categoriesid[-1]})
        con.commit()
    return column


def updatelocations(con, column, strvalue, self):
    """

    :param con:
    :param column:
    :param strvalue:
    :return:
    """
    if strvalue:
        con.query(Locations).update({Locations.Sublocation: strvalue})
        con.commit()
        self.loadstatus = '{}Adding Sublocation {}\n'.format(self.loadstatus, strvalue)
    return column


def parsecomponentid(session, table, name, self):
    """

    :param session:
    :param table:
    :param name:
    :return:
    """
    qry = session.query(func.max(Components.ID).label('maxid'))
    return getnextid(session, qry)


def parsefeatureid(con, table, name, self):
    """

    :param con:
    :param table:
    :param name:
    :return:
    """
    if name:
        featureid = getfeatureid(con, name, self)
        if featureid == 0:
            qry = con.query(func.max(Features.ID))
            featureid = getnextid(con, qry)
            add_feature = Features(ID=featureid, Name=name, Description=name)
            con.add(add_feature)
            con.commit()
            self.loadstatus = '{}Adding Feature {}\n'.format(self.loadstatus, name)
        if 'featuresid' not in self.__dict__:
            self.featuresid = []
        self.featuresid.append(featureid)
        return featureid


def getnextid(session, qry):
    """

    :rtype : integer
    """
    nextid = qry.one()
    session.commit()
    data = nextid[0]
    if data is not None:
        return data + 1
    else:
        return 1


def getcategoryid(con, name):
    """

    :param con:
    :param name:
    :return:

    Given a name get the ID. If Name not found return 0

    """
    try:
        data = con.query(Categories.ID).filter(Categories.Name == name).one()
        return data[0]
    except NoResultFound:
        return 0


def getid(con):
    """

    :param con:
    :return:

    Given a name get the ID. If Name not found return 0

    """
    try:
        data = con.one()
        return data[0]
    except NoResultFound:
        return 0


def adddefinition(con, componentid, categoryid, listorder):
    """
    Add a new definition to the definitions table
    :param con:
    :param componentid:
    :param categoryid:
    :param listorder:
    :return:
    """
    try:
        data = con.query(Definitions.ComponentID).filter(Definitions.ComponentID == componentid).\
            filter(Definitions.CategoriesID == categoryid).\
            filter(Definitions.CategoryOrder == listorder).one()
        return
    except NoResultFound:
        add_def = Definitions(ComponentID=str(componentid), CategoriesID=str(categoryid),
                              CategoryOrder=str(listorder))
        con.add(add_def)
        con.commit()
        return


def parsecategoryid(con, table, name, self):
    """

    :param con:
    :param table:
    :param name:
    :return:
    """
    if name:
        categoryid = getcategoryid(con, name)
        if categoryid == 0:
            qry = con.query(func.max(Categories.ID))
            categoryid = getnextid(con, qry)
            add_category = Categories(ID=categoryid, Name=name, Description=name)
            con.add(add_category)
            con.commit()
            self.loadstatus = '{}Adding Category {}\n'.format(self.loadstatus, name)
        if 'categoriesid' not in self.__dict__:
            self.categoriesid = []
        if 'categorylistorder' not in self.__dict__:
            self.categorylistorder = 0
        self.categoriesid.append(categoryid)
        self.categorylistorder += 1
        adddefinition(con, self.componentid, categoryid, self.categorylistorder)
        return categoryid


attribute_lookup = {'Supplier': ('Suppliers', 'supplierid', parsesupplier),
                    'Location': ('Locations', 'locationid', parselocation),
                    'Name': ('Components', 'componentname', ''),
                    'ID': ('Components.ID', 'componentid', parsecomponentid),
                    'Description': ('Components', 'description', ''),
                    'UnitPrice': ('Components', 'unitprice', 0.0),
                    'Feature': ('Features', 'features', parsefeatureid),
                    'Category': ('Categories.ID', 'categories', parsecategoryid),
                    'Sublocation': ('Locations', 'sublocation', updatelocations),
                    'CurrentStock': ('Components', 'currentstock', 0),
                    'ReorderLevel': ('Components', 'reorderlevel', 0),
                    'OrderCode': ('Components', 'ordercode', ''),
                    'Website': ('Components', 'website', ''),
                    'StrValue': ('StrValue', 'strvalue', updatefeature),
                    'IntValue': ('IntValue', 'intvalue', updatefeature),
                    'Datasheet': ('Components', 'datasheet', '')}


class AddComponent(object):
    """

    Class to contain a component definition and provide interface.

    """

    def __init__(self, initial_data, session, rowsloaded):
        """

        :param initial_data:
        :return:
        """
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
        self.rowsloaded = rowsloaded
        self.loadstatus = ''
        for column_name, column_value in initial_data:
            #print '\nAttribute {} - ({})\n'.format(attribute_lookup[column_name], column_value)
            if not callable(attribute_lookup[column_name][2]):
                self.__dict__[attribute_lookup[column_name][1]] = column_value
            else:
                self.__dict__[attribute_lookup[column_name][1]] = \
                    attribute_lookup[column_name][2](session, attribute_lookup[column_name][0],
                                                     column_value, self)
        # Check if the component exists if not create it
        try:
            testid = session.query(Components.ID).\
                filter(Components.Name == self.componentname).\
                filter(Components.CategoriesID == self.categoriesid[0]).\
                filter(Components.SuppliersID == self.suppliersid).\
                filter(Components.LocationsID == self.locationsid).one()
            self.loadstatus = '{}{} already exists for this supplier and location.\n'.\
                format(self.loadstatus, self.componentname)

        except NoResultFound:
            new_component = Components(ID=self.componentid, Name=self.componentname,
                                       Description=self.description,
                                       CategoriesID=self.categoriesid[0], SuppliersID=self.suppliersid,
                                       CurrentStock=self.currentstock, ReorderLevel=self.reorderlevel,
                                       LocationsID=self.locationsid, Datasheet=self.datasheet,
                                       OrderCode=self.ordercode, UnitPrice=self.unitprice)
            session.add(new_component)
            self.rowsloaded += 1
            self.loadstatus = '{}{} added.\n'.\
                format(self.loadstatus, self.componentname)

        session.commit()


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
        for title in self.titles:
            try:
                test = attribute_lookup[title]

            except KeyError:
                self.filestatus = '{}Invalid column header <{}>\n'.\
                    format(self.filestatus, title)
                return ERRInvalidTitle
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
                comp_object = AddComponent(zip(self.titles, data), session, self.rowsloaded)
                self.rowsloaded = comp_object.rowsloaded
                self.filestatus = '{}{}'.\
                    format(self.filestatus, comp_object.loadstatus)
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
