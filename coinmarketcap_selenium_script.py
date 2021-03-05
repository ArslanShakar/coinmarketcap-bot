# -*- coding: utf-8 -*-

import os
import json
import time
import random

from scrapy import Selector
from selenium import webdriver

from gs_automation import GoogleSheetAutomation
from webdriver_manager.chrome import ChromeDriverManager


class CoinMarketCapSeleniumScript(GoogleSheetAutomation):
    base_url = 'https://coinmarketcap.com/'
    currency_url_t = 'https://coinmarketcap.com/currencies/{slug}/'
    next_page_url_t = 'https://coinmarketcap.com/?page={p_no}'

    watchlist_diff = {}

    sheet_headers = [
        "Coin", "Link", "Rank", "Price", "24 Hr Volume", "Market Cap",
        "Watchlist", "1 Hour", "6 Hour", "1 Day", "3 Day", "7 Day",
        "14 Day", "Price Change - 24h"
    ]

    # chrome_options = webdriver.ChromeOptions()
    # chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--no-sandbox")
    # driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)

    options = webdriver.ChromeOptions()
    # options = webdriver.FirefoxOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    def __init__(self):
        super().__init__()
        self.run_driver()
        self.driver = None

    def run_driver(self):
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=self.options)

        try:
            response = self.get_response_from_web_driver(self.base_url)
            last_page = response.css('li.page a[role="button"]::text').getall()[-1]
            print(f"Total Pages = {last_page}")
            self.parse(response)

            for n in range(2, int(last_page) + 1):
                next_page_url = self.next_page_url_t.format(p_no=n)
                self.parse(self.get_response_from_web_driver(next_page_url))
        except Exception as e:
            print(f"Exception while crawling: {e}")

    def parse(self, response):
        raw = self.get_raw(response)
        currencies = raw.get('props', {}).get('initialState', {}). \
            get('cryptocurrency', {}).get('listingLatest', {}).get('data', [])

        records = []

        for cur in currencies[:]:
            try:
                records.append(self.get_record(cur))
            except Exception as err:
                print(f"Exception while parsing results: {err}")
                pass

    def get_response_from_web_driver(self, url):
        self.driver.get(url)
        time.sleep(random.choice([3, 3.5, 4, 4.5]))
        return Selector(text=self.driver.page_source)

    def get_raw(self, response):
        return json.loads(response.css('#__NEXT_DATA__[type="application/json"]::text').get('{}'))

    def get_record(self, cur):
        info = cur['quote']['USD'] or cur['quotes'][0]

        item = {}
        item["Coin"] = cur['name']
        item["Link"] = self.currency_url_t.format(slug=cur['slug'])
        item["Rank"] = cur['cmcRank']
        item["Price"] = info['price']
        item["24 Hr Volume"] = info['volume24h']
        item["Market Cap"] = info['marketCap']
        # item["1 Hour"] = round(info['percentChange1h'], 2)
        # item["1 Day"] = round(info['percentChange24h'], 2)
        # item["7 Day"] = round(info['percentChange7d'], 2)

        selector = self.get_response_from_web_driver(item['Link'])
        coin_raw = self.get_raw(selector)

        coin_info = coin_raw.get('props', {}).get('initialProps', {}). \
            get('pageProps', {}).get('info', {})

        stats = coin_info['statistics']

        # quotes = coin_raw.get('props', {}).get('initialState', {}).\
        #     get('cryptocurrency', {}).get('quotesLatest', {}).get('data', {})

        item['Price Change - 24h'] = stats['priceChangePercentage24h']
        item["Watchlist"] = coin_info['watchCount']
        self.watchlist_diff.setdefault(item["Coin"], [])

        if item["Coin"] not in self.records:
            item["6 Hour"] = item["Watchlist"]
        else:
            last_record = self.records[item["Coin"]]
            difference = int(last_record['6 Hour']) - int(item["Watchlist"])
            self.watchlist_diff[item["Coin"]].append(difference)
            item["6 Hour"] = difference

        item["1 Day"] = sum(self.watchlist_diff[item["Coin"]][:4]) or ''
        item["3 Day"] = sum(self.watchlist_diff[item["Coin"]][:12]) or ''
        item["7 Day"] = sum(self.watchlist_diff[item["Coin"]][:28]) or ''
        item["14 Day"] = sum(self.watchlist_diff[item["Coin"]][:56]) or ''

        if len(self.watchlist_diff[item["Coin"]]) == 56:
            self.watchlist_diff[item["Coin"]].pop(0)
        print(item)
        self.update_gs_row(item)


if __name__ == "__main__":
    wait_hours = 1

    while True:
        try:
            CoinMarketCapSeleniumScript()
            print(f"Sleeping for {wait_hours} hours...")
            time.sleep(wait_hours * 60 * 60)
        except Exception as err:
            pass
