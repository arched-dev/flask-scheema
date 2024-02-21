# Demo - Flask-Scheema

## Basic

To spin up your first API using flask-scheema, you need to change your flask app very little to get a fully functioning 
API along with an OpenAPI redoc documentation page.

1) Subclass `DeclarativeBase` and pass to Flask-Sqlalchemy [Example](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/extensions.py#L10-L25)
2) Appy a few flask config values   [Example](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/config.py#L12-L14)
3) Initialise the `FlaskScheema` class with your apps `app_context` after all other extensions have been created and initialised [Example](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/extensions.py#L26) [Example1](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/__init__.py#L28)
4) Optionally add a `Meta` class to your sqlalchemy models with a `tag` & `tag_group` to organise the documentation.   [Example1](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/models.py#L32-L36)


### Subclass `DeclarativeBase`

Your models must inherit from a base class that has a method called `get_session` that returns a sqlalchemy session. 
This is so the API can access the database to create the correct schemas and to query the database.

If you are using flask-sqlalchemy, the below works perfectly.

```python
from sqlalchemy.orm import DeclarativeBase

class BaseModel(DeclarativeBase):

    def get_session(*args):
        # you must add a method to your base model called get session that returns a sqlalchemy session for the
        # auto api creator to work.
        return db.session
    
db = SQLAlchemy(model_class=BaseModel)
```
Make sure all of your models inherit from `db.Model` like normal as the above `model_class` is already handling everything 
for you.

### Required flask Config values are:
```
API_BASE_MODEL = db.Model  # This can be any base model as above, but if using flask-sqlalchemy, pass db.Model 
API_TITLE = "Book Shop API"
API_VERSION = "0.1.0"
```

### Sqlalchemy models must have a `Meta` class with the following attributes:

```python
class Meta:
    tag_group = "People/Companies"
    tag = "Author"
```

After this you can run your app and visit the `/docs` route to see your API documentation.
