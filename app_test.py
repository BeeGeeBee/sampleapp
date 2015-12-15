import os
import app
import unittest
import tempfile
import StringIO
from componentsmodule import FileLoad, loadfile, createdbsession
from flask import url_for

__author__ = 'bernie'


class ComponentsTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()
#       app.dbconnect(databasename=app.app.config['DATABASE'])

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.app.config['DATABASE'])

    def test_21database(self):
        print "Creating test database.\n"
        testsession = createdbsession('sqlite:///testdatabase.db', sqlecho=False, cleardown=True)
        # Initial Populate
        fileload = loadfile('testdata.csv', testsession)
        print fileload.filestatus
        assert '<18> Data rows successfully loaded.' in fileload.filestatus
#       testsession.close()

# Check Options to
# list by category
# list all components
# low stock report
# data maintenance
    def test_2checkoptions(self):
        rv = self.app.get('/')
        assert 'List By Category' in rv.data
        assert 'List All Components' in rv.data
        assert 'Low Stock Report' in rv.data
        assert 'Update Stock Levels' in rv.data
        assert 'Data Maintenance' in rv.data


# Category search into semiconductors to next level
    def test_2categorysearch(self):
        rv = self.app.get('/categorysearch/0/0')
#        print rv.data
        assert '->Semiconductor' in rv.data
        rv = self.app.get('/categorysearch/1/19')
        assert '->LED' in rv.data
        # Display details of an LED and check the order code
        rv = self.app.get('/categorysearch/3/25')
#        print rv.data
        assert '55-0125' in rv.data


# List all components
    def test_2listall(self):
        rv = self.app.get('/showlist/0')
        assert 'LED 5mm Red' in rv.data
        # Drill down to an LED and check the order code
        rv = self.app.get('/showcomponents/8')
        assert '55-0120' in rv.data


# Low stock report
    def test_2lowstock(self):
        rv = self.app.get('/showlist/1')
        assert 'LED 5mm Red' not in rv.data
        assert 'LED 5mm Green' in rv.data


# Open a datasheet and compare with original file
    def test_2datasheet(self):
        with open('docs/led_green_5mm_55-0120.pdf', 'rb') as pdf1:
            pdf1StringIO = StringIO.StringIO(pdf1.read())

        rv = self.app.get('/docs/led_green_5mm_55-0120.pdf')
        pdf1StringIO.seek(0)
        assert rv.data == pdf1StringIO.read()


# Static data maintenance options
# Add/Maintain Locations
# Add/Maintain Suppliers
# Upload a CSV formatted file
    def test_staticdataoptions(self):
        rv = self.app.get('/datamaint')
        assert 'Add/Maintain Components' in rv.data
        assert 'Add/Maintain Categories' in rv.data
        assert 'Add/Maintain Locations' in rv.data
        assert 'Add/Maintain Suppliers' in rv.data
        assert 'Add/Maintain Features' in rv.data
        assert 'Upload a CSV formatted file' in rv.data

# Maintain Components
    def test_2maintcomponents(self):
        rv = self.app.get('/maintstaticdata/component')
        # Page labelled correctly
        assert 'Maintain Components' in rv.data
        # Page displays current components
        assert 'LED 5mm Green' in rv.data
        # Page contains a delete option column.
        assert 'Delete' in rv.data
        # Page gives the option to add a component
        assert '"addButton"' in rv.data
        # Table should not have a Supplies Components header
        assert 'Supplies Components' not in rv.data
        # Add a component
        rv = self.app.post('/add/component', data=dict(
            name='Test component',
            description='This is a test component',
            supplier='3',
            location='1'
        ))
        assert 'Test component' in rv.data
        assert 'This is a test component' in rv.data
        # Check delete option available
        assert '"/delete/component/19"' in rv.data
        # Check add feature option available
        assert '"/addfeature/19"' in rv.data
        # Check add categories option available
        assert '"/addcategories/19"' in rv.data
        # Add features
        rv = self.app.post('/addfeature/19', data=dict(
                add2='y'
            ))
        assert 'Attached feature Package:DIP-8' in rv.data
        # Attach it to some categories.
        rv = self.app.post('/addcategories/19', data=dict(
                cat1=1,
                cat2=2
            ))
        assert 'Attached category IC to component' in rv.data
        assert 'Attached category PIC to component' in rv.data
        # Delete this new component
        rv = self.app.post('/delete/component/19')
        assert 'Successfully deleted ID 19 Test component' in rv.data

