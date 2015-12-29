import os
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from forms import ComponentsForm, LocationsForm, SuppliersForm, BasicForm, FeaturesForm, CategoriesForm,\
    AddFeaturesForm, AddCategoriesForm, UpdateStockForm
from models import Components, Base, Locations, Suppliers, Categories, Definitions, Features, DefinedFeatures
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from componentsmodule import loadfile, Category, HtmlMenu, createdbsession, getnextid, SupplierObject,\
    LocationObject, FeatureObject, CategoryObject, NewComponent, FileLoad, ComponentObject, CategoryTree,\
    AddFeatureObject, AddCategoryObject, StockObject


__author__ = 'Bernard'


app = Flask(__name__)

# Load config and override config from an environment variable if defined
app.config.from_pyfile('components.cfg')
app.config.from_envvar('APP_SETTINGS', silent=True)

# Connect to database
session = createdbsession(app.config['DATABASE'], sqlecho=app.config['DBECHO'], cleardown=False)


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


catsearch = Category()


def createstaticquery(querymodel):
    queryobj = session.query(querymodel). \
        order_by(querymodel.Name)
    return queryobj


def initstaticform(formtemplate=BasicForm):
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
    elif option == 'addfeature':
        querytable = Features
        pagetitle = 'Features'
    elif option == 'addcategories':
        querytable = Categories
        pagetitle = 'Categories'
    elif option == 'updatestock':
        querytable = Components
        pagetitle = 'Update Stock Levels'
    else:
        querytable = Locations
        pagetitle = 'Invalid Option'
        option = None
    return option, querytable, pagetitle


def populatelist(option, *args):
    form = []
    option, querytable, pagetitle = setquerytable(option)
    if option is None:
        form.append(initstaticform())
    queryobj = createstaticquery(querytable)
    deleteoption = []
    addfeatureoption = []
    addcategoryoption = []
    updateoption = []
    optionobject = chooseobject(option)
    for data_row in queryobj:
        if option == 'addfeature' or option == 'addcategories':
            optionobject.componentid = args[0]
        form.append(optionobject.loadform(data_row, True))
        if option == 'component':
            form[-1].supplier.choices = [(a.ID, a.Name) for a in session.query(Suppliers).order_by('Name')]
            form[-1].location.choices = \
                [(a.ID, a.Name+'::'+a.Sublocation) for a in session.query(Locations).order_by('Name')]
            deleteoption.append('<a href="/delete/{}/{}">Del</a>'.format(option, data_row.ID))
            addfeatureoption.append('<a href="/addfeature/{}">Fea</a>'.format(data_row.ID))
            addcategoryoption.append('<a href="/addcategories/{}">Cat</a>'.format(data_row.ID))
            updateoption.append('<a href="/update/{}">Upd</a>'.format(data_row.ID))
        else:
            if optionobject is not None and option != 'addfeature' \
                    and option != 'addcategories' and option != 'updatestock':
                form[-1].components.data = optionobject.checkusage(data_row.ID)
                if form[-1].components.data == []:
                    deleteoption.append('<a href="/delete/{}/{}">Del</a>'.format(option, data_row.ID))
                else:
                    deleteoption.append('')
            else:
                deleteoption.append('')

    return option, pagetitle, form, deleteoption, addfeatureoption, addcategoryoption, updateoption


def setform(option, req=None, modify=False):
    if option == 'component':
        form = ComponentsForm(req)
    elif option == 'category':
        form = CategoriesForm(req)
    elif option == 'location':
        form = LocationsForm(req)
    elif option == 'supplier':
        form = SuppliersForm(req)
    elif option == 'feature':
        form = FeaturesForm(req)
    elif option == 'addfeature':
        form = AddFeaturesForm(req)
    elif option == 'addcategories':
        form = AddCategoriesForm(req)
    elif option == 'updatestock':
        form = UpdateStockForm(req)
    else:
        form = BasicForm()
    if modify:
        del form.components
    return form


def checknew(option, *argv):
    arglst = []
    for arg in argv:
        arglst.append(arg)
    name = arglst[0]
    option, querytable, notused = setquerytable(option)
    qry = session.query(querytable).filter(querytable.Name == name)
    if option == 'location':
        sublocation = arglst[1]
        qry = qry.filter(querytable.Sublocation == sublocation)
    elif option == 'feature':
        strvalue = arglst[1]
        intvalue = arglst[2]
        qry = qry.filter(querytable.StrValue == strvalue).filter(querytable.IntValue == intvalue)
    elif option == 'component':
        supplierid = arglst[1]
        locationid = arglst[2]
        qry = qry.filter(querytable.SuppliersID == supplierid).\
            filter(querytable.LocationsID == locationid)
    try:
        qry.one()
        return False
    except NoResultFound:
        return True


