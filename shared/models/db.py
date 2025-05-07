import os
import ormar
import sqlalchemy
from databases import Database


def get_db_url(driver="aiomysql", server="db"):
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    db = os.getenv("MYSQL_DATABASE")
    return f"mysql+{driver}://{user}:{password}@{server}/{db}"


DATABASE_URL = get_db_url()
database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

ormar_base_config = ormar.OrmarConfig(
    database=database,
    metadata=metadata,
)
