import json
from seleniumwire import webdriver
from seleniumwire.utils import decode
import pandas as pd
from dateutil import parser
import pytz  # $ pip install pytz
from tzlocal import get_localzone  # $ pip install tzlocal
import aiohttp
import asyncio
import time

DC_TO_WASH = True
NEW_SCRAPE = True
ACCEPTABLE_STATIONS = ["Union Station", "NY Moynihan Train Hall at Penn Station"]
LIST_OF_ACCEPTABLE_KEYS = ['_id', 'arrive_datetime', 'depart_datetime', 'price', 'arrive_name', 'arrive_cityname',
                           'depart_name', 'depart_cityname', 'trip_id']  # 'arrive_id', 'depart_id',]


def print_train_options(train_data):
    for train in train_data:
        print('$' + str(train['price']) + ' leaves ' + train['depart_datetime'])


def write_json_to_file(filename, json_data):
    with open(filename, "w") as outfile:
        outfile.write(json.dumps(json_data, indent=4))
        outfile.close()


def format_date_string(date_to_format):
    local_tz = get_localzone()
    date = parser.parse(date_to_format).replace(tzinfo=pytz.utc).astimezone(local_tz)
    date = date.strftime('%a %b %d at %I:%M %p')
    return date


# use for when you want to reformat vals, rn just reformatting the date keys
def format_vals(itinerary):
    for key in itinerary.keys():
        if key in "depart_datetime" or key in "arrive_datetime":
            itinerary[key] = format_date_string(itinerary[key])
    return itinerary


# filter out if there are transfers and if the method is not just the train
# filter out if stations are not in list of acceptable stations
def determine_whether_to_include_itinerary(itinerary, date):
    itinerary_departure_date = itinerary['depart_datetime'].split("T")[0]
    # sometimes itinerary_departure_date is not the same date as we queried in the url, so filters these out
    if itinerary['transfers'] != 0 or itinerary_departure_date != date:
        return False
    if itinerary['depart_name'] not in ACCEPTABLE_STATIONS or itinerary[
        'arrive_name'] not in ACCEPTABLE_STATIONS:
        return False
    return 'bus' not in itinerary['vehicle_types']


def filter_and_sort(data, date_list):
    # creates a list of dicts
    itineraries_by_day = list(map(lambda x: json.loads(x.split("window.__INITIAL_STATE__ = ")[1].split("</script")[0])[
        'DUCKS/TRIPS']['TRIP_DATA']['trips'], data))
    filtered_result = []
    for index, itinerary in enumerate(itineraries_by_day):  # for each day
        for key in itinerary.keys():  # go through each itinerary of the day
            if determine_whether_to_include_itinerary(itinerary[key], date_list[index]):
                new_itinerary = {k: itinerary[key][k] for k in LIST_OF_ACCEPTABLE_KEYS}
                new_itinerary = format_vals(new_itinerary)
                filtered_result.append(new_itinerary)
    return filtered_result


async def fetch(url, session):
    async with session.get(url) as response:
        return await response.text()


async def asynchronous_scrape(urls):
    lst = []
    async with aiohttp.ClientSession() as session:
        for number in range(len(urls)):
            task = asyncio.ensure_future(fetch(urls[number], session))
            lst.append(task)
        return await asyncio.gather(*lst)


def get_urls(start_date, end_date, departure_city, arrival_city, weekdays):
    date_list = []
    wanderu_URL = "https://www.wanderu.com/en-us/depart/"
    DC_url = "Washington%2C%20DC%2C%20USA"
    NYP_url = "New%20York%2C%20NY%2010119%2C%20USA"
    if departure_city == "DC":
        wanderu_URL += DC_url + "/"
    elif departure_city == "NYC":
        wanderu_URL += NYP_url + "/"
    if arrival_city == "DC":
        wanderu_URL += DC_url + "/"
    elif arrival_city == "NYC":
        wanderu_URL += NYP_url + "/"

    dates = pd.date_range(start_date, end_date, freq='D', normalize=True)
    string_to_list = list(weekdays)
    weekdays_list = list(map(int, string_to_list))
    urls = []
    for date in dates:
        if date.dayofweek in weekdays_list:
            date = str(str(date).split(" ")[0])
            urls.append(wanderu_URL + date)
            date_list.append(date)
    return urls, date_list


# start_date and end_date: yyyy-dd-mm
# departure_city and arrival_city: DC or NYC
# weekdays list of numbers 0-6 representing which days should be included where 0 is Monday and 6 is Sunday
def main_scrape(start_date, end_date, departure_city, arrival_city, weekdays):
    start_time = time.time()
    print(start_time)
    if NEW_SCRAPE:
        # get urls to scrap
        urls, date_list = get_urls(start_date, end_date, departure_city, arrival_city, weekdays)
        # asynchronously scrape
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        future = asyncio.ensure_future(asynchronous_scrape(urls))
        unfiltered_data = loop.run_until_complete(future)
        all_train_data = filter_and_sort(unfiltered_data, date_list)
        write_json_to_file("output.json", all_train_data)
    else:
        with open("output.json", "r") as readfile:
            all_train_data = json.load(readfile)
    # print how long this took
    print_train_options(all_train_data)
    print("--- %s seconds ---" % (time.time() - start_time))
    return all_train_data


if __name__ == '__main__':
    main_scrape('2022-09-25', '2022-09-25', 'DC', 'NYC', '0123456')
