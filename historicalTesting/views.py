from cmath import nan
from curses import beep
from mmap import ACCESS_COPY
from sqlite3 import Date
from sre_constants import SUCCESS
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
import matplotlib.ticker as ticker
import openpyxl

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
        indicator_ax.fill_between(instrument_df['datetime'], horizontal_line, instrument_df[below_column], where = (instrument_df[below_column] >= horizontal_line), color='g', alpha=0.3, interpolate=True)
        indicator_ax.fill_between(instrument_df['datetime'], horizontal_line, instrument_df[below_column], where = (instrument_df[below_column]  < horizontal_line), color='r', alpha=0.3, interpolate=True)

    price_ax.xaxis.set_major_formatter(ticker.NullFormatter())
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
        

def plot_returns(returns_df,top_columns,bottom_column):
    fig = plt.figure(figsize=(16,10))
    fig.subplots_adjust(hspace=0)
    plt.rcParams.update({'font.size': 14})
    price_ax = plt.subplot(2,1,1)
    for col in top_columns:
        price_ax.plot(returns_df.datetime, returns_df[col], label=col)

    price_ax.legend(loc="upper left", fontsize=12)

    indicator_ax = plt.subplot(2, 1, 2)
    indicator_ax.plot(returns_df['datetime'],returns_df[bottom_column], color='k', linewidth = 1, alpha=0.7, label=bottom_column)
    indicator_ax.legend(loc="upper left", fontsize=12)
    indicator_ax.set_ylabel(bottom_column)

    price_ax.xaxis.set_major_formatter(ticker.NullFormatter())
    indicator_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    price_ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1.0,decimals=2))
    indicator_ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1.0,decimals=2))    

    price_ax.grid(b=True, linestyle='--', alpha=0.5)
    indicator_ax.grid(b=True, linestyle='--', alpha=0.5)
    
    price_ax.set_facecolor((.94,.95,.98))
    indicator_ax.set_facecolor((.98,.97,.93))
    
    
    price_ax.margins(0.05, 0.2)
    indicator_ax.margins(0.05, 0.2)

    price_ax.tick_params(left=False, bottom=False)
    indicator_ax.tick_params(left=False, bottom=False, labelrotation=45)
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
        latest_token = tokens.objects.latest('created_at')
        access_token = latest_token.access_token
        kite = KiteConnect(zerodha_api_key)
        kite.set_access_token(access_token)
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
    def download_all_tracked_instrument_data(frequency,start_date,end_date):
        tracked_instruments = trackedInstruments.objects.all()
        count_all = 0
        total_load = tracked_instruments.count()
        for instrument in tracked_instruments:
            instrument_token = instrument.instrument.instrument_token
            InstrumentDataFetch.download_long_minute_data(
                                                        token_id=instrument_token,
                                                        frequency=frequency,
                                                        start_date=start_date,
                                                        end_date=end_date
                                                        )

        

    def download_long_minute_data(token_id,frequency,start_date,end_date):
        start_date = start_date
        end_date = end_date
        start_date_dt = datetime.datetime.strptime(start_date,"%Y-%m-%d").date()
        end_date_dt = datetime.datetime.strptime(end_date,"%Y-%m-%d").date()
        diff = (end_date_dt - start_date_dt).days
        num_loop = diff//6 + 1
        last_loop = diff%6


        count = 0
        for i in range(num_loop):
            if i == 0:
                start = start_date_dt +  datetime.timedelta(days=5*i)
                end = start_date_dt +  datetime.timedelta(days=5*i + 5)
            else:
                if ((i + 1) == num_loop):
                    start = end +  datetime.timedelta(days=1)
                    end = start +  datetime.timedelta(last_loop)
                else:
                    start = end +  datetime.timedelta(days=1)
                    end = start +  datetime.timedelta(5)
            InstrumentDataFetch.update_stored_historical_data(token_id,frequency,str(start),str(end),long=True)
            count = count + 1
            printProgressBar(count,num_loop)


    def update_stored_historical_data(token_id,frequency,start,end,long=False):
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
            # existing_data = 

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
                for data in historical_data:
                    datetime_corrected =  data['date'] + datetime.timedelta(hours=5, minutes=30)
                    if HistoricalPricesDay.objects.filter(instrument = instrument, datetime = datetime_corrected).count() == 0:
                        HistoricalPricesDay.objects.create(
                            instrument          = instrument
                            ,datetime            = datetime_corrected
                            ,open_price          = data['open']
                            ,high_price          = data['high']
                            ,low_price           = data['low']
                            ,close_price         = data['close']
                            ,volume              = data['volume']
                            ,tradedate           = datetime_corrected.date()
                        )
                    else:
                        pass
                    count = count + 1
                    if not long:
                        printProgressBar(count,total)

            elif frequency == "minute":
                for data in historical_data:
                    datetime_corrected =  data['date'] + datetime.timedelta(hours=5, minutes=30)
                    # if HistoricalPricesMinute.objects.filter(instrument = instrument, datetime = datetime_corrected).count() == 0:
                    if HistoricalPricesMinute.objects.filter(instrument = instrument, datetime = datetime_corrected).count() == 0:
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
                    else:
                        pass
                    count = count + 1
                    if not long:
                        printProgressBar(count,total)

            success = True
            message = "Historical prices downloaded and stored"

        return ({
                'status':success,
                'message':message
                })

