#!/usr/local/bin/python3

import re
import time
import urllib3
import datetime
from bs4 import BeautifulSoup
from enum import Enum

TRACK_SHAPES = {
  "polygon s 5OB": "P5",
  "polygon s 4OB": "P4",
  "polygon s 3OB": "P3",
  "FAI trojúhelník": "TF",
  "trojúhelník s odletem z ramene": "T3",
  "trojúhelník": "T2",
  "2OB": "L2",
  "3OB": "L3",
  "4OB": "L4",
  "5OB": "L5",
  "návratová": "N",
  "FAI trojúhelník s odletem z ramene": "TF",
}

PLANE_ACRONYM = {
  "0705": "V5",
  "1600": "A1",
  "1177": "ZL",
  "1432": "DP",
  "1818": "SK",
  "1948": "GV",
  "1974": "EJ",
  "2424": "24",
  "2474": "24",
  "2912": "XJ",
  "3133": "6L",
  "3370": "JW",
  "3740": "ICQ",
  "3773": "ZE",
  "8522": "PK",
  "9000": "AF",
  "9722": "",
  "9902": "EB"
}

class Flight:
  def __init__(self, row):
    self.url = "http://cpska.cz/public/" + row.find_all("a")[-1]['href']
    self.cps_points = self.get_cps_points(row)
    if self.cps_points:
      self.flight_page = self.get_flight_page()
      self.date = self.get_date(row)
      self.pilot = self.get_name(row)
      self.copilot = self.get_copilot()
      self.lenght = row.find_all("td", class_="cllVzdal")[0].contents[0].split()[0]
      self.avg_speed = row.find_all("td", class_="cllVzdal")[1].contents[0].split()[0]
      self.aircraft_registration = self.get_aircraft_registration()
      self.plane = self.get_plane()
      self.plane_acronym = PLANE_ACRONYM.get(str(self.aircraft_registration))
      self.track_shape = self.get_track_shape()
      self.track_type = self.get_track_type()
      self.locality = row.find_all("td")[2].contents[0]

  def get_plane(self):
    try:
      return self.flight_page.find(id='right').find('h2').contents[0].contents[0]
    except AttributeError:
      return ""

  def get_copilot(self):
    try:
      return self.flight_page.find_all('div', class_="panel_pilot")[1].find('div', class_="jmeno").contents[0]
    except IndexError:
      return ""

  def get_track_type(self):
    track_type = self.flight_page.find(id='right').find_all('div', class_="panel_lt")[2].find_all('p')[0].contents[1][2:]
    if track_type == 'rychlostní let se změnou tratě za letu':
      return "15 %"
    else:
      return ""

  def get_track_shape(self):
    try:
      track_shape = self.flight_page.find(id='right').find_all('div', class_="panel_lt")[2].find_all('p')[0].contents[1][2:]
      return TRACK_SHAPES.get(track_shape)
    except:
      print(self.url)

  def get_flight_page(self):
    http = urllib3.PoolManager()
    r = http.request('GET', self.url)
    soup = BeautifulSoup(r.data, 'html.parser')
    return soup

  def get_aircraft_registration(self):
    try:
      ar=self.flight_page.find(id='right').find('h2').contents[1]
      return re.findall(r'\d+', ar)[0]
    except IndexError:
      return ""

  def get_cps_points(self, row):
    try:
      return row.find("td", class_="cllBody").contents[0].split()[0]
    except AttributeError:
      return ""

  def get_date(self, row):
    date = row.find("td", class_="cllDatum").find("a").contents[0]
    return datetime.datetime.strptime(date, '%d.%m.%Y').strftime('%d/%m/%y')

  def get_name(self, row):
    name = row.find("td", class_="jmeno").find("a").contents[0]
    return ' '.join(reversed(name.split(' ')))

def load_flights(year):
    CPS_URL="https://www.cpska.cz/public/index3.php?lpg=sezlet&filtr=clubs&filtr_soutez=all&filtr_trida=&filtr_zeme=cz&filtr_clubs=5&filtr_minclubs=5&filtr_pilot=all&filtr_glider=all&obdobi_rok={}&obdobi_mesic=00&obdobi_den=00&strankovani={}"
    http = urllib3.PoolManager()

    full_table = []

    for offset in (0, 100, 200, 300, 400, 500, 600, 700):
      r = http.request('GET', CPS_URL.format(year, offset))
      soup = BeautifulSoup(r.data, 'html.parser')

      regex = re.compile('row(Odd|Even)')
      page_table = soup.find("table", class_="tblList").find_all('tr', class_=regex)

      if not page_table:
      # no flights on next page
        break

      full_table = full_table + page_table

    flights = []
    for row in full_table:
      flights.append(Flight(row))

    flights.reverse()

    return flights

def print_csv(flights):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    for flight in flights:
      if flight.cps_points:
        #      da co pi co pl  ar ac ts   leng       awsp tt   cp
        with open(timestr + '.txt', 'a') as f:
            print(';{};{};{};{};{};;{};{};{};;;"{}";;;;;;;"{}";{};;;{};'.format(
            #print('=HYPERLINK("{}","{}"),CZ,{},{},{},,{},{},{},,,{},,,,,,,{},{},,,{},'.format(flight.url,
                                                       flight.date,
                                                       flight.locality,
                                                       flight.pilot,
                                                       flight.copilot,
                                                       flight.plane,
                                                       flight.aircraft_registration,
                                                       flight.plane_acronym,
                                                       flight.track_shape,
                                                       flight.lenght.replace('.',','),
                                                       flight.avg_speed.replace('.',','),
                                                       flight.track_type,
                                                       flight.cps_points
                                                       )
                                                      , file=f)

def main():
    year = "2023"
    flights = load_flights(year)
    print_csv(flights)


if __name__ == "__main__":
    main()
