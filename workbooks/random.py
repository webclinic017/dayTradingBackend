start_date = '2021-12-01'
end_date = '2021-12-15'
frequecy = 'minute'
instrument = InstrumentList.objects.get(instrument_token = 136432388)
if frequecy == "minute":
    distinct_dates = HistoricalPricesMinute.objects.filter(instrument = instrument).values('tradedate').distinct()
elif frequecy == "day":
    distinct_dates = HistoricalPricesDay.objects.filter(instrument = instrument).values('tradedate').distinct()
list_dates = []
for out in distinct_dates:
    list_dates.append(str(out['tradedate']))

print(list_dates)

start_date_dt = datetime.datetime.strptime(start_date,"%Y-%m-%d").date()
end_date_dt = datetime.datetime.strptime(end_date,"%Y-%m-%d").date()
diff = (end_date_dt - start_date_dt).days
list_date_ranges = []
start_date_defined = False

final_start_date = ""
final_end_date = start_date_dt
# print(str(start_date_dt))

for i in range(diff):
    start_date_str = str(start_date_dt)
    
    # if day_diffs < 6:
    if not start_date_defined:
        if start_date_str not in list_dates:    
            final_start_date = start_date_dt
            start_date_defined = True

    else:
        day_diffs = (start_date_dt - final_start_date).days            
        # if day_diffs < 6:
            
    

    # if start_date_defined:
    #     if start_date_str not in list_dates:
    #         day_diffs = (start_date_dt - final_start_date).days            
    #         if day_diffs < 6:
    #             start_date_dt = start_date_dt + datetime.timedelta(days=1)
    #         if day_diffs >= 6:
    #             pass
    #         else:
    #             start_date_dt = start_date_dt + datetime.timedelta(days=1)

    #         start_date_dt = start_date_dt + datetime.timedelta(days=1)
    #         print("end:"+str(end))
    #     else:
    #         start_date_dt = start_date_dt + datetime.timedelta(days=1)
    # else:
    #     if start_date_str not in list_dates:    
    #         final_start_date = start_date_dt
    #         start_date_defined = True
    #         start_date_dt = start_date_dt + datetime.timedelta(days=1)
    #         print("start:"+str(final_start_date))
    #     else:
    #         start_date_dt = start_date_dt + datetime.timedelta(days=1)
    


# num_loop = diff//6
# count = 0
# for i in range(num_loop):
#     if i == 0:
#         start = start_date_dt +  datetime.timedelta(days=5*i)
#         end = start_date_dt +  datetime.timedelta(days=5*i + 5)
#     else:
#         start = end +  datetime.timedelta(days=1)
#         end = start +  datetime.timedelta(5)
#     print(start,end)
#     count = count + 1
    # print(token_id)
    # printProgressBar(count,num_loop)