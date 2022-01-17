from cmath import nan
from curses import beep
from mmap import ACCESS_COPY
from sqlite3 import Date
from django.core.checks import messages
from django.shortcuts import render
from credentials import zerodha_api_key,zerodha_secret_key
from kiteconnect import KiteConnect
from historicalTesting.models import *
from overall.views import *
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates



# import numpy as np
# import datetime as dt
# import pandas_datareader as pdr
# import seaborn as sns
# import matplotlib.pyplot as plt

def Wilder(data, periods):
    start = np.where(~np.isnan(data))[0][0] #Check if nans present in beginning
    Wilder = np.array([np.nan]*len(data))
    Wilder[start+periods-1] = data[start:(start+periods)].mean() #Simple Moving Average
    for i in range(start+periods,len(data)):
        Wilder[i] = (Wilder[i-1]*(periods-1) + data[i])/periods #Wilder Smoothing
    return(Wilder)

def plot_indicators(instrument_df,top_columns,below_column,horizontal_div = None):
    fig = plt.figure(figsize=(16,10))
    fig.subplots_adjust(hspace=0)
    plt.rcParams.update({'font.size': 14})
    price_ax = plt.subplot(2,1,1)
    for col in top_columns:
        price_ax.plot(instrument_df['datetime'], instrument_df[col], label=col)

    price_ax.legend(loc="upper left", fontsize=12)

    indicator_ax = plt.subplot(2, 1, 2)
    indicator_ax.plot(instrument_df['datetime'],instrument_df[below_column], color='k', linewidth = 1, alpha=0.7, label=below_column)
    indicator_ax.legend(loc="upper left", fontsize=12)
    indicator_ax.set_ylabel(below_column)
    
    if horizontal_div:
        horizontal_line = 1
        indicator_ax.axhline(horizontal_line, color = (.5, .5, .5), linestyle = '--', alpha = 0.5)
        indicator_ax.fill_between(instrument_df['datetime'], horizontal_line, instrument_df['sma_ratio_20on5'], where = (instrument_df['sma_ratio_20on5'] >= horizontal_line), color='g', alpha=0.3, interpolate=True)
        indicator_ax.fill_between(instrument_df['datetime'], horizontal_line, instrument_df['sma_ratio_20on5'], where = (instrument_df['sma_ratio_20on5']  < horizontal_line), color='r', alpha=0.3, interpolate=True)

    indicator_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    price_ax.grid(b=True, linestyle='--', alpha=0.5)
    indicator_ax.grid(b=True, linestyle='--', alpha=0.5)
    
    price_ax.set_facecolor((.94,.95,.98))
    indicator_ax.set_facecolor((.98,.97,.93))
    
    price_ax.margins(0.05, 0.2)
    indicator_ax.margins(0.05, 0.2)

    price_ax.tick_params(left=False, bottom=False)
    indicator_ax.tick_params(left=False, bottom=False, labelrotation=45)

    for s in price_ax.spines.values():
        s.set_visible(False)
# Hiding all the spines for the ROC subplot:
    for s in indicator_ax.spines.values():
        s.set_visible(False)
            
    indicator_ax.spines['top'].set_visible(True)
    indicator_ax.spines['top'].set_linewidth(1.5)
    return plt
        


        



# Create your views here.
class ConnectZerodha:
    def get_access_token():
        success = False
        message = ""
        kite = KiteConnect(zerodha_api_key)
        login_url = kite.login_url()
        print(login_url)
        request_token = input("Enter request token here : ")
        data = kite.generate_session(request_token=request_token, api_secret=zerodha_secret_key)
        tokens.objects.create(request_token=request_token,access_token=data["access_token"])
        success = True
        message = "Token Generated"
        return ({
                 'status':success,
                 'message':message,
                 'data':{'request_token':request_token,
                          'access_token':data["access_token"]}
                })

    def create_kite_session():
        success = False
        message = ""
        latest_token = tokens.objects.latest('created_at')
        access_token = latest_token.access_token
        kite = KiteConnect(zerodha_api_key)
        kite.set_access_token(access_token)
        success = True
        message = "Session Created"
        return kite


