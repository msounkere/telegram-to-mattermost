import datetime

def timestamp_from_date(date):
    d = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
    return int(d.strftime("%s")) * 1000

print(timestamp_from_date("2020-04-20T20:15:54+00:00"))