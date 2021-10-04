# Скрипт для определения координат базовых станций с помощью API от Яндекс by JailSeed

import json
import requests
from requests.structures import CaseInsensitiveDict

MCC = ""  # Введите здесь MCC вашей страны. Для Беларуси: 257
MNC = ""  # Введите здесь MNC вашей сети. Для Беларуси: 1 - A1, 2 - MTC, 4 - Life, 6 - BeCloud
network = ""  # Введите здесь поколение вашей сети: 2G, 3G, 4G
LAC = ""  # Введите здесь LAC для 2G/3G или TAC для 4G
CID_start = ""  # Введите здесь начальный Cell ID для поиска. Формат: начальный_cid.начальный_сектор
CID_end = ""  # Введите здесь конечный Cell ID для поиска. Формат: конечный_cid.конечный_сектор
RNC = ""  # Введите здесь RNC. Только для 3G!!!
API_key = ""  # Ваш ключ API, получить бесплатно здесь: https://yandex.ru/dev/locator/keys/get/ (после входа в аккаунт введите абсолютно любой домен)
API_url = "http://api.lbs.yandex.net/geolocation"  # URL Yandex API, не трогать без нужды
not_found = False  # Если True - информация о том, что БС не найдена будет выводится в консоль


def create_kml(file):
    file.write('<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://earth.google.com/kml/2.2">\n')
    file.write('<Document>\n<name>CID scanner by JailSeed</name>\n<open>1</open>\n<Style id="v">\n<IconStyle>\n<color>ff0000ff</color>\n<scale>1.0</scale>\n<Icon>\n<href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>\n</Icon>\n</IconStyle>\n</Style>\n<Folder>\n<name>LAC: %s</name>\n<visibility>1</visibility>\n<Folder>\n<name></name>\n<visibility>1</visibility>\n' % LAC)


def create_folder(file, cid):
    file.write('</Folder>')
    file.write('<Folder>\n<name>CID: %i</name>\n<visibility>1</visibility>' % cid)


def write_coordinates(file, cid, sector, x, y):
    file.write('<Placemark>\n<name>%s/%i.%i</name>\n<LookAt>\n<longitude>%s</longitude>\n<latitude>%s</latitude>\n<altitude>0</altitude>\n</LookAt>\n<styleUrl>#v</styleUrl>\n<Point>\n<coordinates>%s,%s,0</coordinates>\n</Point>\n</Placemark>\n' % (LAC, cid, sector, y, x, y, x))


def save_kml(file):
    file.write('</Folder>\n</Folder>\n</Document>\n</kml>\n')
    file.close()


def parse_cycle(file, cid_start, cid_end, sector_start, sector_end):
    current_cid = -1
    for CID in range(cid_start, cid_end + 1):
        for sector in range(sector_start, sector_end + 1):
            if network == "2G":
                x, y = get_coordinates(file, str(CID) + str(sector))
            elif network == "3G":
                LCID = int(RNC) * 65536 + int(str(CID) + str(sector))
                x, y = get_coordinates(file, str(LCID))
            elif network == "4G":
                LCID = CID * 256 + sector
                x, y = get_coordinates(file, str(LCID))
            if x is not None and y is not None:
                print("CID %i.%i found (%s, %s)" % (CID, sector, x, y))
                if current_cid != CID:
                    create_folder(file, CID)
                    current_cid = CID
                write_coordinates(file, CID, sector, x, y)
            elif not_found is True:
                print("CID %i.%i not found" % (CID, sector))


def get_coordinates(file, cid):
    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    data = 'json={"common": {"version": "1.0", "api_key": "%s"}, "gsm_cells": [ { "countrycode": %s, "operatorid": %s, "cellid": %s, "lac": %s }]}' % (
    API_key, MCC, MNC, cid, LAC)
    try:
        resp = requests.post(API_url, headers=headers, data=data)
    except Exception as e:
        print(e)
        save_kml(file)
        exit(-1)
    json_data = json.loads(resp.text)
    x = str(json_data["position"]["latitude"])
    y = str(json_data["position"]["longitude"])
    restype = json_data["position"]["type"]
    precision = json_data["position"]["precision"]
    if restype == "gsm" and precision <= 99999:
        return x, y
    else:
        return None, None


def main():
    file = open('%s_%s0%s_%s_%s-%s.kml' % (network, MCC, MNC, LAC, CID_start, CID_end), "w")
    create_kml(file)
    cid_start = int(CID_start.split(".")[0])
    cid_end = int(CID_end.split(".")[0])
    sector_start = int(CID_start.split(".")[1])
    sector_end = int(CID_end.split(".")[1])
    parse_cycle(file, cid_start, cid_end, sector_start, sector_end)
    save_kml(file)


if __name__ == "__main__":
    main()
