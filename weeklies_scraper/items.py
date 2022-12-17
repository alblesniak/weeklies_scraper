from scrapy.item import Item, Field


class WeekliesScraperItem(Item):
    issue_name = Field()
    issue_number = Field()
    issue_year = Field()
    issue_url = Field()
    issue_cover_url = Field()
    section_name = Field()
    article_title = Field()
    article_intro = Field()
    article_authors = Field()
    article_url = Field()
    article_content = Field()
    article_tags = Field()
