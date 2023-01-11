from weeklies_scraper.items import WeekliesScraperItem
from scrapy.exceptions import DropItem
import re
import sqlite3


class FullfillDataPipeline(object):
    def __init__(self):
        self.keys_to_check = ['article_authors', 'article_tags',
                              'article_intro', 'section_name', 'issue_cover_url']

    def process_item(self, item, spider):
        for key in self.keys_to_check:
            if key not in item.keys():
                item[key] = None
        return item


class ShortestPipeline(object):
    def process_item(self, item, spider):
        if item['article_content'] == None or len(item['article_content']) < 100:
            raise DropItem("Item shorter than 100: %s" % item)
        else:
            return item


class TextCleanerPipeline(object):
    def process_item(self, item, spider):
        # Split the string on the newline character
        # Remove empty lines using a list comprehension
        # Join the list of non-empty lines back into a single string
        if item['article_content']:
            lines_content = item['article_content'].split('\n')
            lines_content = [line.strip()
                             for line in lines_content if line != '']
            item['article_content'] = '\n'.join(lines_content).strip()
        if item['article_intro']:
            lines_intro = item['article_intro'].split('\n')
            lines_intro = [line.strip() for line in lines_intro if line != '']
            item['article_intro'] = '\n'.join(lines_intro).strip()
        return item


class ScriptStripperPipeline(object):
    def process_item(self, item, spider):
        # Remove HTML, JavaScript, and CSS scripts using regular expressions
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
        # Check if the item is a WeekliesScraperItem
        if isinstance(item, WeekliesScraperItem):
            try:
                # Check if the issue_url already exists in the issues table
                self.cursor.execute(
                    "SELECT id FROM issues WHERE issue_url = ?", (
                        item["issue_url"],)
                )
                result = self.cursor.fetchone()
                # If the issue_url does not exist, insert the issue data into the issues table and get the id of the inserted issue
                if result is None:
                    self.cursor.execute(
                        "INSERT INTO issues (issue_name, issue_year, issue_number, issue_url, issue_cover_url) VALUES (?, ?, ?, ?, ?)",
                        (
                            item["issue_name"],
                            int(item["issue_year"]),
                            item["issue_number"],
                            item["issue_url"],
                            item["issue_cover_url"],
                        ),
                    )
                    issue_id = self.cursor.execute("SELECT last_insert_rowid()").fetchone()[
                        0
                    ]
                # If the issue_url already exists, get the id of the existing issue
                else:
                    issue_id = result[0]
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

    def close_spider(self, spider):
        self.conn.close()
