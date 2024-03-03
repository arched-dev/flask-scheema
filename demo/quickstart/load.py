import datetime
from typing import Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flask_scheema import Naan

class BaseModel(DeclarativeBase):
    def get_session(*args):
        # you must add a method to your base model called get session that returns a sqlalchemy session for the
        # auto api creator to work.
        return db.session

app = Flask(__name__)


db = SQLAlchemy(model_class=BaseModel)

app.config['API_TITLE'] = 'My API'
app.config['API_VERSION'] = '1.0'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['API_BASE_MODEL'] = db.Model

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
    db.init_app(app)
    db.create_all()
    scheema = Naan(app)


if __name__ == '__main__':

    app.run(debug=True)
