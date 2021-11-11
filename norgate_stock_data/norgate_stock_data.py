import pandas as pd, numpy as np
import os, sys
import tqdm # Used for progress bar
import fnmatch, re
import zipline.finance.constants
from os import listdir

data_path3 = os.path.dirname(os.path.realpath(__file__)) + "/data"
if os.path.islink(data_path3):
    data_path = os.readlink(data_path3)
else:
    data_path = data_path3

if not os.path.isdir(data_path):
    raise RuntimeError('The data_path does not point to a directory: {}'.format(data_path))

# symbols_dynamic.csv, symbols_static.csv, snp_membership.csv

def norgate_stock_data(environ, asset_db_writer, minute_bar_writer, daily_bar_writer, adjustment_writer, calendar, start_session, end_session, cache, show_progress, output_dir):
    files = [f[:-4] for f in listdir(data_path)]
    if not files:
        raise ValueError("No symbols found in folder.")

    try:
        files.remove('symbols_dynamic')
    except ValueError:
        pass  # do nothing!

    try:
        files.remove('symbols_static')
    except ValueError:
        pass  # do nothing!

    regex = re.compile(r'\w+_membership')
    files = [f for f in files if not regex.match(f)]

    pattern = r'^([A-Za-z0-9-.]+)_(\d+)$'
    symbol_list = []
    for file in files:
        result = re.match(pattern, file)
        if result:
            symbol = result.group(1)
            norgate_assetid = result.group(2)
            symbol_list.append((symbol, norgate_assetid))
        else:
            print('No match for symbol/assetid: {}'.format(file))

    # Prepare an empty DataFrame for dividends
    divs = pd.DataFrame(columns=['sid', 'amount', 'ex_date', 'record_date', 'declared_date', 'pay_date'])

    # Prepare an empty DataFrame for splits
    splits = pd.DataFrame(columns=['sid', 'ratio', 'effective_date'] )

    # Prepare an empty DataFrame for metadata
    metadata = pd.DataFrame(columns=('start_date', 'end_date', 'auto_close_date', 'symbol', 'exchange'))

    # Check valid trading dates, according to the selected exchange calendar
    sessions = calendar.sessions_in_range(start_session, end_session)

    # Get data for all stocks and write to Zipline
    daily_bar_writer.write(process_stocks(symbol_list, sessions, metadata, divs))

    # Write splits and dividends
    adjustment_writer.write(splits=splits, dividends=divs)

    # Write the metadata
    asset_db_writer.write(equities=metadata)


def process_stocks(symbol_list, sessions, metadata, divs):
    # Loop the stocks, setting a unique Security ID (SID)

    for symbol, norgate_assetid in tqdm.tqdm(symbol_list, desc='Loading data...'):
        # Read the stock data from csv file.

        # Date,Open,High,Low,Close,Volume,Turnover,Unadjusted Close,Dividend,_Close,TR Close,TR Unadjusted Close,S&P 500,Capital Event,Dividend Yield
        # Close:
        #  priceadjust      = norgatedata.StockPriceAdjustmentType.CAPITAL
        # _Close:
        #  priceadjust      = norgatedata.StockPriceAdjustmentType.NONE
        # TR Close, TR Unadjusted Close:
        #  priceadjust      = norgatedata.StockPriceAdjustmentType.TOTALRETURN
        ldf = pd.read_csv('{}/{}_{}.csv'.format(data_path, symbol,norgate_assetid), index_col=[0], parse_dates=[0])
        sid = norgate_assetid

        # trade_date,open,high,low,close,volume,dividend,in_sp500
        ldf = ldf.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume", "Dividend": "dividend", "S&P 500": "in_sp500"}) # , errors="raise"
        ldf = ldf[["open","high","low","close","volume","dividend","in_sp500"]]
        ldf['volume'] = ldf['volume'].astype(np.uint32)
        ldf.index.name = "trade_date"

        # Check first and last date.
        start_date = ldf.index[0]
        end_date = ldf.index[-1]

        # Synch to the official exchange calendar
        ldf = ldf.reindex(sessions.tz_localize(None))[start_date:end_date]

        # Forward fill missing data
        ldf.fillna(method='ffill', inplace=True)

        # Drop remaining NaN
        ldf.dropna(inplace=True)

        # The auto_close date is the day after the last trade.
        ac_date = end_date + pd.Timedelta(days=1)

        # Add a row to the metadata DataFrame. Don't forget to add an exchange field.
        metadata.loc[sid] = start_date, end_date, ac_date, symbol, "NYSE"

        # If there's dividend data, add that to the dividend DataFrame
        if 'dividend' in ldf.columns:
            # Slice off the days with dividends
            tmp = ldf[ldf['dividend'] != 0.0]['dividend']
            div = pd.DataFrame(data=tmp.index.tolist(), columns=['ex_date'])

            # Provide empty columns as we don't have this data for now
            div['record_date'] = pd.NaT
            div['declared_date'] = pd.NaT
            div['pay_date'] = pd.NaT

            # Store the dividends and set the Security ID
            div['amount'] = tmp.tolist()
            div['sid'] = sid

            # Start numbering at where we left off last time
            ind = pd.Index(range(divs.shape[0], divs.shape[0] + div.shape[0]))
            div.set_index(ind, inplace=True)

            # Append this stock's dividends to the list of all dividends
            divs = divs.append(div)

        yield sid, ldf