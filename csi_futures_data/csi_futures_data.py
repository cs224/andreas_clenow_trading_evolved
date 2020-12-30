import pandas as pd, numpy as np
import os, sys
import tqdm # Used for progress bar
import fnmatch, re
import zipline.finance.constants

# ,root_symbol,multiplier,minor_fx_adj,description,exchange,sector
# 0,AD,100000,1,AUD/USD,CME,Currency
# 1,BO,600,0.01,Soybean Oil,CBT,Agricultural
# 2,BP,62500,1,GBP/USD,CME,Currency
# 3,_C,5000,0.01,Corn,CBT,Agricultural
# 4,CC,10,1,Cocoa,NYCE,Agricultural
# 5,CD,100000,1,CAD/USD,CME,Currency
# 6,CL,1000,1,Crude Oil,NYMEX,Non-Agricultural
# 7,CT,50000,0.01,Cotton #2,NYCE,Agricultural
# 8,CU,125000,1,EUR/USD,CME,Currency
# 9,DA,200000,1,Class III Milk,CME,Agricultural
# 10,DX,1000,1,USD Index,FINEX,Currency
# 11,ED,2500,1,Eurodollar 3m,CME,Rates
# 13,ES,50,1,S&P 500 (E-mini),CME,Equities
# 14,FC,50000,0.01,Cattle-Feeder,CME,Agricultural
# 15,FV,1000,1,US Treasury Note 5yr,CBT,Rates
# 16,GC,100,1,Gold,COMEX,Non-Agricultural
# 17,HG,25000,0.01,Copper,COMEX,Non-Agricultural
# 18,HO,42000,1,Heating Oil,NYMEX,Non-Agricultural
# 20,JY,125000,1,JPY/USD,CME,Currency
# 21,KC,37500,0.01,Coffee Arabica,NYCE,Agricultural
# 22,KW,5000,0.01,Wheat-Kansas City,KCBT,Agricultural
# 23,LB,110,1,Lumber,CME,Agricultural
# 24,LC,40000,0.01,Live Cattle,CME,Agricultural
# 25,LO,1000,1,Brent Crude,ICE,Non-Agricultural
# 26,LG,100,1,Petroleum Gas Oil,ICE,Non-Agricultural
# 27,LH,40000,0.01,Lean Hogs,CME,Agricultural
# 29,LR,10,1,Coffee Robusta,EURONEXT,Agricultural
# 30,LS,50,1,Sugar  #5(White),EURONEXT,Agricultural
# 31,MP,500000,0.01,MEP/USD,CME,Currency
# 32,MW,5000,0.01,Wheat-Spring,MGE,Agricultural
# 33,NE,100000,1,NZD/USD,CME,Currency
# 34,NG,10000,1,Natural Gas,NYMEX,Non-Agricultural
# 35,NK,5,1,Nikkei 225,CME,Equities
# 36,NQ,20,1,Nasdaq (E-mini),CME,Equities
# 37,_O,5000,0.01,Oats-CBT,CBT,Agricultural
# 38,OJ,15000,0.01,Orange Juice,NYCE,Agricultural
# 39,PA,100,1,Palladium,NYMEX,Non-Agricultural
# 40,PL,50,1,Platinum,NYMEX,Non-Agricultural
# 41,RB,42000,1,Petroleum Gasoline,NYMEX,Non-Agricultural
# 42,RR,2000,1,Rice(Rough),CBT,Agricultural
# 43,_S,5000,0.01,Soybean,CBT,Agricultural
# 44,SB,120000,0.01,Sugar #11,NYCE,Agricultural
# 45,SF,125000,1,CHF/USD,CME,Currency
# 46,SI,5000,0.01,Silver,COMEX,Non-Agricultural
# 48,SM,100,1,Soybean Meal,CBT,Agricultural
# 50,TW,100,1,MSCI Taiwan,SGX,Equities
# 51,TF,100,1,Russel 2000 (E-mini),NYFE,Equities
# 53,TU,2000,1,US Treasury Note 2yr,CBT,Rates
# 54,TY,1000,1,US Treasury Note 10y,CBT,Rates
# 55,US,1000,1,US Treasury Long Bond 30yr,CBT,Rates
# 56,VX,1000,1,Volatility Index,CFE,Equities
# 57,_W,5000,0.01,Wheat,CBT,Agricultural
# 59,YM,5,1,Dow e mini,CBT,Equities

