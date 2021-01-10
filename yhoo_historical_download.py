#!/usr/bin/python3
"""
A patch-up script to solve the issue for the shutdown of yahoo-finance api.

Author: warif2
"""

import requests
import re
import os
import csv
import datetime
import sys
import pandas as pd

def get_historical(tickers, day):
    url = 'https://finance.yahoo.com/quote/AAPL/history' # url for a ticker symbol, with a download link
    request = requests.get(url, timeout = 10) # download page
    txt = request.text # extract html
    cookie = request.cookies['B'] # extract cookie

    # Now we need to extract the token from html.
    # the string we need looks like this: "CrumbStore":{"crumb":"lQHxbbYOBCq"}

    pattern = re.compile('.*"CrumbStore":\{"crumb":"(?P<crumb>[^"]+)"\}')
    for line in txt.splitlines():
        match = pattern.match(line)
        if match is not None:
            crumb = match.groupdict()['crumb']

    # Prepare directory for data dump
    dataDir = os.getcwd() + "/yahoo_data/"
    if not os.path.exists(dataDir):
        os.mkdir(dataDir)

    # Save data to YAML file
#    data = {'cookie': cookie, 'crumb': crumb}
#    dataFile = os.path.join(dataDir, 'yahoo_cookie.yml')
#    with open(dataFile, 'w') as fid:
#        yaml.dump(data, fid)

    # Prepare date interval
    today = datetime.datetime.now()
    eDate = (today.year, today.month, today.day)
    etime_end = int(datetime.datetime(*eDate).timestamp())
    etime_start = etime_end - (day * 86400)

    found = []
    for symbol in tickers:
        param = (symbol, etime_start, etime_end, crumb)
        fetch_url = "https://query1.finance.yahoo.com/v7/finance/download/{0}?period1={1}&period2={2}&interval=1d&events=history&crumb={3}".format(*param)
        try:
            data = requests.get(fetch_url, cookies={'B':cookie}, timeout = 10)
            out_file = open(os.path.join(dataDir, '%s.csv' % symbol), 'w')
            out_file.write(data.text)
            out_file.close()
            if "Not Found" in data.text:
                print(symbol + " Not Found!")
            else:
                print("Fetched " + symbol)
                found.append(symbol)
        except:
            print(symbol + " Not Found!")

    return found

def data_combine(tck):
    data_in, data_out, num_day = dict(), dict(), dict()
    for symbol in tck:
        data_in[symbol] = pd.read_csv('yahoo_data/%s.csv' % symbol)
        num_day[symbol] = len(data_in[symbol])
    # save data rows info into combine_data folder
    row_df = pd.DataFrame(list(num_day.items()), columns=['ticker', 'num_rows'])
    row_df.to_excel('combine_data/num_rows.xlsx', index=False)

    # get merge order
    merge_order = sorted(num_day.items(), key=lambda x: x[1], reverse=True)

    # column names
    value_types = data_in[merge_order[0][0]].columns
    for data_type in value_types:
        if data_type == 'Date':
            continue
        else:
            data_out[data_type] = pd.DataFrame()
            for symbol in merge_order:
                if data_out[data_type].empty:
                    data_out[data_type] = pd.DataFrame(data_in[symbol[0]], columns=['Date',data_type])
                else:
                    data_out[data_type] = data_out[data_type].merge(data_in[symbol[0]][['Date', data_type]], how='left',
                                                                    on='Date')
                data_out[data_type].rename(columns={data_type: symbol[0]}, inplace=True)

    # save data
    with pd.ExcelWriter('combine_data/data.xlsx') as writer:
        for data_type in data_out.keys():
            data_out[data_type].to_excel(writer, sheet_name=data_type, index=False)

if __name__ == '__main__':
    tickers = []
    print("Fetching historical data from yahoo finance...")
    with open('ticker_file.csv', 'r') as tck_file:
        for tck in tck_file:
            if tck[0] == '#':
                days = int(tck.strip('#').strip('\n'))
            else:
                tickers.append(tck.strip('\n'))

    # Retrieve historical data for input TICKERS
    tickers_found = get_historical(tickers, days)

    # Combine all data
    if len(tickers_found) > 0:
        data_combine(tickers_found)
    else:
        print("Fetching Complete.")
