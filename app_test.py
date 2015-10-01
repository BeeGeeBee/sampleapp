import os
import app
import unittest
import tempfile
import StringIO


__author__ = 'bernie'


class ComponentsTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()
        app.dbconnect(databasename=app.app.config['DATABASE'])

    def tearDown(self):
        os.close(self.db_fd)
        #os.unlink(app.app.config['DATABASE'])


# Check Options to
# list by category
# list all components
# low stock report
    def test_checkoptions(self):
        rv = self.app.get('/')
        assert 'List By Category' in rv.data
        assert 'List All Components' in rv.data
        assert 'Low Stock Report' in rv.data


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


# Open a datasheet
    def test_datasheet(self):
        with open('docs/led_green_5mm_55-0120.pdf', 'rb') as pdf1:
            pdf1StringIO = StringIO.StringIO(pdf1.read())

        rv = self.app.get('/docs/led_green_5mm_55-0120.pdf')
        pdf1StringIO.seek(0)
        assert rv.data == pdf1StringIO.read()


if __name__ == '__main__':
    unittest.main()