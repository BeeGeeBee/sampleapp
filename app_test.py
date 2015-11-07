import os
import app
import unittest
import tempfile
import StringIO
from componentsmodule import FileLoad, loadfile, createdbsession

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

    def test_database(self):
        print "Creating test database.\n"
        testsession = createdbsession('sqlite:///testdatabase.db', sqlecho=False, cleardown=True)
        # Initial Populate
        fileload = loadfile('testdata.csv', testsession)
        assert '<18> Data rows successfully loaded.' in fileload.filestatus
        testsession.close()

# Check Options to
# list by category
# list all components
# low stock report
# data maintenance
    def test_checkoptions(self):
        rv = self.app.get('/')
        assert 'List By Category' in rv.data
        assert 'List All Components' in rv.data
        assert 'Low Stock Report' in rv.data
        assert 'Data Maintenance' in rv.data


# Category search into semiconductors to next level
    def test_categorysearch(self):
        rv = self.app.get('/categorysearch/0/0')
        assert '->Semiconductor' in rv.data
        rv = self.app.get('/categorysearch/1/12')
        assert '->LED' in rv.data
        # Display details of an LED and check the order code
        rv = self.app.get('/categorysearch/3/16')
        assert '55-0125' in rv.data


# List all components
    def test_listall(self):
        rv = self.app.get('/showlist/0')
        assert 'LED 5mm Red' in rv.data
        # Drill down to an LED and check the order code
        rv = self.app.get('/showcomponents/8')
        assert '55-0120' in rv.data


# Low stock report
    def test_lowstock(self):
        rv = self.app.get('/showlist/1')
        assert 'LED 5mm Red' not in rv.data
        assert 'LED 5mm Green' in rv.data


# Open a datasheet and compare with original file
    def test_datasheet(self):
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
        assert 'Upload a CSV formatted file' in rv.data

# Maintain Components
    def test_maintcomponents(self):
        rv = self.app.get('/maintstaticdata/component')
        # Page labelled correctly
        assert 'Maintain Components' in rv.data
        # Page displays current components
        assert 'LED 5mm Green' in rv.data

# Maintain Categories
    def test_maintcategoriess(self):
        rv = self.app.get('/maintstaticdata/category')
        # Page labelled correctly
        assert 'Maintain Categories' in rv.data
        # Page displays current locations
        assert 'Semiconductor' in rv.data


# Maintain Locations
    def test_maintlocations(self):
        rv = self.app.get('/maintstaticdata/location')
        # Page labelled correctly
        assert 'Maintain Locations' in rv.data
        # Page displays current locations
        assert 'MainCupboard - Cab A Tray 1' in rv.data


# Maintain Suppliers
    def test_maintsuppliers(self):
        rv = self.app.get('/maintstaticdata/supplier')
        # Page labelled correctly
        assert 'Maintain Suppliers' in rv.data
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


# Upload a CSV formatted file
    def test_uploadcsvfile(self):
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
        # Set up a session
        testsession = createdbsession('sqlite:///testdatabase.db', sqlecho=False, cleardown=True)
        # Only valid column headers in file
        testfile = 'testdatafail1.csv'
        response = loadfile(testfile, testsession)
        assert 'Invalid column header <Dummy>' in response.filestatus
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


if __name__ == '__main__':
    unittest.main()
