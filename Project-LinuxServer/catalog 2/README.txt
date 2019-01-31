Project Description:

This project creates an online catalog of sports items, specifically for Soccer, Baseball and Basketball.
The catalog is open for anybody to browse.
Users can login using their Google credentials. This enables them to add, edit or delete items to/from the sports catagories.
However, a record of which user created the item prevents an user from editing or deleting an item that some other user created and hence owns.

Project dependencies:
1. Flask
2. SQLalchemy
3. Google APIs oauth2client

Instructions:

1. Once in the 'catalog' directory, setup the database first. To do this, run cmd 'python db_setup.py'. 
2. To start the local application server, run cmd 'python application.py'
3. In the browser please visit 'http://localhost:5000/' or 'http://localhost:5000/catalog' to access the catalog application homepage.
4. Links and buttons on the pages should take you to through the application there onwards.
5. The website also offers two json endpoints to query for categories available ('http://localhost:5000/catalog/json') and the items available within each ('http://localhost:5000/catalog/<category>/items/json').
