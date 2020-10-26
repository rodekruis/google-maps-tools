# google-maps-tools
collection of scripts using Google Maps APIs

## Requirements
1. Python >= 3.7
2. [pandas](https://pypi.org/project/pandas/)
2. [geopandas](https://pypi.org/project/geopandas/)
2. [googlemaps services python client](https://pypi.org/project/googlemaps/)
3. A google maps API key:
   * login in the 510 google account (credentials in BitWarden)
   * copy [this key](https://console.cloud.google.com/apis/credentials/key/d549b609-a5d1-4ea9-b9c1-8de0aa37108a?authuser=1&folder=&organizationId=&project=emergency-data-support)

## google-maps-scraper
Scrape Places from Google Maps
* input: place type, country, search radius
* output: one table (csv) and one shapefile (gpkg) with place coordinates and details: phone number, website, type

See in-code comments for more details.

Contacts: [Jacopo Margutti](https://github.com/jmargutt)
