import datetime
from typing import Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flask_scheema import Naan

# Create a base model that all models will inherit from. This is a requirement for the auto api creator to work.
# Don't, however, add to any of your models when using flask-sqlalchemy, instead, inherit from `db.model` as you
# would normally.
class BaseModel(DeclarativeBase):
    def get_session(*args):
        return db.session

# Create a new flask app
app = Flask(__name__)

# Create a new instance of the SQLAlchemy object and pass in the base model you have created.
db = SQLAlchemy(model_class=BaseModel)

# Set the database uri to an in memory database for this example.
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"

# Set the required fields for flask-scheema to work.
app.config['API_TITLE'] = 'My API'
app.config['API_VERSION'] = '1.0'
app.config['API_BASE_MODEL'] = db.Model

# Create a new model that inherits from db.Model
class Author(db.Model):
    __tablename__ = "author"
    class Meta:
        # all models should have class Meta object and the following fields which defines how the model schema's are
        # references in redocly api docs.
        tag_group = "People/Companies"
        tag = "Author"

    id: Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    biography: Mapped[str] = mapped_column(Text)
    date_of_birth: Mapped[datetime] = mapped_column(Date)
    nationality: Mapped[str] = mapped_column(String)
    website: Mapped[Optional[str]] = mapped_column(String)


with app.app_context():
    # initialize the database with the app context
    db.init_app(app)
    # create the database tables
    db.create_all()
    # initialize the Naan object with the app context
    Naan(app)

# Run the app
if __name__ == '__main__':

    app.run(debug=True)

# To access the API documentation, navigate to http://localhost:5000/docs