# Update stock
    def test_2maintstock(self):
        rv = self.app.get('/updatestock')
        # Page labelled correctly
        assert 'Update Stock Levels' in rv.data
        # Page displays current components
        assert 'LED 5mm Green' in rv.data
        rv = self.app.post('/updatestock', data=dict(
                stk8=999
            ))
        assert 'Updated stock for component LED 5mm Green to 999' in rv.data

# Maintain Categories
    def test_2maintcategoriess(self):
        rv = self.app.get('/maintstaticdata/category')
        # Page labelled correctly
        assert 'Maintain Categories' in rv.data
        # Page contains a delete option column.
        assert 'Delete' in rv.data
        # Should not offer delete for established category
#        print rv.data
        assert '"/delete/category/1"' not in rv.data
        # Table should have a Supplies Components header
        assert 'Supplies Components' in rv.data
        # Should see component referenced
        assert "'PIC12F629', 'PIC12F675'" in rv.data
        # Page displays current categories
        assert 'Semiconductor' in rv.data
        # Page gives the option to add a category
        assert '"addButton"' in rv.data
        # Add a category
        rv = self.app.post('/add/category', data=dict(
            name='Test category',
            description='This is a test category'
        ))
        assert 'Test category' in rv.data
        assert 'This is a test category' in rv.data
        # Check delete option available
#        print rv.data
        assert '"/delete/category/48"' in rv.data
        # Delete this new category
        rv = self.app.post('/delete/category/48')
        assert 'Successfully deleted ID 48 Test category' in rv.data
        # Cannot delete a category in use
        rv = self.app.post('/delete/category/1')
        assert 'Cannot delete IC. It is referenced by component(s)' in rv.data


# Maintain Locations
    def test_2maintlocations(self):
        rv = self.app.get('/maintstaticdata/location')
        # Page labelled correctly
        assert 'Maintain Locations' in rv.data
        # Page contains a delete option column.
        assert 'Delete' in rv.data
        # Should not offer delete for established location
        assert '"/delete/location/1"' not in rv.data
        # Table should have a Supplies Components header
        assert 'Supplies Components' in rv.data
        # Should see component referenced
        assert "'PIC16F887A', 'PIC12F675'" in rv.data
        # Page displays current locations
        assert 'MainCupboard - Cab A Tray 1' in rv.data
        # Page gives the option to add a location
        assert '"addButton"' in rv.data
        # Add a location
        rv = self.app.post('/add/location', data=dict(
            name='Test location',
            description='This is a test location',
            sublocation='A test sublocation'
        ))
        assert 'Test location' in rv.data
        assert 'This is a test location' in rv.data
        assert 'A test sublocation' in rv.data
        # Check delete option available
        assert '"/delete/location/3"' in rv.data
        # Delete this new location
        rv = self.app.post('/delete/location/3')
        assert 'Successfully deleted ID 3 Test location' in rv.data
        # Cannot delete a supplier in use
        rv = self.app.post('/delete/location/1')
        assert 'Cannot delete MainCupboard. It is referenced by component(s)' in rv.data


# Maintain Suppliers
    def test_2maintsuppliers(self):
        rv = self.app.get('/maintstaticdata/supplier')
        # Page labelled correctly
        assert 'Maintain Suppliers' in rv.data
        # Page contains a delete option column.
        assert 'Delete' in rv.data
        # Should not offer delete for RapidOnline
        assert '"/delete/supplier/1"' not in rv.data
        # Table should have a Supplies Components header
        assert 'Supplies Components' in rv.data
        # Should see component referenced
        assert "'PIC16F887A', 'PIC12F675'" in rv.data
        # Page displays current suppliers
        assert 'RapidOnline' in rv.data
        # Page gives the option to add a supplier
        assert '"addButton"' in rv.data
        # Add a supplier
        rv = self.app.post('/add/supplier', data=dict(
            name='Test supplier',
            description='This is a test supplier',
            website='www.testdata.test'
        ))
        assert 'Test supplier' in rv.data
        assert 'This is a test supplier' in rv.data
        assert 'www.testdata.test' in rv.data
        # Check delete option available
        assert '"/delete/supplier/4"' in rv.data
        # Delete this new supplier
        rv = self.app.post('/delete/supplier/4')
        assert 'Successfully deleted ID 4 Test supplier' in rv.data
        # Cannot delete a supplier in use
        rv = self.app.post('/delete/supplier/3')
        assert 'Cannot delete Discontinued. It is referenced by component(s)' in rv.data



