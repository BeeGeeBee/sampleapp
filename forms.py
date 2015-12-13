__author__ = 'Bernard'

from wtforms import Form, StringField, IntegerField, widgets,\
    SelectField, DecimalField, HiddenField, BooleanField, RadioField
from wtforms.validators import Length

class BasicForm(Form):
    name = StringField('Name', [Length(min=1, max=50)])
    description = StringField('Description', [Length(max=250)])
    components = StringField('Supplies Components', [Length(max=5000)])

class FeaturesForm(BasicForm):
    strvalue = StringField('String Value', [Length(max=250)])
    intvalue = IntegerField('Integer Value', [Length(max=10)])
#    categoriesid = IntegerField('CategoriesID', [Length(max=10)])

class AddFeaturesForm(FeaturesForm):
#    add = BooleanField('Add', default=False)
    featureid = IntegerField('ID', [Length(max=4)])


class ComponentsForm(BasicForm):
    id = HiddenField('', [Length(max=3)])
    supplier = SelectField('Supplier', [Length(max=50)])
    location = SelectField('Location', [Length(max=100)])
    currentstock = IntegerField('Stock', [Length(max=3)])
    reorderlevel = IntegerField('ReorderLevel', [Length(max=3)])
    ordercode = StringField('OrderCode', [Length(max=20)])
    unitprice = DecimalField('UnitPrice', [Length(max=10)])
    datasheet = StringField('Datasheet', [Length(max=50)])
    categoryid = StringField('Category', [Length(max=5)])
#    feature = FeaturesForm()


class LocationsForm(BasicForm):
    sublocation = StringField('Sublocation', [Length(max=50)])


class SuppliersForm(BasicForm):
    website = StringField('Website', [Length(max=250)])


class CategoriesForm(BasicForm):
    pass


class AddCategoriesForm(CategoriesForm):
    pass