def getnewstaticid(table):
    qry = session.query(func.max(table.ID))
    return getnextid(session, qry)


def adddata(option, form):
    add_item = None
    if option == 'component':
        # Use the NewComponent object to add this
        fileobj = FileLoad('PASS', session)
        formdata = []
        sup = SupplierObject(session, Suppliers)
        form.supplier.data = sup.getdatabyid(form.supplier.data).Name
        loc = LocationObject(session, Locations)
        locdata = loc.getdatabyid(form.location.data)
        for field in form:
            if field.label.text == 'Location':
                fileobj.titles.append('Sublocation')
                formdata.append(locdata.Sublocation)
                fileobj.titles.append(field.label.text)
                formdata.append(locdata.Name)
            else:
                fileobj.titles.append(field.label.text)
                formdata.append(field.data)
        component = NewComponent(fileobj, formdata)
        status = component.parsedata()
        print status

    elif option == 'category':
        staticid = getnewstaticid(Categories)
        add_item = Categories(ID=staticid, Name=form.name.data, Description=form.description.data)
    elif option == 'location':
        staticid = getnewstaticid(Locations)
        add_item = Locations(ID=staticid, Name=form.name.data, Description=form.description.data,
                             Sublocation=form.sublocation.data)
    elif option == 'supplier':
        staticid = getnewstaticid(Suppliers)
        add_item = Suppliers(ID=staticid, Name=form.name.data, Description=form.description.data,
                             Website=form.website.data)
    elif option == 'feature':
        staticid = getnewstaticid(Features)
        add_item = Features(ID=staticid, Name=form.name.data, Description=form.description.data,
                            StrValue=form.strvalue.data, IntValue=form.intvalue.data)
    else:
        querytable = Locations
    if add_item is not None:
        session.add(add_item)
        session.commit()
        flash('Added {} {}'.format(option, form.name.data))


def chooseobject(option=None):
    if option == 'supplier':
        obj = SupplierObject(session, Suppliers)
    elif option == 'location':
        obj = LocationObject(session, Locations)
    elif option == 'feature':
        obj = FeatureObject(session, Features)
    elif option == 'category':
        obj = CategoryObject(session, Categories)
    elif option == 'component':
        obj = ComponentObject(session, Components)
    elif option == 'addfeature':
        obj = AddFeatureObject(session, Features)
    elif option == 'addcategories':
        obj = AddCategoryObject(session, Categories)
    elif option == 'updatestock':
        obj = StockObject(session, Components)
    else:
        obj = None
    return obj


@app.route('/')
def index():
    menu = HtmlMenu('Electronic Components Stock Management')
    menu.url.append('/categorysearch/0/0')
    menu.label.append('List By Category')
    menu.url.append('/showlist/0')
    menu.label.append('List All Components')
    menu.url.append('/showlist/1')
    menu.label.append('Low Stock Report')
    menu.url.append('/updatestock')
    menu.label.append('Update Stock Levels')
    menu.url.append('/datamaint')
    menu.label.append('Data Maintenance')
    return render_template('menu.html', menu=menu, numrows=len(menu.url))


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


# Refactor and add POST method handling
@app.route('/showcomponents/<componentid>', methods=['POST', 'GET'])
def showcomponents(componentid=None):
    if request.method == 'POST':
        pass

    componentobj = ComponentObject(session, Components)
    componentdata = session.query(Components). \
        filter(Components.ID == componentid).one()
    form = componentobj.loadform(componentdata, False)
    categorytree = []
    catsearch.reset()
    catsearchindex = 0
    for category in session.query(Definitions, Categories). \
            join(Categories, Definitions.CategoriesID == Categories.ID). \
            filter(Definitions.ComponentID == componentid).order_by(Definitions.CategoryOrder):
        categorytree.append(CategoryTree())
        categorytree[-1].id = category.Categories.ID
        categorytree[-1].name = category.Categories.Name
        categorytree[-1].listorder = catsearchindex + 1
        catsearch.listorder.append(catsearchindex + 1)
        catsearch.id.append(category.Categories.ID)
        catsearch.name.append(category.Categories.Name)
        catsearchindex += 1

    return render_template('componentform.html', form=form, categories=categorytree,
                           numfeatures=0, readlock='True')


