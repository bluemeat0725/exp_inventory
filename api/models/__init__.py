from connector.sql import sync_db_engine
from .base import *
from .user_model import *


def init_db():
    from connector.sql import sync_get_db
    db = next(sync_get_db())

    Base.metadata.create_all(bind=sync_db_engine)
    db.commit()