# http://www.csidata.com/?page_id=3271
# Point and Tick Values
# CSI displays 3 different types of price values related to futures markets. Usually these values can be computed from the contract size, units, conversion factor, and minimum tick.
#
# Full Point Value
# This represents the contract value per 1.0 unit of currency.This is the general formula:
#
# FullPointValue = ContractSize x UnitOfMeasurement
#
# For example, CME Live Cattle contract size is 40000 lbs and units are cents per pound.
#
# FullPointValue = ContractSize x UnitOfMeasurement = 40000 lbs x cents per pound = 40000 cents = $400.00
#
# Alternatively this formula can be used:
#
# FullPointValue = FranctionalPointValue x ConversionFactorDivisor
#
# For example, the CME website contract specifications states that the FractionalPointValue is $4.00. The conversion factor is +2 which means the ConversionFactorDivisor is 100.
#
# FullPointValue = FranctionalPointValue x ConversionFactorDivisor = $4.00 x 100 = $400.00
#
# The conversion factor divisors:
# -9 =640
# -8 =320
# -7 =320
# -6 =256
# -5 =128
# -4 =64
# -3 =32
# -2 =16
# -1 =8
# 0 =1
# 1 =10
# 2 = 100
# 3 = 1000
# 4 = 10000
# 5 = 100000
# 6 = 1000000
# 7 = 10000000
# 8 = 100000000
#
# Fractional Point Value
# This represents the contract value of the pricing increment precision unit.
#
# FranctionalPointValue = FullPointValue / ConversionFactorDivisor
#
# Tick Value
# The tick value is the minimum price fluctuation of one contract.
#
# TickValue = FractionalPointValue x MinimumTick
#
# For example, CME Live Cattle has a minimum tick of 2.5 and the FractionalPointValue is $4.00.
#
# TickValue = FractionalPointValue x MinimumTick = $4.00 x 2.5 = $10.00

futures_lookup = pd.DataFrame(columns=['csi_symbol','root_symbol','multiplier','minor_fx_adj','description','exchange','sector'])

