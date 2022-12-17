# Import the necessary modules from SQLAlchemy
from sqlalchemy import create_engine, Column, Table, ForeignKey, MetaData
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Date, DateTime, Float, Boolean, Text

# Import the get_project_settings function from the scrapy module
from scrapy.utils.project import get_project_settings

# Create a base class for the declarative ORM
Base = declarative_base()


def db_connect():
    """
    Performs database connection using database settings from settings.py.
    Returns a SQLAlchemy engine instance.
    """
    # Use the get_project_settings function to get the CONNECTION_STRING value
    # from the settings.py file, and pass it to the create_engine function to
    # create a new database engine.
    return create_engine(get_project_settings().get("CONNECTION_STRING"))


def create_table(engine):
    """
    Creates the table in the database using the engine instance.
    """
    Base.metadata.create_all(engine)


class Issue(Base):
    """
    ORM class for the 'issue' table.
    """

    # Set the name of the table
    __tablename__ = "issue"

    # Define the columns of the table, along with their types and any additional
    # options such as primary keys, nullability, and uniqueness
    id = Column(Integer, primary_key=True)
    name = Column("name", Text(), nullable=False)
    number = Column("number", Text(), nullable=False)
    cover_url = Column("cover_url", Text())
    issue_url = Column("issue_url", Text(), nullable=False, unique=True)

    # Define a relationship to the Article ORM class, using the back_populates
    # option to specify the name of the relationship in the Article class.
    article = relationship("Article", back_populates="issue")


class Article(Base):
    """
    ORM class for the 'article' table.
    """

    # Set the name of the table
    __tablename__ = "article"

    # Define the columns of the table, along with their types and any additional
    # options such as primary keys, nullability, and uniqueness
    id = Column(Integer(), primary_key=True)
    section_name = Column("section_name", Text())
    title = Column("title", Text(), nullable=False)
    authors = Column("authors", Text())
    url = Column("article_url", Text(), unique=True)
    tags = Column("tags", Text())
    intro = Column("intro", Text())
    content = Column("content", Text())
    issue_id = Column("issue_id", ForeignKey("issue.id"))

    # Define a relationship to the Issue ORM class, using the back_populates
    # option to specify the name of the relationship in the Issue class.
    issue = relationship("Issue", back_populates="article")
