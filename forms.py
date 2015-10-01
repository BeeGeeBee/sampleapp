__author__ = 'Bernard'

from wtforms import Form, BooleanField, TextAreaField, StringField, SubmitField
from wtforms.validators import Length, required


class ComponentsForm(Form):
    id = StringField('ID', [Length(max=50)])
    name = StringField('Name', [Length(max=50)])
    supplier = StringField('Supplier', [Length(max=50)])
    description = StringField('Description', [Length(max=50)])
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
