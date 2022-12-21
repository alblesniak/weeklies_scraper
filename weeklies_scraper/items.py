from scrapy import Item, Field
from itemloaders.processors import TakeFirst, Join


class WeekliesScraperItem(Item):
    issue_name = Field(output_processor=TakeFirst())
    issue_number = Field(output_processor=TakeFirst())
    issue_year = Field(output_processor=TakeFirst())
    issue_url = Field(output_processor=TakeFirst())
    issue_cover_url = Field(output_processor=TakeFirst())
    section_name = Field(output_processor=TakeFirst())
    article_title = Field(output_processor=TakeFirst())
    article_intro = Field(output_processor=TakeFirst())
    article_authors = Field(output_processor=Join(", "))
    article_url = Field(output_processor=TakeFirst())
    article_content = Field(output_processor=Join(" "))
    article_tags = Field(output_processor=Join(", "))