# Maintain Features
    def test_2maintfeatures(self):
        rv = self.app.get('/maintstaticdata/feature')
        # Page labelled correctly
        assert 'Maintain Features' in rv.data
        # Page contains a delete option column.
        assert 'Delete' in rv.data
        # Should not offer delete for RapidOnline
        assert '"/delete/feature/1"' not in rv.data
        # Table should have a Supplies Components header
        assert 'Supplies Components' in rv.data
        # Should see component referenced
        assert "'PIC12F629', 'PIC12F675'" in rv.data
        # Should not see multiple occurences of components
        assert "'PIC16F887A', 'PIC16F887A'" not in rv.data
        # Page displays current Features
        assert 'DIP-40' in rv.data
        # Page gives the option to add a feature
        assert '"addButton"' in rv.data
        # Add a feature
        rv = self.app.post('/add/feature', data=dict(
            name='Test feature',
            description='This is a test feature',
            strvalue='A Feature',
            intvalue='10'
        ))
        assert 'Test feature' in rv.data
        assert 'This is a test feature' in rv.data
        assert 'A Feature' in rv.data
        # Check one of the test data set features is there
        assert 'DIP-18' in rv.data
        # Check delete option available
        assert '"/delete/feature/6"' in rv.data
        # Delete this new feature
        rv = self.app.post('/delete/feature/6')
        assert 'Successfully deleted ID 6 Test feature' in rv.data
        # Cannot delete a feature in use
        rv = self.app.post('/delete/feature/3')
        assert 'Cannot delete Package. It is referenced by component(s)' in rv.data


# Get a CSV formatted file
    def test_csvfilename(self):
        testfile = 'testcsv.csv'
        # Page to select the file name
        rv = self.app.get('/fileupload')
        assert 'Stock Data File Upload' in rv.data
        # Log of file load operation
        rv = self.app.post('/fileupload', data=dict(
            uploadfile=testfile
        ))
        assert 'Stock Data File Upload Log' in rv.data
        # If no file to load given then report it.
        response = FileLoad()
        assert 'No filename supplied.' in response.filestatus
        # If file to load not found report it.
        response = FileLoad(testfile)
        assert 'File Not Found. <{}>'.format(testfile) in response.filestatus

    # Must trap various csv load issues
    def test_loadcsvfile(self):
        # Set up a session
        testsession = createdbsession('sqlite:///testdatabase.db', sqlecho=False, cleardown=True)
        # Only valid column headers in file
        testfile = 'testdatafail1.csv'
        response = loadfile(testfile, testsession)
        assert 'Invalid column header <Dummy>' in response.filestatus
        # A Location column must always be declared before any sublocations
        testfile = 'testdatafailsubloc.csv'
        response = loadfile(testfile, testsession)
        assert 'Sublocation declared before location.' in response.filestatus
        # A Feature column must always be declared before any strvalue or intvalue
        testfile = 'testdatafailfeaturevalue.csv'
        response = loadfile(testfile, testsession)
        assert 'Strvalue or Intvalue declared before any feature.' in response.filestatus
        # Each row must have same number of columns as header row.
        testfile = 'testdatafail2.csv'
        response = loadfile(testfile, testsession)
        assert 'Invalid number of columns in data row <1>' in response.filestatus
        # Report file successfully loaded with the number of rows loaded.
        testfile = 'testdata.csv'
        rv = self.app.post('/fileupload', data=dict(
            uploadfile=testfile
        ))
        assert 'File &lt;{}&gt; successfully loaded.'.format(testfile) in rv.data
        assert '&gt; Data rows successfully loaded.' in rv.data
        # Report components already configured so they are not loaded a second time.
        testfile = 'testdata.csv'
        rv = self.app.post('/fileupload', data=dict(
            uploadfile=testfile
        ))
        assert 'Component PIC16F887A already exists' in rv.data


if __name__ == '__main__':
    unittest.main()
