# Job Scraper

This project uses [Scrapy](https://scrapy.org/) to crawl job data from 4 websites:

- itviec
- topdev
- topcv
- vietnamworks

---

## Setup

Create virtual environment:

```bash
python -m venv .venv
```

Activate virtual environment:

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Run Scrapy Spider

Run a spider with:

```bash
scrapy crawl spider_name
```

Example:

```bash
scrapy crawl itviec
```

---

## More Details

Scrapy official documentation:

https://docs.scrapy.org/en/latest/