# futures_lookup.loc[len(futures_lookup)] = []
futures_lookup.loc[len(futures_lookup)] = ['KC2', 'KC', 37500.0, 0.01, 'Coffee', 'CSCE', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['C2' , '_C',  5000.0, 0.01, 'Corn', 'CBT', 'Agricultural'] # duplicate
futures_lookup.loc[len(futures_lookup)] = ['C2' , 'CN',  5000.0, 0.01, 'Corn', 'CBT', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['CT2', 'CT', 50000.0, 0.01, 'Cotton #2', 'NYCE', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['LH' , 'LH', 40000.0, 0.01, 'Lean Hogs', 'CME', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['LC' , 'LC', 40000.0, 0.01, 'Live Cattle', 'CME', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['LB' , 'LB',   110.0, 1.00, 'Lumber', 'CME', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['O2' , '_O',  5000.0, 0.01, 'Oats-CBT', 'CBT', 'Agricultural'] # duplicate
futures_lookup.loc[len(futures_lookup)] = ['O2' , 'OA',  5000.0, 0.01, 'Oats-CBT', 'CBT', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['OJ2', 'OJ', 15000.0, 0.01, 'Orange Juice', 'NYCE', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['RR2', 'RR',  2000.0, 1.00, 'Rice(Rough)', 'CBT', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['S2' , '_S',  5000.0, 0.01, 'Soybean', 'CBT', 'Agricultural'] # duplicate
futures_lookup.loc[len(futures_lookup)] = ['S2' , 'SY',  5000.0, 0.01, 'Soybean', 'CBT', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['LSU', 'LS',    50.0, 1.00, 'Sugar  #5(White)', 'EURONEXT', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['W2' , '_W',  5000.0, 0.01, 'Wheat', 'CBT', 'Agricultural'] # duplicate
futures_lookup.loc[len(futures_lookup)] = ['W2' , 'WC',  5000.0, 0.01, 'Wheat', 'CBT', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['KW2', 'KW',  5000.0, 0.01, 'Wheat-Kansas City', 'KCBT', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['MW2', 'MW',  5000.0, 0.01, 'Wheat-Spring', 'MGE', 'Agricultural']
# data error in AC book!
futures_lookup.loc[len(futures_lookup)] = ['DA' , 'DA',200000.0, 0.01, 'Class III Milk', 'CME', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['FC' , 'FC', 50000.0, 0.01, 'Cattle-Feeder', 'CME', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['LRC', 'LR',    10.0, 1.00, 'Robusta Coffee New (LCE)', 'EURONEXT', 'Agricultural']
# data error in AC book!
futures_lookup.loc[len(futures_lookup)] = ['BO2', 'BO', 60000.0, 0.01, 'Soybean Oil', 'CBT', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['SM2', 'SM',   100.0, 1.00, 'Soybean Meal', 'CBT', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['CC2', 'CC',    10.0, 1.00, 'Cocoa', 'NYCE', 'Agricultural']
# data error in AC book!
futures_lookup.loc[len(futures_lookup)] = ['SB2', 'SB',112000.0, 0.01, 'Sugar #11', 'NYCE', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['XC2', 'CM',  1000.0, 0.01, 'Corn E-Mini', 'CBOT', 'Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['XS2', 'MS',  1000.0, 0.01, 'Soybeans E-Mini', 'CBOT', 'Agricultural']


# futures_lookup.loc[len(futures_lookup)] = []
futures_lookup.loc[len(futures_lookup)] = ['CL2', 'CL',  1000.0, 1.00, 'Crude Oil-Light', 'NYMEX', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['LCO', 'LO',  1000.0, 1.00, 'Brent Crude', 'ICE', 'Non-Agricultural'] # LCO oder L4, aber keine Daten?
futures_lookup.loc[len(futures_lookup)] = ['HO2', 'HO', 42000.0, 1.00, 'Heating Oil', 'NYMEX', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['NG2', 'NG', 10000.0, 1.00, 'Natural Gas', 'NYMEX', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['RB2', 'RB', 42000.0, 1.00, 'Gasoline-Reformulated Blendstock', 'NYMEX', 'Non-Agricultural'] # Petroleum Gasoline
futures_lookup.loc[len(futures_lookup)] = ['GC2', 'GC',   100.0, 1.00, 'Gold', 'COMEX', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['HG2', 'HG', 25000.0, 0.01, 'Copper', 'COMEX', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['PA2', 'PA',   100.0, 1.00, 'Palladium', 'NYMEX', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['PL2', 'PL',    50.0, 1.00, 'Platinum', 'NYMEX', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['SI2', 'SI',  5000.0, 0.01, 'Silver', 'COMEX', 'Non-Agricultural'] # duplicate
futures_lookup.loc[len(futures_lookup)] = ['SI2', 'SV',  5000.0, 0.01, 'Silver', 'COMEX', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['LGO', 'LG',   100.0, 1.00, 'Petroleum Gas Oil', 'ICE', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['ER' , 'AI',   100.0, 1.00, 'Bloomberg Commodity Index Futures', 'CME', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['AC' , 'ET', 29000.0, 1.00, 'Ethanol', 'CBT', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['QG' , 'QG',  2500.0, 1.00, 'Natural Gas E-mini', 'NYMEX', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['QM' , 'QM',   500.0, 1.00, 'Crude Oil E-Mini', 'NYMEX', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['IRB', 'XB', 42000.0, 1.00, 'RBOB Gasoline Futures', 'NYMEX', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['YG' , 'XG',   32.15, 1.00, 'Gold mini-sized', 'ICE', 'Non-Agricultural']
futures_lookup.loc[len(futures_lookup)] = ['YI' , 'YS',  1000.0, 0.01, 'Silver mini-sized', 'ICE', 'Non-Agricultural']



# futures_lookup.loc[len(futures_lookup)] = []
futures_lookup.loc[len(futures_lookup)] = ['AD' , 'AD',100000.0, 1.00, 'AUD/USD', 'CME', 'Currency']
futures_lookup.loc[len(futures_lookup)] = ['BP' , 'BP', 62500.0, 1.00, 'GBP/USD', 'CME', 'Currency']
futures_lookup.loc[len(futures_lookup)] = ['CU' , 'CU',125000.0, 1.00, 'EUR/USD', 'CME', 'Currency'] # duplicate
futures_lookup.loc[len(futures_lookup)] = ['CU' , 'EC',125000.0, 1.00, 'Euro FX', 'CME', 'Currency']
futures_lookup.loc[len(futures_lookup)] = ['CD' , 'CD',100000.0, 1.00, 'CAD/USD', 'CME', 'Currency']
futures_lookup.loc[len(futures_lookup)] = ['JY' , 'JY',125000.0, 1.00, 'JPY/USD', 'CME', 'Currency']
futures_lookup.loc[len(futures_lookup)] = ['NE' , 'NE',100000.0, 1.00, 'NZD/USD', 'CME', 'Currency'] # duplicate
futures_lookup.loc[len(futures_lookup)] = ['NE' , 'NZ',100000.0, 1.00, 'NZD/USD', 'CME', 'Currency']
futures_lookup.loc[len(futures_lookup)] = ['SF' , 'SF',125000.0, 1.00, 'CHF/USD', 'CME', 'Currency']
futures_lookup.loc[len(futures_lookup)] = ['DX2', 'DX',  1000.0, 1.00, 'USD Index', 'FINEX', 'Currency']
# data error in AC book!
futures_lookup.loc[len(futures_lookup)] = ['MP' , 'MP',500000.0, 1.00, 'MEP/USD', 'CME', 'Currency'] # duplicate
futures_lookup.loc[len(futures_lookup)] = ['MP' , 'ME',500000.0, 1.00, 'MEP/USD', 'CME', 'Currency']
futures_lookup.loc[len(futures_lookup)] = ['EX' , 'EE', 62500.0, 1.00, 'Euro FX E-mini', 'CME', 'Currency']
futures_lookup.loc[len(futures_lookup)] = ['M6E' , 'EU', 12500.0, 1.00, 'E-micro EUR/USD Futures', 'CME', 'Currency']
futures_lookup.loc[len(futures_lookup)] = ['JT' , 'JE', 62500.0, 1.00, 'Japanese Yen E-mini', 'CME', 'Currency']



# futures_lookup.loc[len(futures_lookup)] = []
futures_lookup.loc[len(futures_lookup)] = ['ES' , 'ES',    50.0, 1.00, 'S&P 500 (E-mini)', 'CME', 'Equities']
futures_lookup.loc[len(futures_lookup)] = ['NQ' , 'NQ',    20.0, 1.00, 'Nasdaq (E-mini)', 'CME', 'Equities']
futures_lookup.loc[len(futures_lookup)] = ['ER2', 'TF',    50.0, 1.00, 'Russel 2000 (E-mini)', 'CME', 'Equities'] #duplicate
futures_lookup.loc[len(futures_lookup)] = ['ER2', 'ER',    50.0, 1.00, 'Russel 2000 (E-mini)', 'CME', 'Equities']
futures_lookup.loc[len(futures_lookup)] = ['VX' , 'VX',  1000.0, 1.00, 'Volatility Index', 'CFE', 'Equities']
futures_lookup.loc[len(futures_lookup)] = ['YM' , 'YM',     5.0, 1.00, 'Dow e mini', 'CBT', 'Equities']
futures_lookup.loc[len(futures_lookup)] = ['NK' , 'NK',     5.0, 1.00, 'Nikkei 225', 'CME', 'Equities']
futures_lookup.loc[len(futures_lookup)] = ['STW', 'TW',   100.0, 1.00, 'MSCI Taiwan', 'SGX', 'Equities']
futures_lookup.loc[len(futures_lookup)] = ['MEM', 'EI',    50.0, 1.00, 'MSCI Emerging Markets Mini', 'ICE', 'Equities']
futures_lookup.loc[len(futures_lookup)] = ['MFS', 'MG',    50.0, 1.00, 'MSCI EAFE Mini (Europe, Australasia and Far East)', 'ICE', 'Equities']
futures_lookup.loc[len(futures_lookup)] = ['EMD', 'MI',   100.0, 1.00, 'S&P 400 MidCap E-Mini', 'CME', 'Equities']
futures_lookup.loc[len(futures_lookup)] = ['RS1', 'RM',    50.0, 1.00, 'Russell 1000 Mini', 'CME', 'Equities']
futures_lookup.loc[len(futures_lookup)] = ['SP2', 'SP',   250.0, 1.00, 'S&P 500 Futures', 'CME', 'Equities']



# futures_lookup.loc[len(futures_lookup)] = []
futures_lookup.loc[len(futures_lookup)] = ['FV' , 'FV',  1000.0, 1.00, 'US Treasury Note 5yr', 'CBT', 'Rates']
futures_lookup.loc[len(futures_lookup)] = ['ED' , 'ED',  2500.0, 1.00, 'Eurodollar 3m', 'CME', 'Rates']
futures_lookup.loc[len(futures_lookup)] = ['US' , 'US',  1000.0, 1.00, 'US Treasury Long Bond 30yr', 'CBT', 'Rates']
futures_lookup.loc[len(futures_lookup)] = ['TU' , 'TU',  2000.0, 1.00, 'US Treasury Note 2yr', 'CBT', 'Rates']
futures_lookup.loc[len(futures_lookup)] = ['TY' , 'TY',  1000.0, 1.00, 'US Treasury Note 10y', 'CBT', 'Rates']
# 53,TU,2000,1,US Treasury Note 2yr,CBT,Rates
# 54,TY,1000,1,US Treasury Note 10y,CBT,Rates
futures_lookup.loc[len(futures_lookup)] = ['FF' , 'FF',  4167.0, 1.00, '30-Day Federal Funds', 'CBOT', 'Rates']
futures_lookup.loc[len(futures_lookup)] = ['F1U' , 'FI',  1000.0, 1.00, '5-Year Deliverable Interest Rate Swap Futures', 'CBOT', 'Rates']
futures_lookup.loc[len(futures_lookup)] = ['N1U' , 'TN',  1000.0, 1.00, '10-Year Deliverable Interest Rate Swap Futures', 'CBOT', 'Rates']
futures_lookup.loc[len(futures_lookup)] = ['UL2' , 'UB',  1000.0, 1.00, 'Ultra Tbond', 'CBOT', 'Rates']



futures_lookup_ = futures_lookup.copy()

symbols_df = futures_lookup[['csi_symbol','root_symbol']].rename(columns={"root_symbol": "zipline_symbol"}).copy() #   pd.DataFrame(columns=['csi_symbol', 'zipline_symbol'])
futures_lookup = futures_lookup[['root_symbol','multiplier','minor_fx_adj','description','exchange','sector']].copy()


data_path3 = os.path.dirname(os.path.realpath(__file__)) + "/data"
if os.path.islink(data_path3):
    data_path = os.readlink(data_path3)
else:
    data_path = data_path3

if not os.path.isdir(data_path):
    raise RuntimeError('The data_path does not point to a directory: {}'.format(data_path))


class Contract():
    def __init__(self, csi_symbol, zipline_symbol, path, contract_symbol):
        self.csi_symbol = csi_symbol
        self.zipline_symbol = zipline_symbol
        self.path = path
        self.contract_symbol = contract_symbol

# DNOHLCviVI
# D = Date
# N = Delivery Number
# O
# H
# L
# C
# v = contract volume
# i = contract open interest
# V = total volume
# I = total open interest

def read_contract_data(contract):
    ldf = pd.read_csv(contract.path, index_col=[0], parse_dates=[0,2], header=None)
    ldf.columns = ['delivery_yyyymm', 'expiration_date', 'open', 'high', 'low', 'close', 'volume', 'openinterest', 'total_volume', 'total_openinterest']
    # target schema:
    # ,open,high,low,close,volume,openinterest,expiration_date,root_symbol,symbol
    rdf = ldf[['open', 'high', 'low', 'close', 'volume', 'openinterest', 'expiration_date']].copy()
    rdf['root_symbol'] = contract.zipline_symbol
    rdf['symbol'] = contract.contract_symbol
    return rdf

"""
The ingest function needs to have this exact signature, meaning these arguments passed, as shown below.
"""
def csi_futures_data(environ,
                        asset_db_writer,
                        minute_bar_writer,
                        daily_bar_writer,
                        adjustment_writer,
                        calendar,
                        start_session,
                        end_session,
                        cache,
                        show_progress,
                        output_dir):
    contract_list = []
    for idx, row in symbols_df.iterrows():
        csi_symbol, zipline_symbol = row
        # print('zipline_symbol: {}'.format(zipline_symbol))
        for file in sorted(fnmatch.filter(os.listdir(data_path + '/' + csi_symbol), '*.CSV')):
            pattern = r'^{}\d\d(\d\d)([FGHJKMNQUVXZ])'.format(csi_symbol.ljust(3, '_'))
            result = re.match(pattern, file)
            if result:
                contract_two_digit_year = result.group(1)
                contract_month_letter = result.group(2)
                # contract_symbol = zipline_symbol + contract_two_digit_year + contract_month_letter
                contract_symbol = zipline_symbol + contract_month_letter + contract_two_digit_year
                path = data_path + '/' + csi_symbol + '/' + file
                contract = Contract(csi_symbol, zipline_symbol, path, contract_symbol)
                contract_list.append(contract)
            else:
                print('No match for contract: {}'.format(file))



    if len(contract_list) == 0:
        raise ValueError("No symbols found in folder.")

    # Prepare an empty DataFrame for dividends
    divs = pd.DataFrame(columns=['sid',
                                 'amount',
                                 'ex_date',
                                 'record_date',
                                 'declared_date',
                                 'pay_date']
                        )

    # Prepare an empty DataFrame for splits
    splits = pd.DataFrame(columns=['sid',
                                   'ratio',
                                   'effective_date']
                          )

    # Prepare an empty DataFrame for metadata
    metadata = pd.DataFrame(columns=('start_date',
                                     'end_date',
                                     'auto_close_date',
                                     'symbol',
                                     'root_symbol',
                                     'expiration_date',
                                     'notice_date',
                                     'tick_size',
                                     'exchange',
                                     'multiplier'
                                     )
                            )

    # Check valid trading dates, according to the selected exchange calendar
    sessions = calendar.sessions_in_range(start_session, end_session)

    # Get data for all stocks and write to Zipline
    daily_bar_writer.write(
        process_futures(contract_list, sessions, metadata)
    )

    adjustment_writer.write(splits=splits, dividends=divs)

    # Prepare root level metadata
    root_symbols = futures_lookup.copy()
    root_symbols['root_symbol_id'] = root_symbols.index.values
    del root_symbols['minor_fx_adj']

    # write the meta data
    asset_db_writer.write(futures=metadata, root_symbols=root_symbols)

def process_futures(contract_list, sessions, metadata):
    # Loop the stocks, setting a unique Security ID (SID)
    sid = 0

    # Loop the symbols with progress bar, using tqdm
    for contract in tqdm.tqdm(contract_list, desc='Loading data...'):
        sid += 1

        # Read the stock data from csv file.
        # print(contract.path)
        df = read_contract_data(contract)

        # Check for minor currency quotes
        adjustment_factor = futures_lookup.loc[futures_lookup['root_symbol'] == df.iloc[0]['root_symbol']]['minor_fx_adj'].iloc[0]

        df['open'] *= adjustment_factor
        df['high'] *= adjustment_factor
        df['low'] *= adjustment_factor
        df['close'] *= adjustment_factor

        # Avoid potential high / low data errors in data set
        # And apply minor currency adjustment for USc quotes
        df['high'] = df[['high', 'close']].max(axis=1)
        df['low'] = df[['low', 'close']].min(axis=1)
        df['high'] = df[['high', 'open']].max(axis=1)
        df['low'] = df[['low', 'open']].min(axis=1)

        # Synch to the official exchange calendar
        df = df.reindex(sessions.tz_localize(None))[df.index[0]:df.index[-1]]

        # Forward fill missing data
        df.fillna(method='ffill', inplace=True)

        # Drop remaining NaN
        df.dropna(inplace=True)

        # Cut dates before 2000, avoiding Zipline issue
        df = df['2000-01-01':]

        # Prepare contract metadata
        make_meta(sid, metadata, df, sessions)

        del df['openinterest']
        del df['expiration_date']
        del df['root_symbol']
        del df['symbol']

        yield sid, df


def make_meta(sid, metadata, df, sessions):
    # Check first and last date.
    start_date = df.index[0]
    end_date = df.index[-1]

    # The auto_close date is the day after the last trade.
    ac_date = end_date + pd.Timedelta(days=1)

    symbol = df.iloc[0]['symbol']
    root_sym = df.iloc[0]['root_symbol']
    exchng = futures_lookup.loc[futures_lookup['root_symbol'] == root_sym]['exchange'].iloc[0]
    adjustment_factor = futures_lookup.loc[futures_lookup['root_symbol'] == df.iloc[0]['root_symbol']]['minor_fx_adj'].iloc[0]
    multiplier = futures_lookup.loc[futures_lookup['root_symbol'] == root_sym]['multiplier'].iloc[0]
    multiplier = multiplier * adjustment_factor
    # exp_date = end_date
    exp_date = df.iloc[0]['expiration_date']

    # Add notice day if you have.
    # Tip to improve: Set notice date to one month prior to
    # expiry for commodity markets.
    notice_date = ac_date
    tick_size = 0.0001  # Placeholder

    # Add a row to the metadata DataFrame.

    # You might also want to ensure that all of the metadata fields are also populated too (asset_type, notice_date, expiration_date, auto_close_date, exchange, exchange_full, root_symbol, multiplier, start_date, end_date, first_traded too.
    # exchange_full, multiplier, first_traded
    # see also : ./zipline/assets/asset_db_schema.py
    #          : https://www.followingthetrend.com/2019/08/trading-evolved-errata-and-updates/
    metadata.loc[sid] = start_date, end_date, ac_date, symbol, root_sym, exp_date, notice_date, tick_size, exchng, multiplier


ldf = futures_lookup_.copy()
bool_columns = []
ldf['is_in_bundle'] = True
bool_columns.append('is_in_bundle')
ldf['sector'] = ldf['sector'].astype('category').cat.rename_categories(
    {
        'Agricultural': 'agricultural',
        'Non-Agricultural': 'nonagricultural',
        'Currency': 'currencies',
        'Equities': 'equities',
        'Rates': 'rates'
    }).astype('str')

ldf.reset_index(inplace=True)
ldf.set_index('root_symbol', inplace=True, drop=False)

ldf['ROOT_SYMBOL_TO_ETA'] = False
bool_columns.append('ROOT_SYMBOL_TO_ETA')
for k in list(zipline.finance.constants.ROOT_SYMBOL_TO_ETA.keys()):
    ldf.loc[k, 'ROOT_SYMBOL_TO_ETA'] = True
ldf['ROOT_SYMBOL_TO_ETA'] = ldf['ROOT_SYMBOL_TO_ETA'].astype(np.bool)

ldf['FUTURE_EXCHANGE_FEES_BY_SYMBOL'] = False
bool_columns.append('FUTURE_EXCHANGE_FEES_BY_SYMBOL')
for k in list(zipline.finance.constants.FUTURE_EXCHANGE_FEES_BY_SYMBOL.keys()):
    ldf.loc[k, 'FUTURE_EXCHANGE_FEES_BY_SYMBOL'] = True
ldf['FUTURE_EXCHANGE_FEES_BY_SYMBOL'] = ldf['FUTURE_EXCHANGE_FEES_BY_SYMBOL'].astype(np.bool)

currencies = ['AD','BP','CD','EC','DX','JY','NZ','SF',]
agricultural = ['CN','CT','FC','KC','LR','LS','OA','SY','SB','SM','WC','BL']
nonagricultural = ['CL','GC','HG','HO','LG','NG','PA','PL','RB','SV',]
equities = ['ES','NK','NQ','TW','VX','YM',]
rates = ['ED','FV','TU','TY','US',]
markets = currencies + agricultural + nonagricultural + equities + rates
trend_following_markets = markets
ldf['trend_following_markets'] = False
bool_columns.append('trend_following_markets')
for k in trend_following_markets:
    ldf.loc[k, 'trend_following_markets'] = True
ldf['trend_following_markets'] = ldf['trend_following_markets'].astype(np.bool)
# ldf.loc[ldf['root_symbol'].isin(trend_following_markets) ,'trend_following_markets'] = True

currencies = ['AD','BP','CD','EC','DX','JY','NZ','SF',]
agriculturals = ['BL','BO','CN','CC','CT','FC','KC','LB','LC','LR','LS','OA','SY','SB','WC',]
nonagriculturals = ['CL','GC','HG','HO','LG','NG','PA','PL','RB','SV',]
equities = ['ES','NK','NQ','TW','VX','YM',]
rates = ['ED','FV','TU','TY','US',]
markets = currencies + agriculturals + nonagriculturals + equities + rates
time_return_markets = markets
ldf['time_return_markets'] = False
bool_columns.append('time_return_markets')
for k in time_return_markets:
    ldf.loc[k, 'time_return_markets'] = True
ldf['time_return_markets'] = ldf['time_return_markets'].astype(np.bool)

agricultural = ['BL','CC','CT','FC','KC','LB','LR','OJ','RR','SY','SB','LC','LS',]
nonagricultural = ['CL','GC','HG','HO','LG','PA','PL','RB','SV','NG','LO',]
currencies = ['AD','BP','CD','EC','DX','NZ','SF','JY',]
equities = ['ES','NK','NQ','YM',]
rates = ['ED','FV','TU','TY','US',]
markets = agricultural + nonagricultural + currencies + equities + rates
counter_trend_markets = markets
ldf['counter_trend_markets'] = False
bool_columns.append('counter_trend_markets')
for k in counter_trend_markets:
    ldf.loc[k, 'counter_trend_markets'] = True
ldf['counter_trend_markets'] = ldf['counter_trend_markets'].astype(np.bool)

most_liquid_commods = ['CL', 'HO', 'RB', 'NG', 'GC', 'LC', 'CN', 'SY', 'WC', 'SB', 'HG', 'CT', 'KC']
curve_trading_markets = most_liquid_commods
ldf['curve_trading_markets'] = False
bool_columns.append('curve_trading_markets')
for k in curve_trading_markets:
    ldf.loc[k, 'curve_trading_markets'] = True
ldf['curve_trading_markets'] = ldf['curve_trading_markets'].astype(np.bool)


for col in bool_columns:
    ldf[col].fillna(False, inplace=True)
    ldf[col].astype(np.bool, inplace=True)

futures_markets_lookup = ldf

def get_bundle_market_symbols(market):
    ldf = futures_markets_lookup
    return list(ldf[ldf[market] & ldf['is_in_bundle']]['root_symbol'])