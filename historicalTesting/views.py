from mmap import ACCESS_COPY
from django.core.checks import messages
from django.shortcuts import render
from credentials import zerodha_api_key,zerodha_secret_key
from kiteconnect import KiteConnect
from historicalTesting.models import *
from overall.views import *

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

    def create_session():
        success = False
        message = ""
        latest_token = tokens.objects.latest('created_at')
        access_token = latest_token.access_token
        kite = KiteConnect(zerodha_api_key)
        kite.set_access_token(access_token)
        success = True
        message = "Session Created"
        return ({
                 'status':success,
                 'message':message
                })


class InstrumentsDataFetch:
    def get_instruments_list():
        success = False
        message = ""
        kite = KiteConnect(zerodha_api_key)
        instruments = kite.instruments()
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

    def track_instrument(tokenID):
        success = False
        message = ""
        


    def untrack_instrument(tokenID):
        pass








        
    
