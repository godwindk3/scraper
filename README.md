# Job Scraper

This project uses [Scrapy](https://scrapy.org/) to crawl IT job data from 4 websites:

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

# Replace this string with your actual MongoDB Atlas connection string when load to mongodb
MONGO_URI = "mongodb+srv://<username>:<password>@cluster0.xxxx.mongodb.net/?appName=<appname>"

## More Details

Scrapy official documentation:

https://docs.scrapy.org/en/latest/
