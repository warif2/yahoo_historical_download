#!/usr/bin/python3
"""
A patch-up script to solve the issue for the shutdown of yahoo-finance api.

Author: warif2
"""

import requests
import re
import os, csv
import datetime
import argparse
#import yaml

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

    for symbol in tickers:
        param = (symbol, etime_start, etime_end, crumb)
        fetch_url = "https://query1.finance.yahoo.com/v7/finance/download/{0}?period1={1}&period2={2}&interval=1d&events=history&crumb={3}".format(*param)
        data = requests.get(fetch_url, cookies={'B':cookie}, timeout = 10)

        out_file = open(os.path.join(dataDir, '%s.csv' % symbol), 'w')
        out_file.write(data.text)
        out_file.close()

def data_combine(tck):
    dates = []
    output_tables = {}
    value_index = {}
    header = ['Dates']
    with open("yahoo_data/%s.csv" % tck[0], 'r') as f:
        value_types = f.readline().strip('\n').split(',')[1:]
        for values in value_types:
            value_index[values] = value_types.index(values)
        for entry in f:
            dates.append(entry.strip('\n').split(',')[0])

    for values in value_types:
        if values not in output_tables.keys():
            output_tables[values] = []
            for i in range(len(dates)):
                output_tables[values].append([dates[i]])

    for symbol in tck:
        header.append(symbol)
        index = 0
        with open('yahoo_data/%s.csv' % symbol, 'r') as f:
            for line in f:
                skip = 0
                entry = line.strip('\n').split(',')
                for types in value_types:
                    value = entry[value_index[types] + 1]
                    if value in value_index.keys():
                        skip = 1
                        continue
                    else:
                        output_tables[types][index].append(value)
                if skip == 0:
                    index += 1

    dataDir = os.getcwd() + "/combine_data/"
    if not os.path.exists(dataDir):
        os.mkdir(dataDir)

    for types in value_types:
        output = csv.writer(open('combine_data/%s.csv' % types, 'w'), delimiter = ',')
        output.writerow(header)
        for i in range(len(output_tables[types])):
            output.writerow(output_tables[types][i])


if __name__ == '__main__':
    # Setting up argparse
    #parser = argparse.ArgumentParser(description = "A replacement for the yahoo-finance api which has been discontinued.Takes input of ticker symbols in .csv file and downloads tables of historical data.",
    #                                 prog = "yhoo_historical_download.py")
    #parser.add_argument('ticker', type = str, default = None, metavar = 'TICKER FILE', help = 'Specify path to the file of ticker symbols.')
    #args = parser.parse_args()

    tickers = []
    with open('ticker_file.csv', 'r') as tck_file:
        for tck in tck_file:
            if tck[0] == '#':
                days = int(tck.strip('#').strip('\n'))
            else:
                tickers.append(tck.strip('\n'))

    # Retreive historical data for input TICKERS
    get_historical(tickers, days)

    # Combine all data
    data_combine(tickers)
