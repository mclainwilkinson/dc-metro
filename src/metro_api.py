import board
import digitalio
import time
from adafruit_matrixportal.network import Network

from config import config
from secrets import secrets

# Keeping a global reference for this
_network = Network(status_neopixel=board.NEOPIXEL)

def sort_key(item: dict) -> int:
    try:
        return int(item['arrival'])
    except:
        return 0


class MetroApiOnFireException(Exception):
    pass

class MetroApi:
    def fetch_train_predictions(station_code: str, group: str) -> [dict]:
        return MetroApi._fetch_train_predictions(station_code, group, retry_attempt=0)

    def _fetch_train_predictions(station_code: str, group: str, retry_attempt: int) -> [dict]:
        try:

            api_url = config['metro_api_url'] + station_code
            train_data = _network.fetch(api_url, headers={
                'api_key': config['metro_api_key']
            }).json()


            # added to include bus information
            bus_api_url = config['metro_bus_url'] + config['bus_stop_code']
            bus_data = _network.fetch(bus_api_url, headers={
                'api_key': config['metro_api_key']
            }).json()

            print('Received responses from WMATA api...')

            trains = filter(lambda t: t['Group'] == group, train_data['Trains'])
            buses = bus_data['Predictions']

            normalized_trains = list(map(MetroApi._normalize_train_response, trains))
            normalized_buses = list(map(MetroApi._normalize_bus_response, buses))

            # combine train and bus results into sorted list, should produce same output format as previous code
            combined = normalized_trains + normalized_buses
            combined.sort(key=sort_key)

            return combined

        except RuntimeError:
            if retry_attempt < config['metro_api_retries']:
                print('Failed to connect to WMATA API. Reattempting...')
                # Recursion for retry logic because I don't care about your stack
                return MetroApi._fetch_train_predictions(station_code, group, retry_attempt + 1)
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
        if bus['Minutes'] < 1:
            arrival = 'ARR'
        else:
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
