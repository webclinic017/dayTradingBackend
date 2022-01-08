from mmap import ACCESS_COPY
from django.core.checks import messages
from django.shortcuts import render
from credentials import zerodha_api_key,zerodha_secret_key
from kiteconnect import KiteConnect
from historicalTesting.models import *
from overall.views import *
import datetime

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



        

        








        
    
