__author__ = 'Ellies'
"""
componentsmodule to access data, load data etc in components database
"""

import sqlite3 as sql
import os


def dbconnect(databasename='components.db', readonly=True):
    """
    :return:
    connect to database
    """
    # Check database exists
    if readonly:
        if not os.path.exists(databasename):
            return False
    con = sql.connect(databasename)
    return con


def getnextid(con, table):
    """

    :rtype : integer
    """
    curs = con.cursor()
    curs.execute('SELECT max(ID) as maxid from ' + table)
    data = curs.fetchone()
    if data[0] is not None:
        return data[0] + 1
    else:
        return 1


def getid(con, name, table):
    """

    :param con:
    :param name:
    :param table:
    :return:

    Given a name get the ID. If Name not found return 0

    """
    curs = con.cursor()
    curs.execute('SELECT ID from ' + table + ' where Name = \'' + name + '\'')
    data = curs.fetchone()
    if data is not None:
        return data[0]
    else:
        return data


def addstatic(con, table, name):
    """
    Add a static data record.
    :param con:
    :param table:
    :param name:
    :return:
    """
    nextid = getnextid(con, table)
    con.cursor().execute(("INSERT INTO " + table + " (ID,Name,Description) values("
                          + str(nextid) + ",'" + name + "','" + name + "')"))
    con.commit()
    return nextid


def adddefinition(con, componentid, categoryid, listorder):
    """
    Add a new definition to the definitions table
    :param con:
    :param componentid:
    :param categoryid:
    :param listorder:
    :return:
    """
    con.cursor().execute((
        'INSERT INTO Definitions (ComponentID,CategoriesID,CategoryOrder) values({0},{1},{2})'.format(str(componentid),
                                                                                                      str(categoryid),
                                                                                                      str(listorder))))


def parsestatic(con, table, name, self):
    """

    :rtype : object
    :param con:
    :param table:
    :param name:
    :return: integer
    """
    staticid = 0
    if name:
        staticid = getid(con, name, table)
        if not staticid:
            staticid = addstatic(con, table, name)
    return staticid


def getfeatureid(con, name, self):
    """
        Get a feature id so use categoryid as well as name.
    :param con:
    :param name:
    :return:
    """
    curs = con.cursor()
    curs.execute("SELECT ID from Features where Name = '" + name + "' and CategoriesID=" + str(self.categoriesid[-1]))
    data = curs.fetchone()
    if data is not None:
        return data[0]
    else:
        return data


def updatefeature(con, column, strvalue, self):
    """

    :param con:
    :param column:
    :param strvalue:
    :return:
    """
    if strvalue:
        curs = con.cursor()
        sqlstatement = "UPDATE Features set " + column + "="
        if column == 'StrValue':
            sqlstatement = sqlstatement + "'" + strvalue + "'"
        else:
            sqlstatement = sqlstatement + strvalue
        sqlstatement = sqlstatement + ", CategoriesID=" + str(self.categoriesid[-1])
        sqlstatement = sqlstatement + " WHERE ID=" + str(self.featuresid[-1])
        print sqlstatement
        curs.execute(sqlstatement)
    return column


def updatelocations(con, column, strvalue, self):
    """

    :param con:
    :param column:
    :param strvalue:
    :return:
    """
    if strvalue:
        curs = con.cursor()
        sqlstatement = "UPDATE Locations set Sublocation = " + "'" + strvalue + "'"
        sqlstatement = sqlstatement + " WHERE ID=" + str(self.locationid)
        print sqlstatement
        curs.execute(sqlstatement)
    return column


def parsecomponentid(con, table, name, self):
    """

    :param con:
    :param table:
    :param name:
    :return:
    """
    return getnextid(con, table)


def parsefeatureid(con, table, name, self):
    """

    :param con:
    :param table:
    :param name:
    :return:
    """
    if name:
        featureid = getfeatureid(con, name, self)
        if not featureid:
            featureid = addstatic(con, 'Features', name)
        if 'featuresid' not in self.__dict__:
            self.featuresid = []
        self.featuresid.append(featureid)
        return featureid


def parsecategoryid(con, table, name, self):
    """

    :param con:
    :param table:
    :param name:
    :return:
    """
    if name:
        categoryid = getid(con, name, table)
        if not categoryid:
            categoryid = addstatic(con, table, name)
        if 'categoriesid' not in self.__dict__:
            self.categoriesid = []
        if 'categorylistorder' not in self.__dict__:
            self.categorylistorder = 0
        self.categoriesid.append(categoryid)
        self.categorylistorder += 1
        adddefinition(con, self.componentid, categoryid, self.categorylistorder)
        return categoryid

attribute_lookup = {'Supplier': ('Suppliers', 'supplierid', parsestatic),
                    'Location': ('Locations', 'locationid', parsestatic),
                    'Name': ('Components', 'componentname', ''),
                    'ID': ('Components', 'componentid', parsecomponentid),
                    'Description': ('Components', 'description', ''),
                    'UnitPrice': ('Components', 'unitprice', 0.0),
                    'Feature': ('Features', 'features', parsefeatureid),
                    'Category': ('Categories', 'categories', parsecategoryid),
                    'Sublocation': ('Locations', 'sublocation', updatelocations),
                    'CurrentStock': ('Components', 'currentstock', 0),
                    'ReorderLevel': ('Components', 'reorderlevel', 0),
                    'OrderCode': ('Components', 'ordercode', ''),
                    'Website': ('Components', 'website', ''),
                    'StrValue': ('StrValue', 'strvalue', updatefeature),
                    'IntValue': ('IntValue', 'intvalue', updatefeature),
                    'Datasheet': ('Components', 'datasheet', '')}


class Component(object):
    """

    Class to contain a component definition and provide interface.

    """

    def __init__(self, initial_data, con):
        """

        :param initial_data:
        :return:
        """
        for column_name, column_value in initial_data:
            if not callable(attribute_lookup[column_name][2]):
                self.__dict__[attribute_lookup[column_name][1]] = column_value
            else:
                self.__dict__[attribute_lookup[column_name][1]] = \
                    attribute_lookup[column_name][2](con, attribute_lookup[column_name][0], column_value, self)
        cmd = """
        INSERT INTO Components
        (ID,Name,Description,CategoriesID,SuppliersID,CurrentStock,ReorderLevel,LocationsID,Datasheet,OrderCode,UnitPrice)
            values (?,?,?,?,?,?,?,?,?,?,?)
            """
        values = [str(item) for item in (self.componentid, self.componentname, self.description, self.categoriesid[0],
                                         self.supplierid,  self.currentstock, self.reorderlevel, self.locationid,
                                         self.datasheet, self.ordercode, self.unitprice)]
        con.cursor().execute(cmd, values)
        con.commit()
