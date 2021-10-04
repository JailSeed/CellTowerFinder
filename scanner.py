# Скрипт для определения координат базовых станций с помощью API от Яндекс by JailSeed

import json
import requests
from requests.structures import CaseInsensitiveDict

MCC = ""  # Введите здесь MCC вашей страны. Для Беларуси: 257
MNC = ""  # Введите здесь MNC вашей сети. Для Беларуси: 1 - A1, 2 - MTC, 4 - Life, 6 - BeCloud
network = ""  # Введите здесь поколение вашей сети: 2G, 3G, 4G
LAC = ""  # Введите здесь LAC для 2G/3G или TAC для 4G
CID_start = ""  # Введите здесь начальный CellID для поиска. Формат: начальный_cid.начальный_сектор
CID_end = ""  # Введите здесь конечный CellID для поиска. Формат: конечный_cid.конечный_сектор
RNC = ""  # Введите здесь RNC. Только для 3G!!!
API_key = ""  # Ваш ключ API, получить бесплатно здесь: https://yandex.ru/dev/locator/keys/get/
API_url = "http://api.lbs.yandex.net/geolocation"  # URL Yandex API, не трогать без нужды


def create_xml(file):
    file.write('<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://earth.google.com/kml/2.2">\n')
    file.write('<Document>\n<name>CID scanner by JailSeed</name>\n<open>1</open>\n<Style id="v">\n<IconStyle>\n<color>ff0000ff</color>\n<scale>1.0</scale>\n<Icon>\n<href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>\n</Icon>\n</IconStyle>\n</Style>\n<Folder>\n<name>LAC: %s</name>\n<visibility>1</visibility>\n<Folder>\n<name></name>\n<visibility>1</visibility>\n' % LAC)


def write_coordinates(file, cid, sector, x, y):
    file.write('<Placemark>\n<name>%s/%i.%i</name>\n<LookAt>\n<longitude>%s</longitude>\n<latitude>%s</latitude>\n<altitude>0</altitude>\n</LookAt>\n<styleUrl>#v</styleUrl>\n<Point>\n<coordinates>%s,%s,0</coordinates>\n</Point>\n</Placemark>\n' % (LAC, cid, sector, y, x, y, x))


def parse_cycle(file, start, end):
    current_cid = -1
    for CID in range(start, end + 1):
        x, y = get_coordinates(str(CID))
        if x is not None and y is not None:
            if network == "2G":
                cid = int(CID / 10)
                sector = int(CID % 10)
                print("CID %i.%i found (%s, %s)" % (cid, sector, x, y))
                if current_cid != cid:
                    file.write('</Folder>')
                    file.write('<Folder>\n<name>%i</name>\n<visibility>1</visibility>' % cid)
                    current_cid = cid
                write_coordinates(file, cid, sector, x, y)
            elif network == "3G":
                cid = int((CID % 65536) / 10)
                sector = int((CID % 65536) % 10)
                print("CID %i.%i found (%s, %s)" % (cid, sector, x, y))
                if current_cid != cid:
                    file.write('</Folder>\n')
                    file.write('<Folder>\n<name>CID: %i</name>\n<visibility>1</visibility>' % cid)
                    current_cid = cid
                write_coordinates(file, cid, sector, x, y)
            elif network == "4G":
                cid = int(CID / 256)
                sector = int(CID % 256)
                print("eNB %i.%i found (%s, %s)" % (cid, sector, x, y))
                if current_cid != cid:
                    file.write('</Folder>')
                    file.write('<Folder>\n<name>%i</name>\n<visibility>1</visibility>' % cid)
                    current_cid = cid
                write_coordinates(file, cid, sector, x, y)
        else:
            if network == "2G":
                print("CID %i.%i not found" % (int(CID / 10), int(CID % 10)))
            elif network == "3G":
                print("CID %i.%i not found" % (int(CID % 65536 / 10), int(CID % 65536 % 10)))
            elif network == "4G":
                print("eNB %i.%i not found" % (int(CID / 256), int(CID % 256)))


def get_coordinates(cid):
    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    data = 'json={"common": {"version": "1.0", "api_key": "%s"}, "gsm_cells": [ { "countrycode": %s, "operatorid": %s, "cellid": %s, "lac": %s }]}' % (API_key, MCC, MNC, cid, LAC)
    try:
        resp = requests.post(API_url, headers=headers, data=data)
    except Exception as e:
        print(e)
        exit()
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
    create_xml(file)
    if network == "2G":
        parse_cycle(file, int(CID_start.replace(".", "")), int(CID_end.replace(".", "")))
    elif network == "3G":
        LCID_start = int(RNC) * 65536 + int(CID_start.replace(".", ""))
        LCID_end = int(RNC) * 65536 + int(CID_end.replace(".", ""))
        parse_cycle(file, LCID_start, LCID_end)
    elif network == "4G":
        LCID_start = int(CID_start.split(".")[0]) * 256 + int(CID_start.split(".")[1])
        LCID_end = int(CID_end.split(".")[0]) * 256 + int(CID_end.split(".")[1])
        parse_cycle(file, LCID_start, LCID_end)
    file.write('</Folder>\n</Folder>\n</Document>\n</kml>\n')
    file.close()


if __name__ == "__main__":
    main()