from scrapy.utils.project import get_project_settings
from weeklies_scraper.items import WeekliesScraperItem
import re
import sqlite3
import os


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
            item["article_content"] = re.sub(r"<[^>]*>", "", item["article_content"])
        return item

    # class SQLitePipeline(object):
    # def __init__(self):
    #     # Get the connection string from the Scrapy settings
    #     connection_string = get_project_settings().get("CONNECTION_STRING")
    #     # Check if the database file specified in the connection string exists
    #     if not os.path.exists(connection_string):
    #         # Create the database file if it does not exist
    #         open(connection_string, "w").close()
    #     # Connect to the database and create the tables
    #     self.conn = sqlite3.connect(connection_string)
    #     self.conn.execute(
    #         "CREATE TABLE IF NOT EXISTS issues (id INTEGER PRIMARY KEY AUTOINCREMENT, issue_name TEXT, issue_year INTEGER, issue_number INTEGER, issue_url TEXT, issue_cover_url TEXT)"
    #     )
    #     self.conn.execute(
    #         "CREATE TABLE IF NOT EXISTS articles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, author TEXT, content TEXT, date TEXT, section_name TEXT, article_url TEXT, issue_id INTEGER, FOREIGN KEY(issue_id) REFERENCES issues(id))"
    #     )

    # def process_item(self, item, spider):
    #     # Check if the item is a WeekliesScraperItem
    #     if isinstance(item, WeekliesScraperItem):
    #         # Insert the issue data into the issues table
    #         self.conn.execute(
    #             "INSERT INTO issues (issue_name, issue_year, issue_number, issue_url, issue_cover_url) VALUES (?, ?, ?, ?, ?)",
    #             (
    #                 item["issue_name"],
    #                 item["issue_year"],
    #                 item["issue_number"],
    #                 item["issue_url"],
    #                 item["issue_cover_url"],
    #             ),
    #         )
    #         # Get the id of the inserted issue
    #         issue_id = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    #         # Insert the article data into the articles table
    #         self.conn.execute(
    #             "INSERT INTO articles (name, author, content, date, section_name, article_url, issue_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
    #             (
    #                 item["name"],
    #                 item["author"],
    #                 item["content"],
    #                 item["date"],
    #                 item["section_name"],
    #                 item["article_url"],
    #                 issue_id,
    #             ),
    #         )
    #         self.conn.commit()
    #     return item

    # def close_spider(self, spider):
    #     # Close the database connection when the spider is closed
    #     self.conn.close()
