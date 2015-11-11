import os
from flask import Flask, render_template, request, send_file, redirect, url_for
from forms import ComponentsForm, LocationsForm, SuppliersForm, BasicForm, FeaturesForm
from models import Components, Base, Locations, Suppliers, Categories, Definitions, Features
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from componentsmodule import loadfile, Category, HtmlMenu, createdbsession, getnextid


__author__ = 'Bernard'


app = Flask(__name__)

# Load config and override config from an environment variable if defined
app.config.from_pyfile('components.cfg')
app.config.from_envvar('APP_SETTINGS', silent=True)

# Connect to database
session = createdbsession(app.config['DATABASE'], sqlecho=app.config['DBECHO'], cleardown=False)


@app.route('/')
def index():
    menu = HtmlMenu('Electronic Components Stock Management')
    menu.url.append('/categorysearch/0/0')
    menu.label.append('List By Category')
    menu.url.append('/showlist/0')
    menu.label.append('List All Components')
    menu.url.append('/showlist/1')
    menu.label.append('Low Stock Report')
    menu.url.append('/datamaint')
    menu.label.append('Data Maintenance')
    return render_template('menu.html', menu=menu, numrows=len(menu.url))


def createlistquery(filtered=1):
    """
    Build a query object depending on whether it is a filtered query or not
    :param filtered:
    :return: orm query object
    """
    if filtered == '1':
        query_obj = session.query(Components.ID, Components.Name, Components.CurrentStock,
                                  Components.ReorderLevel, Components.UnitPrice, Suppliers.Name,
                                  Locations.Name, Components.Datasheet). \
                        outerjoin(Suppliers, Components.SuppliersID == Suppliers.ID). \
                        outerjoin(Locations, Components.LocationsID == Locations.ID). \
                        filter(Components.CurrentStock <= Components.ReorderLevel). \
                        filter(Components.ReorderLevel != ""). \
                        order_by(Components.Name)
    else:
        query_obj = session.query(Components.ID, Components.Name, Components.CurrentStock,
                                  Components.ReorderLevel, Components.UnitPrice, Suppliers.Name,
                                  Locations.Name, Components.Datasheet). \
                        outerjoin(Suppliers, Components.SuppliersID == Suppliers.ID). \
                        outerjoin(Locations, Components.LocationsID == Locations.ID). \
                        order_by(Components.Name)
    return query_obj


def initcomponentform():
    """
    Create and then initialise form object with list attributes
    :return:
    """
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
    form = initcomponentform()
    query_obj = createlistquery(filtered=filtered)
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


# Refactor and add POST method handling
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
    for feature in session.query(Features):
        form.feature.label.append(feature.Name)
        if feature.StrValue is not None:
            form.feature.name.append(feature.StrValue)
        else:
            form.feature.name.append(str(feature.IntValue))

    return render_template('componentform.html', form=form, numcats=len(form.categoryid.id),
                           numfeatures=len(form.feature.label), readlock='True')


# Needs refactoring
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


# Static Data Maintenance menu
@app.route('/datamaint')
def datamaintmenu():
    menu = HtmlMenu('Stock Data Maintenance Menu')
    menu.url.append('/maintstaticdata/component')
    menu.label.append('Add/Maintain Components')
    menu.url.append('/maintstaticdata/category')
    menu.label.append('Add/Maintain Categories')
    menu.url.append('/maintstaticdata/location')
    menu.label.append('Add/Maintain Locations')
    menu.url.append('/maintstaticdata/supplier')
    menu.label.append('Add/Maintain Suppliers')
    menu.url.append('/maintstaticdata/feature')
    menu.label.append('Add/Maintain Features')
    menu.url.append('/fileupload')
    menu.label.append('Upload a CSV formatted file')
    return render_template('menu.html', menu=menu, numrows=len(menu.url))


def createstaticquery(querymodel):
    """
    Build a query object
    :return: orm query object
    """
    queryobj = session.query(querymodel). \
        order_by(querymodel.Name)
    return queryobj


def initstaticform(formtemplate=BasicForm):
    """
    Create and then initialise form object with list attributes
    :return:
    """
    return formtemplate()


def setquerytable(option):
    if option == 'component':
        querytable = Components
        pagetitle = 'Components'
    elif option == 'category':
        querytable = Categories
        pagetitle = 'Categories'
    elif option == 'location':
        querytable = Locations
        pagetitle = 'Locations'
    elif option == 'supplier':
        querytable = Suppliers
        pagetitle = 'Suppliers'
    elif option == 'feature':
        querytable = Features
        pagetitle = 'Features'
    else:
        querytable = Locations
        pagetitle = 'Invalid Option'
        option = None
    return option, querytable, pagetitle


