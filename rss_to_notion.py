name: RSS to Notion

on:
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:

jobs:
  run-script:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Install Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: pip install feedparser requests

      - name: Run script
        env:
          NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
          DATABASE_ID: ${{ secrets.DATABASE_ID }}
        run: python rss_to_notion.py
