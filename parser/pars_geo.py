from requests import Session


BASE_URL = 'https://user-geo-data.wildberries.ru/get-geo-info'
# 'latitude': 54.98570,
        # 'longitude': 73.38877,


def get_geo(data: dict):

    params = {
        'latitude': data['latitude'],
        'longitude': data['longitude'],
    }

    work = Session()
    response = work.get(url=BASE_URL, params=params)
    return response
