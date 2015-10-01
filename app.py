import os
from flask import Flask, render_template, request, send_file, redirect, url_for
from forms import ComponentsForm
from models import Components, Base, Locations, Suppliers, Categories, Definitions, Features
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from componentsmodule import dbconnect


__author__ = 'Bernard'


class Category(object):
    '''
    Define Category class to keep track of category searches
    '''
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


# Connect to database (for sqlite)
engine = create_engine('sqlite:///database//components.db', echo=True)
Base.metadata.bind = engine

DBSession = sessionmaker()
DBSession.bind = engine
session = DBSession()

app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'database/components.db'),
    DEBUG=True,
    SECRET_KEY='development key',
))
app.config.from_envvar('APP_SETTINGS', silent=True)
con = dbconnect()


@app.route('/')
def index():
    return render_template('index.html')


def create_query(filtered=1):
    '''
    Build a query object depending on whether it is a filtered query or not
    :param filtered:
    :return: orm query object
    '''
    if filtered == '1':
        query_obj = session.query(Components.ID, Components.Name, Components.CurrentStock, Components.ReorderLevel,
                        Components.UnitPrice, Suppliers.Name, Locations.Name, Components.Datasheet). \
                        outerjoin(Suppliers, Components.SuppliersID == Suppliers.ID). \
                        outerjoin(Locations, Components.LocationsID == Locations.ID). \
                        filter(Components.CurrentStock <= Components.ReorderLevel). \
                        filter(Components.ReorderLevel != ""). \
                        order_by(Components.Name)
    else:
        query_obj = session.query(Components.ID, Components.Name, Components.CurrentStock,
                        Components.ReorderLevel, Components.UnitPrice, Suppliers.Name, Locations.Name,
                        Components.Datasheet). \
                        outerjoin(Suppliers, Components.SuppliersID == Suppliers.ID). \
                        outerjoin(Locations, Components.LocationsID == Locations.ID). \
                        order_by(Components.Name)
    return query_obj


def init_form():
    form = ComponentsForm()
    form.name.value = []
    form.id.value = []
    form.currentstock.value = []
    form.reorderlevel.value = []
    form.unitprice.value = []
    form.supplier.value = []
    form.location.value = []
    form.datasheet.value = []
    return form


@app.route('/showlist/<filtered>')
def showlist(filtered=None):
    form = init_form()
    query_obj = create_query(filtered=filtered)
    for (componentid, name, currentstock, reorderlevel, unitprice, supplier, location, datasheet) in query_obj:
        form.id.value.append(componentid)
        form.name.value.append(name)
        form.currentstock.value.append(currentstock)
        form.reorderlevel.value.append(reorderlevel)
        form.unitprice.value.append(unitprice)
        form.supplier.value.append('')
        if supplier:
            form.supplier.value[-1] = supplier
        form.location.value.append('')
        if location:
            form.location.value[-1] = location
        form.datasheet.value.append(datasheet)
    return render_template('showlist.html', form=form, numrows=len(form.name.value))


@app.route('/docs/<docid>')
def show_pdf(docid=None):
    if docid is not None:
        return send_file("docs/" + docid)


catsearch = Category()


@app.route('/showcomponents/<componentid>', methods=['POST', 'GET'])
def showcomponents(componentid=None):
    if request.method == 'POST':
        pass

    form = ComponentsForm()
    q = session.query(Components, Suppliers, Locations). \
        outerjoin(Suppliers, Components.SuppliersID == Suppliers.ID). \
        outerjoin(Locations, Components.LocationsID == Locations.ID). \
        filter(Components.ID == componentid).one()
    form.name.data = q.Components.Name
    form.description.data = ''
    if q.Components.Description is not None:
        form.description.data = q.Components.Description
    form.ordercode.data = ''
    if q.Components.OrderCode is not None:
        form.ordercode.data = q.Components.OrderCode
    form.supplier.data = ''
    if q.Suppliers is not None:
        form.supplier.data = q.Suppliers.Name
    form.location.data = ''
    form.sublocation.data = ''
    if q.Locations is not None:
        form.location.data = q.Locations.Name
        if q.Locations.Sublocation is not None:
            form.sublocation.data = q.Locations.Sublocation
    form.datasheet.data = ''
    if q.Components.Datasheet is not None:
        form.datasheet.data = q.Components.Datasheet
    form.currentstock.data = q.Components.CurrentStock
    form.reorderlevel.data = q.Components.ReorderLevel
    form.categoryid.id = []
    form.categoryid.name = []
    form.categoryid.listorder = []
    catsearch.reset()
    catsearchindex = 0
    for category in session.query(Definitions, Categories). \
            join(Categories, Definitions.CategoriesID == Categories.ID). \
            filter(Definitions.ComponentID == componentid).order_by(Definitions.CategoryOrder):
        form.categoryid.id.append(category.Categories.ID)
        form.categoryid.name.append(category.Categories.Name)
        form.categoryid.listorder.append(catsearchindex + 1)
        catsearch.listorder.append(catsearchindex + 1)
        catsearch.id.append(category.Categories.ID)
        catsearch.name.append(category.Categories.Name)
        catsearchindex += 1
    form.feature.label = []
    form.feature.name = []
    for feature in session.query(Features). \
            filter(Features.CategoriesID == form.categoryid.id[-1]).order_by(Features.ListOrder):
        form.feature.label.append(feature.Name)
        if feature.StrValue is not None:
            form.feature.name.append(feature.StrValue)
        else:
            form.feature.name.append(str(feature.IntValue))

    return render_template('componentform.html', form=form, numcats=len(form.categoryid.id),
                           numfeatures=len(form.feature.label), readlock='True')


