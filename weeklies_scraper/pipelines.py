from scrapy.utils.project import get_project_settings
from weeklies_scraper.items import WeekliesScraperItem
import re
import sqlite3
import os


class ExtractOrConcatenatePipeline(object):
    def process_item(self, item, spider):
        # Define the output processor
        def extract_or_concatenate(values):
            if len(values) == 1:
                # Extract the single value if there is only one element
                return values[0]
            else:
                # Concatenate the values if there are multiple elements
                return " ".join(values)

        # Iterate over the fields of the item object
        for field in item.fields:
            # If the field is a list, extract or concatenate
            if isinstance(item.get(field), list):
                print(item.fields[field])
                # Set the output processor for the field
                item.fields[field].output_processor = extract_or_concatenate

        # Ensure that the article_content field is a string
        article_content = item["article_content"]
        if isinstance(article_content, list):
            # Concatenate the elements of the list into a single string
            item["article_content"] = " ".join(article_content)
        else:
            # Ensure that the article_content field is a string
            item["article_content"] = str(article_content)

        return item


class TextCleanerPipeline(object):
    def process_item(self, item, spider):
        """Clean the text fields of the item object.

        Args:
            item (scrapy.Item): The item object to be processed.
            spider (scrapy.Spider): The spider that generated the item.

        Returns:
            scrapy.Item: The processed item object.
        """
        # Iterate over the fields of the item object
        for field in item.fields:
            # If the field is a string, clean the text
            if isinstance(item.get(field), str):
                # Remove multiple spaces and newlines
                item[field] = re.sub(r"\s+", " ", item[field])
                # Strip leading and trailing whitespace
                item[field] = item[field].strip()
        return item


class ScriptStripperPipeline(object):
    def process_item(self, item, spider):
        # Check if the item is a WeekliesScraperItem
        if isinstance(item, WeekliesScraperItem):
            # Remove HTML, JavaScript, and CSS scripts using regular expressions
            # The first regular expression removes all script tags and their contents
            # The second regular expression removes all style tags and their contents
            # The third regular expression removes all other HTML tags
            item["article_content"] = re.sub(
                r"<script.*?</script>", "", item["article_content"]
            )
            item["article_content"] = re.sub(
                r"<style.*?</style>", "", item["article_content"]
            )
            item["article_content"] = re.sub(
                r"<[^>]*>", "", item["article_content"])
        return item


class SQLitePipeline(object):
    def __init__(self):
        # Connect to the database and create the tables
        with sqlite3.connect("scrapy_data.db") as conn:
            self.conn = conn
            self.cursor = conn.cursor()
            self.create_tables()

    def create_tables(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS issues (id INTEGER PRIMARY KEY AUTOINCREMENT, issue_name TEXT, issue_year INTEGER, issue_number INTEGER, issue_url TEXT UNIQUE, issue_cover_url TEXT)"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS articles (id INTEGER PRIMARY KEY AUTOINCREMENT, section_name TEXT, article_title TEXT, article_authors TEXT, article_intro TEXT, article_url TEXT UNIQUE, article_content TEXT, article_tags TEXT, issue_id INTEGER, FOREIGN KEY(issue_id) REFERENCES issues(id))"
        )

    def process_item(self, item, spider):
        # print(item)
        # Check if the item is a WeekliesScraperItem
        if isinstance(item, WeekliesScraperItem):
            try:
                # Insert the issue data into the issues table
                self.cursor.execute(
                    "INSERT OR IGNORE INTO issues (issue_name, issue_year, issue_number, issue_url, issue_cover_url) VALUES (?, ?, ?, ?, ?)",
                    (
                        item["issue_name"],
                        int(item["issue_year"]),
                        item["issue_number"],
                        item["issue_url"],
                        item["issue_cover_url"],
                    ),
                )
                # Get the id of the inserted issue
                issue_id = self.cursor.execute("SELECT last_insert_rowid()").fetchone()[
                    0
                ]
                # Insert the article data into the articles table
                self.cursor.execute(
                    "INSERT OR IGNORE INTO articles (section_name, article_title, article_authors, article_intro, article_url, article_content, article_tags, issue_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        item["section_name"],
                        item["article_title"],
                        item["article_authors"],
                        item["article_intro"],
                        item["article_url"],
                        item["article_content"],
                        item["article_tags"],
                        issue_id,
                    ),
                )
                self.conn.commit()
            except Exception as e:
                print(e)
                self.conn.rollback()
        return item
