
from flask import current_app, g
from werkzeug.local import LocalProxy

from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.write_concern import WriteConcern
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson.objectid import ObjectId
from bson.errors import InvalidId
from pymongo.read_concern import ReadConcern


def get_db():
    """
    Configuration method to return db instance
    """
    db = getattr(g, "_database", None)
    DB_URI = current_app.config["DB_URI"]
    DB_NAME = current_app.config["NS"]
    if db is None:
        db = g._database = MongoClient(
        DB_URI,
        )[DB_NAME]
        print(db['__my_database__'])
    return db


# Use LocalProxy to read the global db instance with just `db`
db = LocalProxy(get_db)

def get_user_by_name(name):
    return db.users.find_one({'username' : name})