class InstrumentsTracking:
    def get_instruments_list():
        success = False
        message = ""
        # create session
        kite = ConnectZerodha.create_kite_session()
        
        try:
            instruments = kite.instruments()
        except:
            success = False
            message = "Authentication Failed"
            return ({
                'status':success,
                'message':message
            })
        
        total_instruments = len(instruments)
        count = 0 
        for instrument in instruments:
            existing_count = InstrumentList.objects.filter(instrument_token = instrument['instrument_token']).count()
            if existing_count > 0:
                pass
            else:
                # try:
                # print(instrument)
                InstrumentList.objects.create(
                            instrument_token     = instrument['instrument_token']
                            ,exchange_token      = instrument['exchange_token']
                            ,tradingsymbol       = instrument['tradingsymbol']
                            ,name                = instrument['name'] if instrument['name'] != "" else None
                            ,last_price          = instrument['last_price']
                            ,expiry              = instrument['expiry'] if instrument['expiry'] != "" else None
                            ,strike              = instrument['strike'] if instrument['strike'] != "" else None
                            ,tick_size           = instrument['tick_size']
                            ,lot_size            = instrument['lot_size']
                            ,instrument_type     = instrument['instrument_type']
                            ,segment             = instrument['segment']
                            ,exchange            = instrument['exchange']
                )
                # except:
                #     print(instrument)
                    # exit()
            count = count + 1
            printProgressBar(count,total_instruments)
        success = True
        message = "Instruments List Updated"
        return ({
                 'status':success,
                 'message':message
                })

    def track_instrument(token_id):
        success = False
        message = ""
        instrument = InstrumentList.objects.get(instrument_token = token_id)
        # print(instruments[0].name,instruments[0].instrument_token)
        existing_instruments  = trackedInstruments.objects.filter(instrument = instrument)

        if existing_instruments.count() > 0:
            success = False
            message = "Instrument already tracked"
        else:
            success = True
            new_tracked_instrument = trackedInstruments.objects.create(instrument = instrument)
            message = "Instrument added for tracking"
        return ({
                 'status':success,
                 'message':message
                })
               
    def untrack_instrument(token_id):
        instruments  = trackedInstruments.objects.filter(instrument__instrument_token = token_id)
        if instruments.count() == 0:
            success = False
            message = "Instrument not present"
        else:
            success = True
            instruments.delete()
            message = "Instrument removed from tracking"
        return ({
                 'status':success,
                 'message':message
                })

class InstrumentDataFetch:
    def update_stored_historical_data(token_id,frequency,start,end):
        """
        Give start date and end date in the format YYYY-MM-DD
        Note this deletes existing occurance of historical data in the database
        """
        success = False
        message = ""
        # create session
        kite = ConnectZerodha.create_kite_session()

        allowed_frequency = ['day','minute']
        start_formatted = datetime.datetime.strptime(start,"%Y-%m-%d")
        end_formatted = datetime.datetime.strptime(end,"%Y-%m-%d")
        instruments = InstrumentList.objects.filter(instrument_token = token_id)
        delta_days = (end_formatted - start_formatted).days

        if instruments.count() < 0:
            success = False
            message = "No such instrument"
        elif end_formatted < start_formatted:
            success = False
            message = "Start date is later than end date"
        elif frequency not in allowed_frequency:
            success = False
            message = "Not an allowed frequency; Only day and minute allowed."
        elif frequency == "minute" and delta_days > 60:
            success = False
            message = "Minute data is limited to 60 days"
        else:
            instrument = instruments[0]
            try:
                historical_data = kite.historical_data(token_id,start + " 00:00:00",end + " 23:59:59",frequency)
            except:
                success = False
                message = "Authentication Failed"
                return ({
                    'status':success,
                    'message':message
                })    
            total = len(historical_data)
            count = 0 
            if frequency == "day":
                existing_data = HistoricalPricesDay.objects.filter(instrument=instrument)
                existing_data.delete()
                for data in historical_data:
                    datetime_corrected =  data['date'] + datetime.timedelta(hours=5, minutes=30)
                    HistoricalPricesDay.objects.create(
                        instrument          = instrument
                        ,datetime            = datetime_corrected
                        ,open_price          = data['open']
                        ,high_price          = data['high']
                        ,low_price           = data['low']
                        ,close_price         = data['close']
                        ,volume              = data['volume']
                    )
                    count = count + 1
                    printProgressBar(count,total)

            elif frequency == "minute":
                existing_data = HistoricalPricesMinute.objects.filter(instrument=instrument)
                existing_data.delete()
                for data in historical_data:
                    datetime_corrected =  data['date'] + datetime.timedelta(hours=5, minutes=30)
                    HistoricalPricesMinute.objects.create(
                        instrument           = instrument
                        ,datetime            = datetime_corrected
                        ,open_price          = data['open']
                        ,high_price          = data['high']
                        ,low_price           = data['low']
                        ,close_price         = data['close']
                        ,volume              = data['volume']
                        ,tradedate           = datetime_corrected.date()
                    )
                    count = count + 1
                    printProgressBar(count,total)

            success = True
            message = "Historical prices downloaded and stored"

        return ({
                'status':success,
                'message':message
                })

