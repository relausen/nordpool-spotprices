#! /usr/bin/env python

import sys

from datetime import date, datetime, timedelta, time
from functools import lru_cache

import colorama
import requests

from colorama import Fore

day_begin = time(6, 0, 0)
day_end = time(23, 0, 0)


@lru_cache
def eur_to_dkk_rate():
    exchange_rates = requests.get('https://cdn.forexvalutaomregner.dk/api/nationalbanken.json').json()
    usd_eur = exchange_rates['rates']['EUR']
    usd_dkk = exchange_rates['rates']['DKK']
    return usd_dkk/usd_eur


def eur_to_dkk(eur):
    return eur * eur_to_dkk_rate()


def is_night_time(data_time_string):
    return not (day_begin < datetime.fromisoformat(data_time_string).time() < day_end)


def print_prises_for(prices, night_only=False, now_color=Fore.GREEN):
    min_price = min(prices, key=lambda p: p['SpotPriceEUR'])['SpotPriceEUR']
    max_price = max(prices, key=lambda p: p['SpotPriceEUR'])['SpotPriceEUR']
    day_average_sum = sum(price_data['SpotPriceEUR'] / 10.0 for price_data in prices)
    day_average_price = eur_to_dkk(day_average_sum / float(len(prices)))

    shown_prices = prices if not night_only else [price_data for price_data in prices if is_night_time(price_data['HourDK'])]
    shown_average_sum = sum(price_data['SpotPriceEUR'] / 10.0 for price_data in shown_prices)
    shown_average_price = eur_to_dkk(shown_average_sum / float(len(shown_prices)))

    shown_price_sum = 0.0
    for price_data in shown_prices:
        price_time = datetime.fromisoformat(price_data['HourDK'])

        eur_price = price_data['SpotPriceEUR']
        dkk_price_entry = price_data['SpotPriceDKK']
        dkk_price = round(dkk_price_entry/10, 1) if dkk_price_entry is not None else round(eur_to_dkk(eur_price)/10, 1)
        shown_price_sum += dkk_price
        estimate_suffix = '' if dkk_price_entry is not None else '  *'
        min_max_suffix = ''
        if eur_price == min_price:
            min_max_suffix = ' (min)'
        elif eur_price == max_price:
            min_max_suffix = ' (max)'
        fg_color = now_color if price_time.date() == datetime.now().date() and price_time.hour == datetime.now().hour else ''
        print(f'{fg_color}{price_time} {dkk_price:>6}{estimate_suffix}{min_max_suffix}')
    print(f"Average, whole day: {round(day_average_price, 1)}")
    if night_only:
        print(f"Average, shown prices: {round(shown_average_price, 1)}")


def run(night_only):
    from_date = date.today()
    to_date = from_date + timedelta(days=2)

    query = f'''
      {{
        elspotprices(
          where:
            {{
              HourDK: {{ _gte: "{from_date}", _lt: "{to_date}" }},
              PriceArea: {{ _eq: "DK1" }}
            }},
            order_by: {{ HourDK: asc }},
        )
        {{
          HourDK,
          SpotPriceEUR,
          SpotPriceDKK
        }}
      }}
    '''

    headers = {
        'content-type': 'application/json',
    }

    prices_request = requests.post(
        'https://data-api.energidataservice.dk/v1/graphql',
        json={'query': query},
        headers=headers
    )

    all_prices = prices_request.json()['data']['elspotprices']
    prices_today = [price_data for price_data in all_prices if datetime.fromisoformat(price_data['HourDK']).date() == datetime.now().date()]
    prices_tomorrow = [price_data for price_data in all_prices if price_data not in prices_today]

    colorama.init(autoreset=True)
    print_prises_for(prices_today, night_only=night_only)
    if prices_tomorrow:
        print('-' * 24)
        print_prises_for(prices_tomorrow, night_only=night_only)
    colorama.deinit()


if __name__ == "__main__":
    night_only = len(sys.argv) > 1 and sys.argv[1] == "-n" # Yikes. Use argparse instead.
    run(night_only)
