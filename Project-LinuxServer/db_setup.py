import sys
import json
import os
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

Base = declarative_base()

# --- Define DB Table Classes---


class Category(Base):  # Define Table
    __tablename__ = 'categories'  # Define Table
    # Mapper ORM code
    id = Column(Integer, primary_key=True)
    name = Column(String(80),  # 80 char string name
                  nullable=False  # Name string MUST be speficied
                  )


class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(100), nullable=True)
    # ForeignKey - Relationship
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship(Category)
    owner_email = Column(String(80), nullable=False)

# Remove old db
if os.path.exists('catalog.db'):
    os.remove('catalog.db')

engine = create_engine('postgres://catalog:dbadmin@localhost/catalog')
if not database_exists(engine.url):
    create_database(engine.url)

Base.metadata.create_all(engine)

# this makes the connection between our class definitions and the
# corresponding tables in the DB
Base.metadata.bind = engine
# this connects our code that follows and the engine (in turn the db).
DBSession = sessionmaker(bind=engine)
# a session collects all the sql commands and sends them all on 'commit'
session = DBSession()

# --- Populate DB Tables ---

categories = [
    'Soccer',
    'Basketball',
    'Baseball'
]

def clearDB():
    session.query(Item).delete()
    session.query(Category).delete()
    session.commit()

def populateDB():
    for cat in categories:
        newcat = Category(name=cat)
        session.add(newcat)
        session.commit()