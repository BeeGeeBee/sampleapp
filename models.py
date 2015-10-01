__author__ = 'Bernard'

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Locations(Base):
    __tablename__ = 'locations'
    ID = Column(Integer, primary_key=True)
    Name = Column(String(50))
    Description = Column(String(250))
    Sublocation = Column(String(50))


class Suppliers(Base):
    __tablename__ = 'suppliers'
    ID = Column(Integer, primary_key=True)
    Name = Column(String(50))
    Description = Column(String(250))
    Website = Column(String(250))


class Components(Base):
    __tablename__ = 'components'
    ID = Column(Integer, primary_key=True)
    Name = Column(String(50))
    Description = Column(String(250))
    CategoriesID = Column(Integer)
    SuppliersID = Column(Integer)
    CurrentStock = Column(Integer)
    ReorderLevel = Column(Integer)
    LocationsID = Column(Integer)
    Datasheet = Column(String(250))
    OrderCode = Column(String(50))
    UnitPrice = Column(Float)


class Categories(Base):
    __tablename__ = 'categories'
    ID = Column(Integer, primary_key=True)
    Name = Column(String(50))
    Description = Column(String(250))


class Definitions(Base):
    __tablename__ = 'definitions'
    ComponentID = Column(Integer, primary_key=True)
    CategoriesID = Column(Integer)
    CategoryOrder = Column(Integer)


class Features(Base):
    __tablename__ = 'features'
    ID = Column(Integer, primary_key=True)
    Name = Column(String(50))
    Description = Column(String(250))
    CategoriesID = Column(Integer)
    ListOrder = Column(Integer)
    StrValue = Column(String(50))
    IntValue = Column(Integer)