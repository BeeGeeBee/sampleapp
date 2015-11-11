__author__ = 'Bernard'

from wtforms import Form, BooleanField, TextAreaField, StringField, SubmitField, IntegerField
from wtforms.validators import Length


class BasicForm(Form):
    name = StringField('Name', [Length(min=1, max=50)])
    description = StringField('Description', [Length(max=250)])


class ComponentsForm(BasicForm):
    id = StringField('ID', [Length(max=50)])
    supplier = StringField('Supplier', [Length(max=50)])
    location = StringField('Location', [Length(max=50)])
    sublocation = StringField('Sublocation', [Length(max=50)])
    datasheet = StringField('Datasheet', [Length(max=50)])
    currentstock = StringField('Current Stock', [Length(max=50)])
    reorderlevel = StringField('Reorder Level', [Length(max=50)])
    ordercode = StringField('Order Code', [Length(max=50)])
    unitprice = StringField('Unit Price', [Length(max=50)])
    submit = SubmitField("Return")
    categoryid = StringField('Category', [Length(max=5)])
    feature = StringField('Feature', [Length(max=50)])


class LocationsForm(BasicForm):
    sublocation = StringField('Sublocation', [Length(max=50)])


class SuppliersForm(BasicForm):
    website = StringField('Website', [Length(max=250)])


class FeaturesForm(BasicForm):
    strvalue = StringField('String Value', [Length(max=250)])
    intvalue = IntegerField('Integer Value', [Length(max=10)])
#    categoriesid = IntegerField('CategoriesID', [Length(max=10)])


class CategoriesForm(BasicForm):
    pass
