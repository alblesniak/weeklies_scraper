## Documentation for Weeklies Scraper
### Overview
Weeklies Scraper is a Python-based tool designed for scraping weekly updates or newsletters from specified websites as:
- [newsweek.pl](https://www.newsweek.pl/mapa-archiwum)
- [polityka.pl](https://www.polityka.pl/archiwumpolityki)
- [wprost.pl](https://www.wprost.pl/tygodnik/archiwum)
- [gosc.pl](https://www.gosc.pl/wyszukaj/wydania/3.Gosc-Niedzielny)
- [przewodnik-katolicki.pl](https://www.przewodnik-katolicki.pl/Archiwum?rok=wszystkie)
- [niedziela.pl](https://m.niedziela.pl/archiwum)

Its main function is to automate the process of collecting and organizing information that is updated on a weekly basis in form of SQLite3 database.

### Getting Started
Prerequisites
- Python 3.x
- Scrapy
- Selenium

```bash
git clone https://github.com/alblesniak/weeklies_scraper.git
cd weeklies_scraper
pip install -r requirements.txt
```

### Features
- Scrapy Integration: Leverages Scrapy for robust and efficient data extraction.
- Selenium Support: Uses Selenium for scraping dynamic content from JavaScript-rendered pages.
- Weekly Data Scraping: Tailored for collecting weekly updates or newsletters.
- Data Processing: Includes features for cleaning and processing scraped data.
- Output Formats: Details the formats in which the scraped data is saved (e.g., CSV, JSON).
