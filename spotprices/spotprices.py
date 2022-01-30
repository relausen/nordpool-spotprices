from datetime import date, datetime, timedelta

import colorama
import requests

from colorama import Fore, Style


headers = {
    'content-type': 'application/json',
}

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

prices_request = requests.post(
    'https://data-api.energidataservice.dk/v1/graphql',
    json={'query': query},
    headers=headers
)

exchange_rates = requests.get('https://cdn.forexvalutaomregner.dk/api/nationalbanken.json').json()
usd_eur = exchange_rates['rates']['EUR']
usd_dkk = exchange_rates['rates']['DKK']
eur_dkk = usd_dkk/usd_eur

colorama.init()

for price_data in prices_request.json()['data']['elspotprices']:
    price_time = datetime.fromisoformat(price_data['HourDK'])
    eur_price = price_data['SpotPriceEUR']
    dkk_price_entry = price_data['SpotPriceDKK']
    dkk_price = round(dkk_price_entry/10) if dkk_price_entry else round(eur_price*eur_dkk/10)
    suffix = '' if dkk_price_entry else '  *'
    fg_color = Fore.GREEN if price_time.date() == datetime.now().date() and price_time.hour == datetime.now().hour else ''
    print(f'{fg_color}{price_time} {dkk_price:>4}{suffix}{Style.RESET_ALL}')

colorama.deinit()
