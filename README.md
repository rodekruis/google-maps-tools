# google-maps-tools
collection of scripts using Google Maps APIs

# requirements
1. Python >= 3.7
2. [pandas](https://pypi.org/project/pandas/)
2. [geopandas](https://pypi.org/project/geopandas/)
2. [googlemaps services python client](https://pypi.org/project/googlemaps/)

## GoogleMapsScraper.py
scrape Places from Google Maps
* input: place type, country, search radius
* output: one table (csv) and one shapefile (gpkg) with place coordinates and details: phone number, website, type

see in-code comments for more details
