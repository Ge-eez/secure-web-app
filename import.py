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
    CREATE TABLE users (
          id SERIAL PRIMARY KEY,
          username VARCHAR NOT NULL,
          email VARCHAR NOT NULL UNIQUE,
          password VARCHAR NOT NULL
      )
    """
    db.execute(user_table)
    db.commit()


def create_feedback_table():
    feedback_table = """
    CREATE TABLE feedbacks (
          id SERIAL PRIMARY KEY,
          title VARCHAR NOT NULL,
          content TEXT,
          attachment VARCHAR,
          timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
          user_id INTEGER REFERENCES users
      )
    """
    db.execute(feedback_table)
    db.commit()


def create_admin_table():
    admin_table = """
    CREATE TABLE admin (
          id SERIAL PRIMARY KEY,
          username VARCHAR NOT NULL UNIQUE,
          password VARCHAR NOT NULL
      )
    """
    db.execute(admin_table)
    db.commit()


if __name__ == "__main__":
    create_user_table()
    create_feedback_table()
    create_admin_table()
