import requests
import time

from config import config
from secrets import secrets


from config import config

class MetroApiOnFireException(Exception):
    pass

class MetroApi:
    def fetch_train_predictions(group: str) -> [dict]:
        return MetroApi._fetch_train_predictions(group, retry_attempt=0)

    def _fetch_train_predictions(group: str, retry_attempt: int) -> [dict]:
        try:
            api_url = config['metro_api_url'] + config['metro_station_code']
            train_data = requests.get(api_url, headers={
                'api_key': config['metro_api_key']
            }).json()

            # added to include bus information
            bus_api_url = config['metro_bus_url'] + config['bus_stop_code']
            print(bus_api_url)
            bus_data = requests.get(bus_api_url, headers={
                'api_key': config['metro_api_key']
            }).json()

            print('Received responses from WMATA api...')

            trains = filter(lambda t: t['Group'] == group, train_data['Trains'])
            buses = bus_data['Predictions']

            normalized_trains = list(map(MetroApi._normalize_train_response, trains))
            normalized_buses = list(map(MetroApi._normalize_bus_response, buses))

            # combine train and bus results into sorted list, should produce same output format as previous code
            combined = normalized_trains + normalized_buses
            combined.sort(key=lambda t: int(t['arrival'])
                                if t['arrival'].isnumeric()
                                else (0 if t['arrival'] in ['ARR', 'BRD'] else 99))
            return combined

        except RuntimeError:
            if retry_attempt < config['metro_api_retries']:
                print('Failed to connect to WMATA API. Reattempting...')
                # Recursion for retry logic because I don't care about your stack
                return MetroApi._fetch_train_predictions(group, retry_attempt + 1)
            else:
                raise MetroApiOnFireException()

    def _normalize_train_response(train: dict) -> dict:
        line = train['Line']
        destination = train['Destination']
        arrival = train['Min']

        if destination == 'No Passenger' or destination == 'NoPssenger' or destination == 'ssenger':
            destination = 'No Psngr'

        return {
            'line_color': MetroApi._get_line_color(line),
            'destination': destination,
            'arrival': arrival
        }

    def _normalize_bus_response(bus: dict) -> dict:
        line = 'BUS'
        destination = bus['RouteID']
        arrival = str(bus['Minutes'])

        return {
            'line_color': MetroApi._get_line_color(line),
            'destination': destination,
            'arrival': arrival  # always number
        }

    def _get_line_color(line: str) -> int:
        if line == 'RD':
            return 0xFF0000
        elif line == 'OR':
            return 0xFF5500
        elif line == 'YL':
            return 0xFFFF00
        elif line == 'GR':
            return 0x00FF00
        elif line == 'BL':
            return 0x0000FF
        elif line == 'SV':
            return 0xAAAAAA
        else:
            # bus line
            return 0x0000FF


while True:
    preds = MetroApi.fetch_train_predictions('2')
    print(len(preds))
    for pred in preds:
        print(pred)
    print('-------------------------')
    time.sleep(5)
