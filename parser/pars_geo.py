from urllib.parse import parse_qs
from requests import Session

GEO_BASE_URL = 'https://user-geo-data.wildberries.ru/get-geo-info'
OSM_BASE_URL = 'https://nominatim.openstreetmap.org/search'
COUNTRY_LIST = {'Армения', 'Беларусь', 'Казахстан', 'Киргизия', 'Россия', 'Узбекистан'}

#получаем xinfo от wb
async def get_xinfo(data: dict = None):    
    
    if not data:
        payload = {
            'latitude': 55.625578,
            'longitude': 37.6063916,
        }
    else:
        payload = {
            'latitude': data['latitude'],
            'longitude': data['longitude'],
        }


    work = Session()

    response = work.get(url=GEO_BASE_URL, params=payload, timeout=1)
    dest = parse_qs(response.json().get('xinfo', None))['dest'][0]

    work.close()

    return dest

#получаем координаты от OSM
async def get_osm(query: str):
    payload = {
        'format': 'json',
        'q': query,
    }
    result = {
        'latitude': None,
        'longitude': None,
        'status': None,
    }
    
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'Cookie': 'SL_G_WPT_TO=ru; SL_GWPT_Show_Hide_tmp=1; SL_wptGlobTipTmp=1',
        'Priority': 'u=0, i',
        'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': "Windows",
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }

    work = Session()
    response = work.get(url=OSM_BASE_URL, headers=headers, params=payload, timeout=1)

    data = response.json()
    if response.status_code == 200 and len(data) != 0:
        result['latitude'] = data[0]['lat']
        result['longitude'] = data[0]['lon']
        address = data[0]['display_name']
    else:
        result['status'] = False
        work.close()
        return result
    
    if COUNTRY_LIST.intersection(address.split(' ')):
        result['status'] = True
    else:
        result['status'] = False
    
    work.close()

    return result