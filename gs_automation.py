import time

import gspread


class GoogleSheetAutomation:
    sheet_link = "https://docs.google.com/spreadsheets/d/1xZIwM_kqq8k7zjWzH9-ehtIAObl-d1UH0HlEdvkHJ1o/edit#gid=0"
    sheet_name = "CoinMarketCap Watchlist Scraper"

    scopes = [
        "https://spreadsheets.google.com/feeds",
        'https://www.googleapis.com/auth/spreadsheets',
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]

    gs = gspread.service_account(filename='credentials.json', scopes=scopes)
    sheet = gs.open(sheet_name).sheet1

    records = {r['Coin']: row_id for row_id, r in enumerate(sheet.get_all_records(), start=1)}
    sheet_headers = {h: i for i, h in enumerate(sheet.row_values(1), start=1) if h}

    def __init__(self):
        print(f"{self.sheet_name} Google Spreadsheet Connected!")

    def update_gs_row(self, record):
        self.records = {r['Coin']: row_id for row_id, r in enumerate(self.sheet.get_all_records(), start=1)}
        self.sheet_headers = {h: i for i, h in enumerate(self.sheet.row_values(1), start=1) if h}

        values = [record.get(key, '') for key in self.sheet_headers]
        is_row_exist = record['Coin'] in self.records

        if record['Coin'] not in self.records:
            self.records[record['Coin']] = len(self.records) + 1
        row_id = self.records[record['Coin']] + 1

        try:
            if is_row_exist:
                self.sheet.delete_row(row_id)
        except:
            pass

        retry = 0
        while retry < 3:
            try:
                self.sheet.insert_row(values, row_id)
                time.sleep(0.2)
                break
            except Exception as err:
                print(err)
                time.sleep(1)
                retry += 1

        print(f"{record['Coin']} at row # {row_id} updated!")


# g = GoogleSheetAutomation()
# r = {'Coin': 'Bitcoin', 'Link': 'https://coinmarketcap.com/currencies/bitcoin/', 'Rank': 1,
#      'Price': 222, '24 Hr Volume': 222, 'Market Cap': 222,
#      '1 Day': -2.81, '7 Day': -20.09, 'Watchlist #': '22222', '6 Hour': '', '3 Day': '', '14 Day': ''}
#
# g.update_gs_row(r)
#
# r2 = {'Coin': 'Ripple', 'Link': 'https://coinmarketcap.com/currencies/bitcoin/', 'Rank': 1,
#      'Price': 11, '24 Hr Volume': 11.45, 'Market Cap': 11.11,
#      '1 Day': -2.81, '7 Day': -20.09, 'Watchlist #': '1111', '6 Hour': '', '3 Day': '', '14 Day': ''}
#
# g.update_gs_row(r2)