# Needs refactoring
@app.route('/categorysearch/<categorylevel>/<categoryid>')
def categorysearch(categorylevel=None, categoryid=None):
    if categorylevel is not None and categoryid is not None:
        # print 'Category level & id {} {}'.format(categorylevel, categoryid)
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


@app.route("/maintstaticdata/<option>", methods=['GET', 'POST'])
def maintstaticdata(option='component'):
    (option, pagetitle, form, deleteoptions, addfeatureoptions, categoriesopt, updateoption) = populatelist(option)
    return render_template('maintstatic.html', statictitle=pagetitle, form=form,
                           numrows=len(form), option=option, deleteoption=deleteoptions,
                           featureoption=addfeatureoptions, categoryoption=categoriesopt, updateoption=updateoption)


@app.route("/fileupload", methods=['GET', 'POST'])
def fileupload():
    if request.method == 'POST':
        fileload = loadfile(request.form['uploadfile'], session)
        return render_template('fileloadstatus.html', statustext=fileload.filestatus)

    else:
        return render_template('fileupload.html')


@app.route('/add/<option>', methods=['GET', 'POST'])
def addelement(option=None):
    form = setform(option, request.form, modify=True)
    if request.method == 'POST':
        if option == 'location':
            if checknew(option, form.name.data, form.sublocation.data):
                adddata(option, form)
        elif option == 'feature':
            if checknew(option, form.name.data, form.strvalue.data, form.intvalue.data):
                adddata(option, form)
        elif option == 'component':
            if checknew(option, form.name.data, form.supplier.data, form.location.data):
                adddata(option, form)
        else:
            if checknew(option, form.name.data):
                adddata(option, form)

        (option, pagetitle, form, deleteoptions, addfeatureoptions, categoriesopt, updateoption) = populatelist(option)
        return render_template('maintstatic.html', statictitle=pagetitle, form=form,
                               numrows=len(form), option=option, deleteoption=deleteoptions,
                               featureoption=addfeatureoptions, categoryoption=categoriesopt,
                               updateoption=updateoption)
    else:
        form = setform(option, None, modify=True)
        if option == 'component':
            # Add suppliers choices
            form.supplier.choices = [(a.ID, a.Name) for a in session.query(Suppliers).order_by('Name')]
            # Add location choices
            form.location.choices = \
                [(a.ID, a.Name+'::'+a.Sublocation) for a in session.query(Locations).order_by('Name')]

    return render_template('addelement.html', form=form, statictitle=option)


@app.route('/delete/<option>/<elementid>', methods=['GET', 'POST'])
def deleteelement(option=None, elementid=None):
    obj = chooseobject(option)
    if request.method == 'POST':
        # confirm button was pressed and delete
        flash(obj.delete(elementid))
        # refresh the list
        (option, pagetitle, form, deleteoptions, addfeatureoptions, categoriesopt, updateoption) = populatelist(option)
        return render_template('maintstatic.html', statictitle=pagetitle, form=form,
                               numrows=len(form), option=option, deleteoption=deleteoptions,
                               featureoption=addfeatureoptions, categoryoption=categoriesopt,
                               updateoption=updateoption)
    else:
        form = obj.loadform(obj.getdatabyid(elementid), False)
    return render_template('delelement.html', form=form, statictitle=option, readlock='True', elementid=elementid)


@app.route('/addfeature/<componentid>', methods=['GET', 'POST'])
def addfeature(componentid=None):
    if request.method == 'POST':
        # first delete existing features defined
        # now save any that have been checked
        session.query(DefinedFeatures).filter(DefinedFeatures.ComponentID == componentid).delete()
        listorder = 0
        for addid in request.form.keys():
            listorder += 1
            additem = DefinedFeatures(ComponentID=componentid, FeatureID=addid[3:], ListOrder=listorder)
            session.add(additem)
            feature = session.query(Features).filter(Features.ID == addid[3:]).one()
            flash('Attached feature {}:{} to component.'.format(feature.Name, feature.StrValue))
        session.commit()
        option = 'component'
        (option, pagetitle, form, deleteoptions, addfeatureoptions, categoriesopt, updateoption) = populatelist(option)
        return render_template('maintstatic.html', statictitle=pagetitle, form=form,
                               numrows=len(form), option=option, deleteoption=deleteoptions,
                               featureoption=addfeatureoptions, categoryoption=categoriesopt,
                               updateoption=updateoption)
    else:
        option = 'addfeature'
        (option, pagetitle, form, deleteoptions, addfeatureoptions, categoriesopt, updateoption) = populatelist(option, componentid)
    return render_template('addfeature.html', form=form, statictitle=pagetitle, componentid=componentid)


