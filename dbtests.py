__author__ = 'bernie'

from componentsmodule import dbconnect, getnextid, getid
import os


def test_dbconnect():
    localcon = dbconnect(databasename='components1.db')
    print 'Test for missing database.'
    assert localcon is False, 'Database does exist'
    localcon = dbconnect()
    print 'Test for default database.'
    assert localcon is not False, 'Default database does not exist'
    localcon.close()
    localcon = dbconnect(databasename='components1.db', readonly=False)
    print 'Test empty database create.'
    if not os.path.exists('components1.db'):
        assert False, 'Unable to create database file.'
    else:
        localcon.close()
        os.remove('components1.db')

con = dbconnect()


def test_getnextid():
    print 'Testing getnextid.'
    assert getnextid(con, 'components') > 0, 'getnextid failed on table components'


def test_getid():
    print 'Testing getid.'
    assert getid(con, 'Test Value', 'components') is not 'None', 'getid failed'