import os
from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    MetaData,
    ForeignKey,
)
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def create_user_table():
    user_table = """

    DROP TABLE users CASCADE
    """
    db.execute(user_table)
    db.commit()


def create_feedback_table():
    feedback_table = """
    DROP TABLE feedbacks;
    """
    db.execute(feedback_table)
    db.commit()


def create_admin_table():
    admin_table = """
    DROP TABLE admin
    """
    db.execute(admin_table)
    db.commit()


if __name__ == "__main__":
    create_user_table()
    create_feedback_table()
    create_admin_table()
