import csv
from componentsmodule import Component, dbconnect
import pdb

#pdb.set_trace()

with dbconnect() as conn:

    with open(r'testdata.csv','r') as fp:
        component_details = csv.reader(fp)
        titles_row = component_details.next()
        for component_row in component_details:
            comp_object = Component(zip(titles_row,component_row),conn)
            print component_row