@app.route('/categorysearch/<categorylevel>/<categoryid>')
def categorysearch(categorylevel=None, categoryid=None):
    if categorylevel is not None and categoryid is not None:
        categories = Category()
        catlevel = int(categorylevel)
        catid = int(categoryid)
        if catid > 0:
            # Test if it is a component. First get category name
            cat = session.query(Categories.Name).filter(Categories.ID == catid).one()
            compexists = session.query(func.count(Components.Name)).filter(Components.Name == cat[0]).scalar()
            if compexists > 0:
                # A component matches this category by name so display the component
                compid = session.query(Components.ID).filter(Components.Name == cat[0]).one()
                return showcomponents(componentid=compid[0])
            while len(catsearch.id) >= catlevel:
                catsearch.id.pop()
                catsearch.name.pop()
                catsearch.listorder.pop()
            catsearch.id.append(catid)
            catsearch.listorder.append(catlevel)
            catsearch.name.append(cat[0])
        # If coming in for top level categories get all components with Categoryorder == 1
        if catlevel == 0:
            catsearch.reset()
            for sublist in session.query(Definitions). \
                    filter(Definitions.CategoryOrder == 1).distinct():
                categories.componentid.append(sublist.ComponentID)
        else:
            # Collect all distinct categories from definitions at the current level
            for sublist in session.query(Definitions). \
                    filter(Definitions.CategoriesID == categoryid). \
                    filter(Definitions.CategoryOrder == catlevel).distinct():
                categories.componentid.append(sublist.ComponentID)
        catlevel += 1
        # Get all the distinct categories at the selected level
        for category in session.query(Categories.Name, Categories.ID). \
                join(Definitions, Definitions.CategoriesID == Categories.ID). \
                filter(Definitions.CategoryOrder == catlevel). \
                filter(Definitions.ComponentID.in_(categories.componentid)). \
                order_by(Categories.Name).distinct():
            categories.id.append(category.ID)
            categories.listorder.append(catlevel)
            categories.name.append(category.Name)
        # Create a matrix of objects. The catmatrix array represents each level across the page.
        # The array of attributes represents each row going down the page.
        catmatrix = [Category() for catpoint in range(len(catsearch.name) + 1)]
        catpoint = len(catsearch.name)
        if catid > 0:
            # This loop adds a top row showing the category path
            for counter in range(catpoint):
                catmatrix[counter].id.append(catsearch.id[counter])
                catmatrix[counter].listorder.append(catsearch.listorder[counter])
                catmatrix[counter].name.append(catsearch.name[counter])
            # This double loop pads out the rows under the top row. The ? in the name is used on the html sheet
            # to decide whether to display anything in a particular cell.
            for counter in range(catpoint):
                for catcount in range(len(categories.name) - 1):
                    catmatrix[counter].id.append(0)
                    catmatrix[counter].listorder.append(catcount)
                    catmatrix[counter].name.append("?")
        # This loop adds the final rightmost column of categories.
        for catcount in range(len(categories.name)):
            catmatrix[catpoint].id.append(categories.id[catcount])
            catmatrix[catpoint].listorder.append(categories.listorder[catcount])
            catmatrix[catpoint].name.append(categories.name[catcount])
        return render_template("categorysearch.html", categories=catmatrix, numcats=len(categories.id),
                               numlevels=catpoint + 1)


if __name__=='__main__':
    app.run(host='0.0.0.0',debug=True)