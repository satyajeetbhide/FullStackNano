from flask import Flask
from flask import request, render_template, redirect, url_for
from flask import session as login_session
from flask import make_response, flash, g

from sqlalchemy import create_engine, and_, exists

from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, Item

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

import httplib2
import json
import requests
from collections import deque
import random
import string
from functools import wraps

app = Flask(__name__)

engine = create_engine('postgres://catalog:dbadmin@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
db_session = DBSession()

CLIENT_ID = json.loads(open('/var/www/FLASKAPPS/catalogapp/client_secrets.json', 'r').read())[
    'web']['client_id']
recentItems = deque('')

def pushItemToRecents(category, item):
    if (category, item) in recentItems:
        recentItems.remove((category, item))
    if len(recentItems) >= 5:
        recentItems.pop()
    recentItems.appendleft((category, item))


def user_authorized(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        db_session = DBSession()
        item = db_session.query(Item).filter_by(
            name=kwargs.get('item', '')).one_or_none()
        if item:
            if item.owner_email == login_session['email']:
                return func(*args, **kwargs)
            else:
                flash("User not authorized to perform this action.")
                return redirect(url_for('index'))
        else:
            flash("Invalid Item.")
            return redirect(url_for('index'))
    return wrapper


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if login_session['user_logged_in']:
                return func(*args, **kwargs)
            else:
                return redirect(url_for('login'))
        except KeyError:
            return redirect(url_for('login'))
    return wrapper


@app.route('/login', methods=['GET'])
def login():
    state = ''.join(
        random.choice(
            string.ascii_uppercase +
            string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:  # CSRF check
        response = make_response(
            json.dumps('Invalid State params'), status=401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data
    try:
        oauthflow = flow_from_clientsecrets('/var/www/FLASKAPPS/catalogapp/client_secrets.json', scope='')
        oauthflow.redirect_uri = 'postmessage'
        credentials = oauthflow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response('Failed to upgrade auth code', 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += (' " style = "width: 300px; height: 300px;border-radius: 150px;'
               '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> ')
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    login_session['user_logged_in'] = True
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = ('https://accounts.google.com/o/'
           'oauth2/revoke?token=%s') % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        login_session['user_logged_in'] = False
        flash("Successfully disconnected.")
        return redirect(url_for('index'))
    else:
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.',
                400))
        response.headers['Content-Type'] = 'application/json'
        login_session.clear()
        flash("Failed to revoke token for given user. \
                Resetting user session. Please login again.")
        return redirect(url_for('index'))


@app.route('/', methods=['GET'])
@app.route('/catalog', methods=['GET'])
def index():
    # This is done as a workaround for "ProgrammingError: SQLite objects
    # created in a thread can only be used in that same thread."
    db_session = DBSession()
    categories = db_session.query(Category.name).all()
    recents = list(recentItems)
    return render_template("catalog_index.html", **locals())

@app.route('/catalog/<path:category>/items', methods=['GET'])
def category_index(category):
    # This is done as a workaround for "ProgrammingError: SQLite objects
    # created in a thread can only be used in that same thread."
    db_session = DBSession()
    categories = [c.name for c in db_session.query(Category).all()]
    category_obj = db_session.query(Category).filter_by(name=category).one_or_none()
    items = [r.name for r in db_session.query(
        Item).filter_by(category_id=category_obj.id)]

    return render_template("category_index.html", **locals())

@app.route('/catalog/<path:category>/<path:item>/delete', methods=['POST'])
@login_required
@user_authorized
def delete_item(category, item):
    # This is done as a workaround for "ProgrammingError: SQLite objects
    # created in a thread can only be used in that same thread."
    db_session = DBSession()
    category_obj = db_session.query(Category).filter_by(name=category).one_or_none()
    curr_item = db_session.query(Item).filter_by(name=item, category_id=category_obj.id).one_or_none()
    if curr_item:
        db_session.delete(curr_item)
        db_session.commit()
        recentItems.remove((category, item))
    return redirect(url_for('category_index', category=category))

@app.route('/catalog/<path:category>/<path:item>/edit',
           methods=['GET', 'POST'])
@login_required
@user_authorized
def edit_item(category, item):
    # This is done as a workaround for "ProgrammingError: SQLite objects
    # created in a thread can only be used in that same thread."
    db_session = DBSession()
    if request.method == 'GET':
        category_obj = db_session.query(Category).filter_by(name=category).one_or_none()
        curr_item = db_session.query(Item).filter_by(name=item, category_id=category_obj.id).one_or_none()
        categories = [c.name for c in db_session.query(Category).all()]
        return render_template(
            "edit_item.html", item=curr_item, categories=categories,
            category=category)
    else:
        category_obj = db_session.query(Category).filter_by(name=category).one_or_none()
        curr_item = db_session.query(Item).filter_by(name=item, category_id=category_obj.id).one_or_none()
        if not curr_item:
            return redirect(url_for('index'))
        curr_item.name = request.form.get('name')
        curr_item.description = request.form.get('description')
        curr_item.category = db_session.query(Category).filter_by(
            name=request.form.get('category')).one()
        db_session.commit()

        recentItems.remove((category, item))
        pushItemToRecents(request.form.get('category'), curr_item.name)
        return redirect(
            url_for('item_index', category=request.form.get('category'),
                    item=curr_item.name))

@app.route('/catalog/<path:category>/<path:item>', methods=['GET'])
def item_index(category, item):
    # This is done as a workaround for "ProgrammingError: SQLite objects
    # created in a thread can only be used in that same thread."
    db_session = DBSession()
    curr_item = db_session.query(Item).filter_by(name=item).one_or_none()
    if curr_item:
        pushItemToRecents(category, item)
        return render_template(
            "item_index.html", item=curr_item, category=category)
    else:
        return redirect(url_for('index'))

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    # This is done as a workaround for "ProgrammingError: SQLite objects
    # created in a thread can only be used in that same thread."
    db_session = DBSession()
    if request.method == 'POST':
        # Create item
        # Make sure another item by the same name does not exist in the
        # category
        category_obj = db_session.query(Category).filter_by(name=request.form.get('category')).one_or_none()
        already_exists = db_session.query(exists().where(
            and_(Item.name == request.form.get('name'),
                 Item.category_id == category_obj.id))).scalar()
        if (already_exists):
            flash("This item already exists")
            return redirect(url_for('add_item'))

        newitem = Item(name=request.form.get('name'),
                       description=request.form.get('description', ''),
                       category=db_session.query(Category).filter_by(
                           name=request.form.get('category')).one(),
                       owner_email=login_session['email'])
        db_session.add(newitem)
        db_session.commit()
        return redirect(
            url_for('item_index', category=request.form.get('category'),
                    item=newitem.name))
    else:
        categories = [c.name for c in db_session.query(Category).all()]
        category = request.args.get('category', None)
        return render_template('add_item.html', **locals())

@app.route('/catalog/json', methods=['GET'])
def catalog_data():
    # This is done as a workaround for "ProgrammingError: SQLite objects
    # created in a thread can only be used in that same thread."
    db_session = DBSession()
    categories = db_session.query(Category).all()
    ret = []
    for cat in categories:
        ret.append({
            'id': cat.id,
            'name': cat.name
        })
    return json.dumps(ret)


@app.route('/catalog/<path:category>/items/json', methods=['GET'])
def catalog_items_data(category):
    # This is done as a workaround for "ProgrammingError: SQLite objects
    # created in a thread can only be used in that same thread."
    db_session = DBSession()
    category_obj = db_session.query(Category).filter_by(name=category).one_or_none()
    items = [r for r in db_session.query(
        Item).filter_by(category_id=category_obj.id)]
    ret = []
    for item in items:
        ret.append({
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'category': category_obj.name
        })
    return json.dumps(ret)


@app.route('/catalog/<path:category>/<path:item>/json', methods=['GET'])
def catalog_item_data(category, item):
    # This is done as a workaround for "ProgrammingError: SQLite objects
    # created in a thread can only be used in that same thread."
    db_session = DBSession()
    category_obj = db_session.query(Category).filter_by(name=category).one_or_none()
    item = db_session.query(
        Item).filter_by(name=item, category_id=category_obj.id).one_or_none()
    if item:
        ret = json.dumps({
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'category': category_obj.name
        })
    else:
        ret = ''

    return ret



app.secret_key = 'super secret key'
if __name__ == "__main__":
    app.run()