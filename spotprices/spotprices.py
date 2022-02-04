from datetime import date, datetime, timedelta

import colorama
import requests

from colorama import Fore


def print_prises_for(prices, now_color=Fore.GREEN):
    min_price = min(prices, key=lambda p: p['SpotPriceEUR'])['SpotPriceEUR']
    max_price = max(prices, key=lambda p: p['SpotPriceEUR'])['SpotPriceEUR']

    for price_data in prices:
        price_time = datetime.fromisoformat(price_data['HourDK'])
        eur_price = price_data['SpotPriceEUR']
        dkk_price_entry = price_data['SpotPriceDKK']
        dkk_price = round(dkk_price_entry/10) if dkk_price_entry else round(eur_price*eur_dkk/10)
        estimate_suffix = '' if dkk_price_entry else '  *'
        min_max_suffix = ''
        if eur_price == min_price:
            min_max_suffix = ' (min)'
        elif eur_price == max_price:
            min_max_suffix = ' (max)'
        fg_color = now_color if price_time.date() == datetime.now().date() and price_time.hour == datetime.now().hour else ''
        print(f'{fg_color}{price_time} {dkk_price:>4}{estimate_suffix}{min_max_suffix}')
        # print(f'{fg_color}{price_time} {dkk_price:>4}{min_max_suffix}{estimate_suffix}{Style.RESET_ALL}')


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

exchange_rates = requests.get('https://cdn.forexvalutaomregner.dk/api/nationalbanken.json').json()
usd_eur = exchange_rates['rates']['EUR']
usd_dkk = exchange_rates['rates']['DKK']
eur_dkk = usd_dkk/usd_eur

all_prices = prices_request.json()['data']['elspotprices']
prices_today = [price_data for price_data in all_prices if datetime.fromisoformat(price_data['HourDK']).date() == datetime.now().date()]
prices_tomorrow = [price_data for price_data in all_prices if price_data not in prices_today]

colorama.init(autoreset=True)
print_prises_for(prices_today)
if prices_tomorrow:
    print('-' * 24)
    print_prises_for(prices_tomorrow)
colorama.deinit()