class HistoricalAnalysis:

    def update_indicator(instrument_token,target_indicators=['return','sma','equal_sma']):
        instrument = trackedInstruments.objects.get(instrument__instrument_token = instrument_token)
        completeData = HistoricalPricesMinute.objects.filter(instrument= instrument.instrument)
        instrument_token = instrument.instrument.instrument_token
        instrument_data = []
        for data in completeData:
            instrument_data.append([instrument_token,data.datetime, data.tradedate, data.open_price, data.close_price, data.high_price, data.low_price, data.volume])

        instrument_df = pd.DataFrame(instrument_data, columns = ['instrument_token','datetime','tradedate','open_price', 'close_price','high_price','low_price','volume'])
        
        # Minute Return Update
        if 'return' in target_indicators:
            instrument_df['minute_return'] = instrument_df.groupby('instrument_token')['close_price'].pct_change() 

        # Simple Moving Averages - Equal Weighted
        if 'equal_sma' in target_indicators:
            instrument_df['equal_sma_2'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 2).mean())        
            instrument_df['equal_sma_3'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 3).mean())        
            instrument_df['equal_sma_4'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 4).mean())        
            instrument_df['equal_sma_5'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 5).mean())        
            instrument_df['equal_sma_10'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 10).mean())
            instrument_df['equal_sma_15'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 15).mean())
            instrument_df['equal_sma_20'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 20).mean())
            instrument_df['equal_sma_25'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 25).mean())
            instrument_df['equal_sma_30'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 30).mean())
            instrument_df['equal_sma_35'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 35).mean())
            instrument_df['equal_sma_40'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 40).mean())
            instrument_df['equal_sma_45'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 45).mean())
            instrument_df['equal_sma_50'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 50).mean())
            instrument_df['equal_sma_55'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 55).mean())
            instrument_df['equal_sma_60'] = instrument_df.groupby('instrument_token')['close_price'].transform(lambda x: x.rolling(window = 60).mean())

        # More weights to recent data
        if 'sma' in target_indicators:
            instrument_df['sma_2']  = Wilder(instrument_df['close_price'],2)
            instrument_df['sma_3']  = Wilder(instrument_df['close_price'],3)
            instrument_df['sma_4']  = Wilder(instrument_df['close_price'],4)
            instrument_df['sma_5']  = Wilder(instrument_df['close_price'],5)
            instrument_df['sma_10'] = Wilder(instrument_df['close_price'],10)
            instrument_df['sma_15'] = Wilder(instrument_df['close_price'],15)
            instrument_df['sma_20'] = Wilder(instrument_df['close_price'],20)
            instrument_df['sma_25'] = Wilder(instrument_df['close_price'],25)
            instrument_df['sma_30'] = Wilder(instrument_df['close_price'],30)
            instrument_df['sma_35'] = Wilder(instrument_df['close_price'],35)
            instrument_df['sma_40'] = Wilder(instrument_df['close_price'],40)
            instrument_df['sma_45'] = Wilder(instrument_df['close_price'],45)
            instrument_df['sma_50'] = Wilder(instrument_df['close_price'],50)
            instrument_df['sma_55'] = Wilder(instrument_df['close_price'],55)
            instrument_df['sma_60'] = Wilder(instrument_df['close_price'],60)

        # SMA Ratio
            instrument_df['sma_ratio_15on5'] = instrument_df['sma_15'] / instrument_df['sma_5']
            instrument_df['sma_ratio_20on5'] = instrument_df['sma_20'] / instrument_df['sma_5']
            instrument_df['sma_ratio_30on5'] = instrument_df['sma_30'] / instrument_df['sma_5']
    
        return instrument_df


    def define_position(indicator_df):
        df = indicator_df.sort_values('datetime')
        datelist = df.tradedate.unique()
        df_out = pd.DataFrame()
        for date in datelist:
            position = "none"
            previous_position = "none"
            df_filtered = df[df['tradedate'] == date]
            df_filtered['position'] = ""
            total_len_df = len(df_filtered)
            for row in range(total_len_df):
                if df_filtered['sma_ratio_20on5'][row] > 1:
                    if previous_position in ["bear","none"]:
                        position = "bull"
                    else:
                        position = previous_position
                else:
                    if previous_position in ["bull"]:
                        position = "bear"
                    else:
                        position = previous_position
                df_filtered['position'][row] = position
                previous_position = position
            df_out = df_out.append(df_filtered)
        return df_out


# Wrong Calculation
    def calculate_returns(position_df):
        df = position_df.sort_values('datetime')
        datelist = df.tradedate.unique()
        df_out = pd.DataFrame()
        for date in datelist:  
            df_filtered = df[df['tradedate'] == date]
            df_filtered['holding_price'] = np.nan
            total_len_df = len(df_filtered)
            previous_holding_price = np.nan
            holding_price = np.nan
            previous_position = "none"

            for row in range(total_len_df):
                if df_filtered['position'][row] == "none":
                    holding_price = np.nan
                elif df_filtered['position'][row] == "bull":
                    holding_price = df_filtered['close_price'][row]
                elif df_filtered['position'][row] == "bear":
                    if previous_position == "bull":
                        holding_price = df_filtered['close_price'][row]
                    else:
                        holding_price = previous_holding_price
                df_filtered['holding_price'][row] = holding_price
                previous_holding_price = holding_price
                previous_position = df_filtered['position'][row]
            
            df_out = df_out.append(df_filtered)
        return df_out