class HistoricalAnalysis:
    def calculate_fees(price,type,broker="zerodha",num_units=1.0):
        if broker == "zerodha":
            order_size = num_units * price
            brokerage =  0.0003 * order_size
            if type == "sell":
                stt_ctt	= 0.00025 * order_size
            else:
                stt_ctt	= 0
            transaction_charges	= 0.0000345 * order_size 
            gst = 0.18 * (brokerage + stt_ctt + transaction_charges) 
            if order_size >= 10000000:
                sebi_charges = (order_size//1000000)*10
            else:
                sebi_charges = 0 

            if type == "buy":
                stamp_charges = 0.00003 * order_size         
            else:
                stamp_charges = 0
            
            total_fees = brokerage + stt_ctt + transaction_charges + gst + sebi_charges + stamp_charges
        return total_fees

    def calculate_trade_return(sell_price, get_in_price,broker="zerodha",num_units=1,with_fees=True):
        if with_fees:
            calculated_return = (sell_price*num_units - HistoricalAnalysis.calculate_fees(broker=broker,num_units=num_units,price=sell_price,type="sell") - HistoricalAnalysis.calculate_fees(broker=broker,num_units=num_units,price=get_in_price,type="buy"))/(get_in_price*num_units)-1
        else:
            calculated_return = (sell_price*num_units)/(get_in_price*num_units)-1
        return calculated_return
    
    def update_indicator(instrument_token,target_indicators=['simple_weighted_sma','equal_sma']):
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
        if 'simple_weighted_sma' in target_indicators:
            instrument_df['weighted_sma_2']  = Wilder(instrument_df['close_price'],2)
            instrument_df['weighted_sma_3']  = Wilder(instrument_df['close_price'],3)
            instrument_df['weighted_sma_4']  = Wilder(instrument_df['close_price'],4)
            instrument_df['weighted_sma_5']  = Wilder(instrument_df['close_price'],5)
            instrument_df['weighted_sma_10'] = Wilder(instrument_df['close_price'],10)
            instrument_df['weighted_sma_15'] = Wilder(instrument_df['close_price'],15)
            instrument_df['weighted_sma_20'] = Wilder(instrument_df['close_price'],20)
            instrument_df['weighted_sma_25'] = Wilder(instrument_df['close_price'],25)
            instrument_df['weighted_sma_30'] = Wilder(instrument_df['close_price'],30)
            instrument_df['weighted_sma_35'] = Wilder(instrument_df['close_price'],35)
            instrument_df['weighted_sma_40'] = Wilder(instrument_df['close_price'],40)
            instrument_df['weighted_sma_45'] = Wilder(instrument_df['close_price'],45)
            instrument_df['weighted_sma_50'] = Wilder(instrument_df['close_price'],50)
            instrument_df['weighted_sma_55'] = Wilder(instrument_df['close_price'],55)
            instrument_df['weighted_sma_60'] = Wilder(instrument_df['close_price'],60)

        # SMA Ratio
            instrument_df['weighted_sma_ratio_15on5'] = instrument_df['weighted_sma_15'] / instrument_df['weighted_sma_5']
            instrument_df['weighted_sma_ratio_20on5'] = instrument_df['weighted_sma_20'] / instrument_df['weighted_sma_5']
            instrument_df['weighted_sma_ratio_30on5'] = instrument_df['weighted_sma_30'] / instrument_df['weighted_sma_5']
            instrument_df['weighted_sma_ratio_10on5'] = instrument_df['weighted_sma_10'] / instrument_df['weighted_sma_5']        
            instrument_df['weighted_sma_ratio_10on3'] = instrument_df['weighted_sma_10'] / instrument_df['weighted_sma_3']        
        
        return instrument_df
    
    def calculate_returns(position_df,broker="zerodha",num_units = 1,with_fees=True):
        """
        Provide sorted positions dataframes 
        """
        # print(df)
        df = position_df.sort_values(by=['datetime'], ascending=True)
        datelist = df.tradedate.unique()
        df_out = pd.DataFrame()
        date_summary = []
        hwm_summary = []
        return_summary = []
        max_dd_summary = []
        strategy_cat = []
        strategy_sub_cat = []
        strategy_details = []
        total_purchases = []
        total_sales = []
        instrument_token = []
        df['trade_return'] = 0.0
        df['hwm'] = 1.0
        df['drawdown'] = 0.0
        df['cumulative_return'] = 0.0
        df['purchase_flag'] = 0 
        df['sell_flag'] = 0 
        df['with_fees'] = with_fees
        
        for date in datelist:  
            df_filtered = df[df['tradedate'] == date]
            total_len_df = len(df_filtered)
            previous_position = "none"
            calculated_return = 0
            get_in_price = 0 
            hwm = 1.0
            port_return = 1.0
            max_drawdown = 0.0
            purchases = 0 
            sales = 0 

            df_filtered.reset_index(inplace = True, drop = True)                
            for row in range(total_len_df):
                if df_filtered.at[row,'position'] == "none":
                    if previous_position == "bull":
                        calculated_return = HistoricalAnalysis.calculate_trade_return(broker=broker,num_units=num_units,sell_price = df_filtered.at[row,'close_price'], get_in_price= get_in_price,with_fees=with_fees)
                        get_in_price = 0
                        sales = sales + 1
                    else:
                        get_in_price = 0
                        calculated_return = 0 
                elif df_filtered.at[row,'position'] == "bull":
                    if previous_position in ["none","bear"]:
                        get_in_price = df_filtered.at[row,'close_price']
                        calculated_return = 0 
                        purchases = purchases + 1
                    else:
                        calculated_return = 0 

                elif df_filtered.at[row,'position'] == "bear":
                    if previous_position == "bull":
                        calculated_return = HistoricalAnalysis.calculate_trade_return(broker=broker,num_units=num_units,sell_price = df_filtered.at[row,'close_price'], get_in_price= get_in_price,with_fees=with_fees)
                        get_in_price = 0
                        sales = sales + 1
                    else:
                        calculated_return = 0 
                        get_in_price = 0 
                    
                df_filtered.at[row,'trade_return'] = calculated_return
                previous_position = df_filtered.at[row,'position']

                port_return = port_return * ( 1.0 + calculated_return)
                hwm = max(hwm, port_return)
                drawdown = hwm - port_return 
                max_drawdown = max(max_drawdown,drawdown)
                df_filtered.at[row,'hwm'] = hwm
                df_filtered.at[row,'drawdown'] = drawdown
                df_filtered.at[row,'cumulative_return'] = port_return

            hwm_summary.append(hwm)
            return_summary.append(port_return)
            max_dd_summary.append(max_drawdown)
            date_summary.append(date)
            total_sales.append(sales)
            total_purchases.append(purchases)
            strategy_cat.append(df_filtered['strategy_cat'][0])
            strategy_sub_cat.append(df_filtered['sub_cat'][0])
            strategy_details.append(df_filtered['description'][0])

            instrument_token.append(df_filtered['instrument_token'][0])
            df_out = df_out.append(df_filtered)
            
        data_summary_out = {
            'instrument_token':instrument_token,
            'strategy_cat':strategy_cat,
            'strategy_sub_cat':strategy_sub_cat,
            'strategy_details':strategy_details,
            'with_fees':with_fees,
            'date':date_summary,
            'day_return':return_summary,
            'max_drawdown':max_dd_summary,
            'high_water_mark':hwm,
            'total_sales':total_sales,
            'total_purchases':total_purchases,
        }
        
        df_summary_daily = pd.DataFrame(data_summary_out)
        return {
                'output_data':df_out,
                'daily_summary':df_summary_daily
        }


    def calculate_all_strategies(write_output_data = False):
        strategies = HistoricalAnalysis.strategy_sub_category_dict
        with_fees = True
        tracked_instruments = trackedInstruments.objects.all()
        count_all = 0
        count_strategy = 0 
        count_token = 0 
        total_load = tracked_instruments.count() * len(list(strategies.keys()))
        for instrument in tracked_instruments:
            instrument_token = instrument.instrument.instrument_token
            df = HistoricalAnalysis.update_indicator(instrument_token,list(strategies.keys()))
            for strategy in strategies:
                sub_strategies = strategies[strategy]
                for sub_strategy in sub_strategies:
                    df_sub_strategy = HistoricalAnalysis.define_position(indicator_df=df,strategy_category=str(strategy),strategy_sub_category=str(sub_strategy))                    
                    df_return = HistoricalAnalysis.calculate_returns(df_sub_strategy,num_units=1,with_fees=with_fees)            
                    daily_summary = df_return['daily_summary']
                    if count_all == 0:
                        comparative_summary = daily_summary
                    else:
                        comparative_summary = comparative_summary.append(daily_summary)
                    count_all = count_all + 1
                count_strategy = count_strategy + 1
                printProgressBar(count_strategy,total_load)
            if count_token == 0:
                df_out = df
            else:
                df_out = df_out.append(df)
            count_token = count_token + 1
        print('Writing Excel Summary')    
        comparative_summary.reset_index(inplace = True, drop = True)
        book1 = openpyxl.load_workbook('/Users/shashwatyadav/Desktop/Trading Outputs/TradingOutputSummary.xlsx')
        writer1 = pd.ExcelWriter('/Users/shashwatyadav/Desktop/Trading Outputs/TradingOutputSummary.xlsx', engine='openpyxl') 
        writer1.book = book1
        writer1.sheets = dict((ws.title, ws) for ws in book1.worksheets)
        comparative_summary.to_excel(writer1, "Output")
        writer1.save()
        if write_output_data:
            df_out.reset_index(inplace = True, drop = True)
            df_out['datetime'] = str(df_out['datetime'])
            df_out['tradedate'] = str(df_out['tradedate'])
            print('Writing Output Data')    
            book2 = openpyxl.load_workbook('/Users/shashwatyadav/Desktop/Trading Outputs/TradingOutputData.xlsx')
            writer2 = pd.ExcelWriter('/Users/shashwatyadav/Desktop/Trading Outputs/TradingOutputData.xlsx', engine='openpyxl') 
            writer2.book = book2
            writer2.sheets = dict((ws.title, ws) for ws in book2.worksheets)
            df.to_excel(writer2,"Data")
            writer2.save()
        
        output = {
            'message':'calculated return',
            'success':True
            }
        return output


    strategy_sub_category_dict = {
                            'simple_weighted_sma':{
                                '20_5':{
                                    'up_variable': 'weighted_sma_ratio_20on5',
                                    'down_variable':'weighted_sma_ratio_20on5',
                                    'details':'Weighted SMA 20 on 5 > 1'
                                    },
                                '10_3':{
                                    'up_variable': 'weighted_sma_ratio_10on3',
                                    'down_variable':'weighted_sma_ratio_10on3',
                                    'details':'Weighted SMA 10 on 3 > 1'
                                    },
                                '30_5':{
                                    'up_variable': 'weighted_sma_ratio_30on5',
                                    'down_variable':'weighted_sma_ratio_30on5',
                                    'details':'Weighted SMA 30 on 5 > 1'
                                    }    
                                }
                            }


    def define_position(indicator_df,strategy_category,strategy_sub_category):
        df = indicator_df.sort_values(by=['datetime'], ascending=True)
        datelist = df.tradedate.unique()
        df_out = pd.DataFrame()
        df['position'] = ""
        if strategy_category == "simple_weighted_sma":
            for date in datelist:                
                position = "none"
                previous_position = "none"
                df_filtered = df[df['tradedate'] == date]
                total_len_df = len(df_filtered)
                df_filtered.reset_index(inplace = True, drop = True)
                for row in range(total_len_df):
                    if (row + 1) == total_len_df:
                        position = "none"
                    else:                        
                        target_up_indicator = df_filtered.at[row,((HistoricalAnalysis.strategy_sub_category_dict[strategy_category])[strategy_sub_category])['up_variable']]
                        # target_down_indicator = df_filtered.at[row,((HistoricalAnalysis.strategy_sub_category_dict[strategy_category])[strategy_sub_category])['down_variable']]
                        if target_up_indicator > 1:
                            if previous_position in ["bear","none"]:
                                position = "bull"
                            else:
                                position = previous_position
                        else:
                            if previous_position in ["bull"]:
                                position = "bear"
                            else:
                                position = previous_position
                                
                    df_filtered.at[row,'position'] = position
                    # df_filtered.loc[row,position_index] = position
                    previous_position = position
                df_out = df_out.append(df_filtered)
            df_out['strategy_cat'] = strategy_category
            df_out['sub_cat'] = strategy_sub_category
            df_out['description'] = ((HistoricalAnalysis.strategy_sub_category_dict[strategy_category])[strategy_sub_category])['details']
        
        df_out.reset_index(inplace = True, drop = True)                
        return df_out


        

    # def calculate_all_strategies():
    #     pass


# output_data_2.loc[3,'instrument_token'] = 2
# output_data_2