@app.route('/addcategories/<componentid>', methods=['GET', 'POST'])
def addcategories(componentid=None):
    if request.method == 'POST':
        # first delete existing categories defined
        # now save any that have been checked
        session.query(Definitions).filter(Definitions.ComponentID == componentid).delete()
        tmpcomponent = ComponentObject(session, Components)
        tmpcompdata = tmpcomponent.getdatabyid(componentid)
        tmpcategory = CategoryObject(session, Categories)
        tmpcatdata = tmpcategory.getdatabyname(tmpcompdata.Name)
        listcount = 1
        for addid in request.form.keys():
            listorder = request.form[addid]
            if listorder != '':
                additem = Definitions(ComponentID=componentid, CategoriesID=addid[3:], CategoryOrder=listorder)
                session.add(additem)
                category = session.query(Categories).filter(Categories.ID == addid[3:]).one()
                flash('Attached category {} to component {}.'.format(category.Name, tmpcompdata.Name))
                listcount += 1
        additem = Definitions(ComponentID=componentid, CategoriesID=tmpcatdata.ID, CategoryOrder=listcount)
        session.add(additem)
        session.commit()
        option = 'component'
        (option, pagetitle, form, deleteoptions, addfeatureoptions, categoriesopt, updateoption) = populatelist(option)
        return render_template('maintstatic.html', statictitle=pagetitle, form=form,
                               numrows=len(form), option=option, deleteoption=deleteoptions,
                               featureoption=addfeatureoptions, categoryoption=categoriesopt,
                               updateoption=updateoption)
    else:
        option = 'addcategories'
        (option, pagetitle, form, deleteoptions, addfeatureoptions, categoriesopt, updateoption) = populatelist(option, componentid)
    return render_template('addcategories.html', form=form, statictitle=pagetitle, componentid=componentid)


@app.route('/updatestock', methods=['GET', 'POST'])
def updatestock():
    if request.method == 'POST':
        for updstock in request.form.keys():
            newstock = request.form[updstock]
            if newstock != '':
                upd = session.query(Components).filter(Components.ID == updstock[3:]).one()
                session.query(Components).filter(Components.ID == updstock[3:]).\
                    update({Components.CurrentStock: newstock})
                flash('Updated stock for component {} to {}.'.format(upd.Name, newstock))

        session.commit()
        return redirect(url_for('showlist', filtered=0))
    else:
        option = 'updatestock'
        (option, pagetitle, form, deleteoptions, addfeatureoptions, addcategories, updateoption) = populatelist(option)
    return render_template('updatestock.html', form=form, statictitle=pagetitle)


@app.route('/update/<componentid>', methods=['GET', 'POST'])
def updelement(componentid=None):
    option = 'component'
    form = setform(option, request.form, modify=True)
    tmcomponent = ComponentObject(session, Components)
    if request.method == 'POST':
        # Update the component
        flash(tmcomponent.update(componentid, request.form))
        (option, pagetitle, form, deleteoptions, addfeatureoptions, categoriesopt, updateoption) = populatelist(option)
        return render_template('maintstatic.html', statictitle=pagetitle, form=form,
                               numrows=len(form), option=option, deleteoption=deleteoptions,
                               featureoption=addfeatureoptions, categoryoption=categoriesopt,
                               updateoption=updateoption)
    else:
        # form = setform(option, None, modify=True)
        compdata = tmcomponent.getdatabyid(componentid)
        form = tmcomponent.loadform(compdata, False)
        if option == 'component':
            # Add suppliers choices
            form.supplier.choices = [(a.ID, a.Name) for a in session.query(Suppliers).order_by('Name')]
            # Add location choices
            form.location.choices = \
                [(a.ID, a.Name+'::'+a.Sublocation) for a in session.query(Locations).order_by('Name')]

    return render_template('updatecomponent.html', form=form, statictitle=option, componentid=componentid)


if __name__=='__main__':
    app.run(host='0.0.0.0',debug=True)