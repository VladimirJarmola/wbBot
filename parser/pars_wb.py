from requests import Session
from time import sleep
from urllib.parse import quote


# https://user-geo-data.wildberries.ru/get-geo-info

result = {
    "page": "",
    "place": "",
    "status": None,
}

BASE_URL = "https://www.wildberries.ru"
URL = "https://search.wb.ru/exactmatch/ru/common/v4/search"
PAGE_LIMIT = 100
PAGE_START = 1
DELAY = 2


async def get_response(data: dict):
    search_query = data['search_query']
    vendor_code = data['vendor_code']
    
    query_format_ASCII = quote(search_query)

    headers = {
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Origin": BASE_URL,
        "Referer": f"https://www.wildberries.ru/catalog/0/search.aspx?search={query_format_ASCII}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "sec-ch-ua": 'Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        # 'x-queryid': 'qid972214069171014002220240311102816',
    }

    params = {
        "ab_testing": "false",
        "appType": 1,
        "curr": "rub",
        "dest": -1257786,
        "page": PAGE_START,
        "query": search_query,
        "resultset": "catalog",
        "sort": "popular",
        "spp": 30,
        "suppressSpellcheck": "false",
    }

    work = Session()
    work.get(BASE_URL)

    for i in range(PAGE_START, PAGE_LIMIT):
        current_page = params.get("page", None)
        sleep(DELAY)
        response = work.get(URL, headers=headers, params=params)
        place = find_place(response.json(), vendor_code)
        if place is not None:
            result["page"] = current_page
            result["place"] = place
            result["status"] = True
            work.close()
            return result
        if current_page is not None:
            params["page"] = i + 1
    result["status"] = False
    work.close()
    return result


def find_place(response, vendor_code):

    list_id = []
    products_raw = response.get("data", {}).get("products", None)
    
    if products_raw is not None and len(products_raw) > 0:
        for product in products_raw:
            list_id.append(product.get("id", None))
        if int(vendor_code) in list_id:
            place = list_id.index(int(vendor_code)) + 1
            return place
        else:
            return None
