from django.db import models
import json
# Create your models here.
from overall.models import *

class tokens(BaseModel):
    request_token = models.CharField(max_length=100)
    access_token = models.CharField(max_length=100)
    def __str__(self):
        return json.dumps({
                            'id':self.id,
                            'request_token':self.request_token,
                            'access_token':self.access_token,
                            'created_at':self.created_at
                            })

class InstrumentList(BaseModel):
    instrument_token    = models.CharField(max_length=50,db_index=True)
    exchange_token      = models.CharField(max_length=50,db_index=True) 
    tradingsymbol       = models.CharField(max_length=50,db_index=True)
    name                = models.CharField(max_length=100,null=True,db_index=True)
    last_price          = models.FloatField()
    expiry              = models.DateField(null=True)
    strike              = models.FloatField(null=True)
    tick_size           = models.FloatField()
    lot_size            = models.IntegerField()
    instrument_type     = models.CharField(max_length=50,db_index=True)
    segment             = models.CharField(max_length=50,db_index=True)
    exchange            = models.CharField(max_length=50,db_index=True)
    def __str__(self):
        return json.dumps({ 
                            'id':self.id,
                            'instrument_token':self.instrument_token,
                            'name':self.name,
                            'tradingsymbol':self.tradingsymbol,
                            'exchange_token':self.exchange_token
                            })

class trackedInstruments(BaseModel):
    instrument    = models.ForeignKey(InstrumentList,on_delete=models.CASCADE,null=True)
    def __str__(self):
        return json.dumps({
                            'id':self.id,
                            'instrument_token':self.instrument.instrument_token,
                            'name':self.instrument.name,
                            'trading_symbol':self.instrument.tradingsymbol
                            })


class HistoricalPricesMinute(BaseModel):
    instrument          = models.ForeignKey(InstrumentList,on_delete=models.CASCADE,null=True)
    datetime            = models.DateTimeField()
    open_price          = models.FloatField()
    high_price          = models.FloatField()
    low_price           = models.FloatField()
    close_price         = models.FloatField()
    volume              = models.FloatField()
    tradedate           = models.DateField()
    def __str__(self):
        return json.dumps({
                            'id':self.id,
                            'instrument_token':self.instrument.instrument_token,
                            'name':self.instrument.name,
                            'trading_symbol':self.instrument.tradingsymbol,
                            'high':self.high_price,
                            'low':self.low_price,
                            'open':self.open_price,
                            'close':self.close_price,
                            'volume':self.volume
                            })

class HistoricalPricesDay(BaseModel):
    instrument          = models.ForeignKey(InstrumentList,on_delete=models.CASCADE,null=True)
    datetime            = models.DateTimeField()
    open_price          = models.FloatField()
    high_price          = models.FloatField()
    low_price           = models.FloatField()
    close_price         = models.FloatField()
    volume              = models.FloatField()
    def __str__(self):
        return json.dumps({
                            'id':self.id,
                            'instrument_token':self.instrument.instrument_token,
                            'name':self.instrument.name,
                            'trading_symbol':self.instrument.tradingsymbol,
                            'high':self.high_price,
                            'low':self.low_price,
                            'open':self.open_price,
                            'close':self.close_price,
                            'volume':self.volume
                            })

    
    