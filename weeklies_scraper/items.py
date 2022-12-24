from scrapy import Item, Field
from itemloaders.processors import TakeFirst, Join


class WeekliesScraperItem(Item):
    issue_name = Field(output_processor=TakeFirst(), required=True)
    issue_number = Field(output_processor=TakeFirst(), required=True)
    issue_year = Field(output_processor=TakeFirst(), required=True)
    issue_url = Field(output_processor=TakeFirst(), required=True)
    issue_cover_url = Field(output_processor=TakeFirst(), required=False)
    section_name = Field(output_processor=TakeFirst(), required=False)
    article_title = Field(output_processor=TakeFirst(), required=True)
    article_intro = Field(output_processor=TakeFirst(), required=False)
    article_authors = Field(output_processor=Join(", "), required=False)
    article_url = Field(output_processor=TakeFirst(), required=True)
    article_content = Field(output_processor=Join(" "), required=True)
    article_tags = Field(output_processor=Join(", "), required=False)