def populatelist(option):
    form = []
    option, querytable, pagetitle = setquerytable(option)
    if option is None:
        form.append(initstaticform())
    queryobj = createstaticquery(querytable)
    for data_row in queryobj:
        if option == 'component':
            form.append(initstaticform(ComponentsForm))
        elif option == 'category':
            form.append(initstaticform())
        elif option == 'location':
            form.append(initstaticform(LocationsForm))
            if data_row.Sublocation:
                form[-1].sublocation.value = data_row.Sublocation
        elif option == 'supplier':
            form.append(initstaticform(SuppliersForm))
            if data_row.Website:
                form[-1].website.value = data_row.Website
        elif option == 'feature':
            form.append(initstaticform(FeaturesForm))
            if data_row.StrValue:
                form[-1].strvalue.value = data_row.StrValue
            if data_row.IntValue:
                form[-1].intvalue.value = data_row.IntValue
        form[-1].name.value = data_row.Name
        if data_row.Description:
            form[-1].description.value = data_row.Description
    return option, pagetitle, form


@app.route("/maintstaticdata/<option>", methods=['GET', 'POST'])
def maintstaticdata(option='component'):
    (option, pagetitle, form) = populatelist(option)
    return render_template('maintstatic.html', statictitle=pagetitle, form=form,
                           numrows=len(form), option=option)


@app.route("/fileupload", methods=['GET', 'POST'])
def fileupload():
    if request.method == 'POST':
        fileload = loadfile(request.form['uploadfile'], session)
        return render_template('fileloadstatus.html', statustext=fileload.filestatus)

    else:
        return render_template('fileupload.html')


def setform(option, req):
    if option == 'component':
        form = ComponentsForm(req)
    elif option == 'category':
        form = BasicForm(req)
    elif option == 'location':
        form = LocationsForm(req)
    elif option == 'supplier':
        form = SuppliersForm(req)
    elif option == 'feature':
        form = FeaturesForm(req)
    else:
        form = BasicForm()
    return form


def checknew(option, *argv):
    arglst = []
    for arg in argv:
        arglst.append(arg)
    name = arglst[0]
    if option == 'component':
        querytable = Components
        qry = session.query(querytable).filter(querytable.Name == name)
    elif option == 'category':
        querytable = Categories
        qry = session.query(querytable).filter(querytable.Name == name)
    elif option == 'location':
        querytable = Locations
        sublocation = arglst[1]
        qry = session.query(querytable).filter(querytable.Name == name).\
            filter(querytable.Sublocation == sublocation)
    elif option == 'supplier':
        querytable = Suppliers
        qry = session.query(querytable).filter(querytable.Name == name)
    elif option == 'feature':
        querytable = Features
        qry = session.query(querytable).filter(querytable.Name == name)
    else:
        querytable = Locations
        qry = session.query(querytable).filter(querytable.Name == name)

    try:
        qry.one()
        return False
    except NoResultFound:
        return True


def getnewstaticid(table):
    qry = session.query(func.max(table.ID))
    return getnextid(session, qry)


def adddata(option, form):
    if option == 'component':
        querytable = Components
    elif option == 'category':
        querytable = Categories
        staticid = getnewstaticid(Categories)
        add_category = Categories(ID=staticid, Name=form.name.data, Description=form.description.data)
        session.add(add_category)
    elif option == 'location':
        staticid = getnewstaticid(Locations)
        add_location = Locations(ID=staticid, Name=form.name.data, Description=form.description.data,
                                 Sublocation=form.sublocation.data)
        session.add(add_location)
    elif option == 'supplier':
        staticid = getnewstaticid(Suppliers)
        add_supplier = Suppliers(ID=staticid, Name=form.name.data, Description=form.description.data,
                                 Website=form.website.data)
        session.add(add_supplier)
    elif option == 'feature':
        staticid = getnewstaticid(Features)
        add_data = Features(ID=staticid, Name=form.name.data, Description=form.description.data,
                                 StrValue=form.strvalue.data, IntValue=form.intvalue.data)
        session.add(add_data)
    else:
        querytable = Locations
    session.commit()


@app.route('/add/<option>', methods=['GET', 'POST'])
def addelement(option=None):
    form = setform(option, request.form)
    if request.method == 'POST':
        if option == 'location':
            if checknew(option, form.name.data, form.sublocation.data):
                adddata(option, form)
        else:
            if checknew(option, form.name.data):
                adddata(option, form)

        (option, pagetitle, form) = populatelist(option)
        return render_template('maintstatic.html', statictitle=pagetitle, form=form,
                               numrows=len(form), option=option)
    else:
        if option == 'supplier':
            form = SuppliersForm()
        elif option == 'location':
            form = LocationsForm()
        elif option == 'feature':
            form = FeaturesForm()
        else:
            form = None
    return render_template('addelement.html', form=form, statictitle=option)


if __name__=='__main__':
    app.run(host='0.0.0.0',debug=True)