# -*- coding: utf-8 -*-
"""
Created on Wed May 22 11:49:32 2019

@author: Jacopo Margutti

this is a script to extract "places" from Google maps using its API
API documentation: https://developers.google.com/places/web-service/search

configurable settings:
1) type(s) of places to search for
2) country
3) bounding box
4) output file name
5) max money to be spent
"""

import numpy as np
import pandas as pd
import math
import geopandas as gpd
from geopy.geocoders import Nominatim
import time
import googlemaps
import os
path = os.path.dirname(os.path.realpath(__file__))
os.chdir(path)

gmaps = googlemaps.Client(key='<my-API-key>')

# SETTINGS #############################################################################################################

# WHAT DO YOU WANT TO SEARCH FOR
# use only supported types, see https://developers.google.com/places/web-service/supported_types
search_words_manual = ['school', 'primary_school', 'secondary_school', 'university']

# IN WHICH COUNTRY
search_country = 'Lebanon'  # set False if you do not care about the country

# IN WHICH BOUNDING BOX
# N.B. standard format (e.g. https://boundingbox.klokantech.com/) is [long_start, lat_start, long_end, lat_end]
# write longitudes and latitudes in correct order, because it is not checked anywhere
# also, the script can not handle crossing -180/180 longitude
lat_start = 33.797122
lat_end = 33.926553
long_start = 35.459023
long_end = 35.608712

# STEP OF THE SEARCH GRID AND RADIUS
# each search will happen within a circle of fixed radius; for each search, a maximum of 60 places will be returned.
# the radius has to be chosen based on the maximum number of places of given type expected to be found within it.
# rule of thumb: 1km for dense cities, 5km for towns, 50km for rural areas
radius = 50000  # in meters
STEP = 1.41421356237 * radius / 111000.  # in degrees, approximate at the equator

# OUTPUT FILE NAME
# without extension
out_filename = 'search_results_beirut_education'

# MAX COST
# in USD
MAX_SPENT = 100

########################################################################################################################

# read all the data that is needed

# dictionary with codes for each country
codes = pd.read_csv('input/codes.csv', header=0)
codes['Code'] = codes['Code'].str.lower()

# in geoloc_dict we save points for which the country is already identified
# we do that to deacrease the number of requests to geopy and computation time
geoloc_dict = pd.DataFrame(columns=['latitude', 'longitude', 'country'])
SPENT = 0.00  # here we will save the costs


def long_step(latitude):
    # computes step in longitude so that the step in longitude and latitude is the same in meters
    return round(STEP/math.cos(math.radians(latitude)),  2)


def which_country(latitude, longitude):
    # finds a country given latitude and longitude
    global geoloc_dict
    geolocator = Nominatim(user_agent="my_app")
    place = geolocator.reverse((str(latitude)+', '+str(longitude)), timeout = 300).raw ## returns a nearby address for a point
    country = 'Unknown'
    if not 'error' in place:
        if 'country_code' in place['address']:
            country_code = place['address']['country_code']
            country = codes[codes['Code']==country_code]['Name'].values[0]  # uses codes distionary to find full country name
    geoloc_dict = geoloc_dict.append({'latitude':latitude, 'longitude': longitude, 'country':country}, ignore_index = True)
    time.sleep(1) # geopy does not really like when you do more than 1 request per second
    return country


def list_of_countries(latitude, longitude):
    # finds list of countries in a circle around given place
    set_of_countries = set()
    # we look at four corners of the square with our point in the middle and side = STEP,
    # check to which country they belong and return these countries
    for x in [-0.5*STEP, 0.5*STEP]:
        corner_latitude = latitude+x
        for y in [-long_step(corner_latitude)/2, long_step(corner_latitude)/2]:
            corner_longitude = round(longitude+y, 2)
            country = 'Unknown'
            # if the point is already in geoloc_dict we read it from there
            if not geoloc_dict[(geoloc_dict['latitude']==corner_latitude)&(geoloc_dict['longitude']==corner_longitude)].empty:
                country = geoloc_dict[(geoloc_dict['latitude']==corner_latitude)&(geoloc_dict['longitude']==corner_longitude)]['country'].values[0]
            else:   # if not, call which_country function
                country = which_country(corner_latitude, corner_longitude)
            if country != 'Unknown':
                set_of_countries.add(country) # adding the country of the corner to the set
    list_of_countries = list(set_of_countries)
    return list_of_countries


def text_search(latitude, longitude, search_word):
    # searches for a red cross around given location using given language
    # expensive search, up to 60 results, returns information about places
    global SPENT
    result_columns = ['search_lat', 'search_long', 'search_words', 'place_id', 'place_name', 'place_address', 'place_lat', 'place_long', 'distance']
    final_results = pd.DataFrame(columns = result_columns)
    location = str(latitude)+','+str(longitude)
    # relevant_fields = ['place_id', 'formatted_address', 'geometry/location', 'name', 'perm_closed']
    CONTINUE = True
    page = 0
    next_page_token = False
    all_pages = pd.DataFrame()
    while CONTINUE:
        page = page + 1
        #print(page)
        if not next_page_token: ## if there is no next_page_token, we perform normal search
            this_page = gmaps.places_nearby(type=search_word, location=location, radius=radius)
            # this_page = gmaps.places(search_word, location=location, radius=radius)
        else:
            # if there is we look at the next page
            time.sleep(3)  # there is a short delay before the token works, so we wait
            this_page = gmaps.places_nearby(type=search_word, location=location, radius=radius, page_token=next_page_token)
            # this_page = gmaps.places(type=search_word, location = location, radius = radius, page_token = next_page_token)
        SPENT = SPENT + 0.0274224
        # transform search result to a nice data frame
        df_this_page = pd.DataFrame.from_records(this_page['results'])
        if 'geometry' in df_this_page.columns:
            df_this_page['latitude'] = [x['location']['lat'] for x in df_this_page['geometry']]
            df_this_page['longitude'] = [x['location']['lng'] for x in df_this_page['geometry']]
            df_this_page['distance'] = (df_this_page['latitude'] - latitude)**2+(df_this_page['longitude'] - longitude)**2
            # add them to the final results
            if page == 1:
                all_pages = df_this_page
            else:
                all_pages = all_pages.append(df_this_page)
        # now we define if we need to do request for the next page or not
        if 'next_page_token' not in this_page.keys():
            CONTINUE = False
        else:
            next_page_token = this_page['next_page_token']

    if 'place_id' in all_pages:
        final_results['place_id'] = all_pages['place_id']
        final_results['place_name'] = all_pages['name']
        try:
            final_results['place_address'] = all_pages['formatted_address']
        except:
            pass
        final_results['place_lat'] = all_pages['latitude']
        final_results['place_long'] = all_pages['longitude']
        final_results['distance'] = all_pages['distance']
        final_results[['search_lat', 'search_long', 'search_words']] = [latitude, longitude, search_word]
    return final_results


# START SCRIPT #########################################################################################################

latitude_range = np.arange(lat_start, lat_end, STEP)
first_search_results = pd.DataFrame(columns=['latitude', 'longitude', 'search_words', 'place_id'])

result_columns = ['search_lat', 'search_long', 'search_words', 'place_id', 'place_name', 'place_address', 'place_lat', 'place_long', 'distance']
total_search_results = pd.DataFrame(columns=result_columns)

# we iterate over all grid points and perform a search around each point
print('doing search')
count_steps = 0
for latitude in latitude_range:
    longitude = long_start
    longitude_range = np.arange(long_start, long_end, longitude + long_step(latitude))
    while longitude < long_end:
        longitude = round(longitude + long_step(latitude), 2)
        count_steps += 1
total_steps = count_steps
print('total number of steps:', total_steps)
count_steps = 0

for latitude in latitude_range:
    longitude = long_start
    longitude_range = np.arange(long_start, long_end, longitude + long_step(latitude))
    while longitude < long_end:
        longitude = round(longitude + long_step(latitude), 2)
        # find countries intersecting with the circle
        countries_here = list_of_countries(latitude, longitude)
        print('step', count_steps, '/', total_steps, ': searching at', latitude, longitude)
        if search_country:
            if not search_country in countries_here:
                continue
            countries_here = [search_country]
        len_s = len(total_search_results)
        for search_word in search_words_manual:
            # print('searching for ', search_word)
            ## search aroung this place using current search word from the list
            new_total_search_results = text_search(latitude, longitude, search_word)
            if len(new_total_search_results) == 60:
                print('WARNING: possible places missed (hit limit of 60 places)')
            total_search_results = total_search_results.append(new_total_search_results)
        print('----> found', len(total_search_results)-len_s, 'places')
        count_steps += 1

        if SPENT > MAX_SPENT:
            print(f'WARNING: more than {MAX_SPENT} euro spent! breaking')
            break
        time.sleep(0.5)


'''
Nice! We have the list of places. 
Let's remove duplicates and places outside of country of interest
'''
results = total_search_results
results['count'] = results.groupby(['place_id'])['place_id'].transform('count') #count how many times we found each place
places = results[['place_id', 'place_name', 'place_address', 'place_lat', 'place_long', 'count']]
places = places.drop_duplicates() 
if search_country:  # if we use search country, drop the locations outside of it
    try:
        places['country'] = [x.split(', ')[-1] for x in places['place_address']]
        places = places[places['country'] == search_country]
    except:
        pass

'''
For now we know the name and address of each place.
If we want to have also phone number, website and opening hours, we need to run another request
'''
places_extended = places
places_extended = places_extended.drop('count', axis = 1)
places_extended['phone_number'] = ''
places_extended['website'] = ''
places_extended['url'] = ''
places_extended['country'] = ''
places_extended['adm_lvl_1'] = ''
places_extended['adm_lvl_2'] = ''
places_extended['types'] = ''  # types contain the types of the place returned by google maps

# iterate over found places and request additional information about each place
print('doing extended search')
for place_id in places_extended['place_id']:
    
    place_details = gmaps.place(place_id)['result']  # request to google maps, returns a lot of information
    # Places Details per ID should be free
    # check https://developers.google.com/places/web-service/usage-and-billing#places-details-id-refresh
    SPENT = SPENT + 0.
    
    # save the information in places_extended
    if 'international_phone_number' in place_details:
        places_extended.loc[places_extended['place_id']==place_id, 'phone_number'] = place_details['international_phone_number']
    if 'website' in place_details:
        places_extended.loc[places_extended['place_id']==place_id, 'website'] = place_details['website']
    if 'url' in place_details:
        places_extended.loc[places_extended['place_id']==place_id, 'url'] = place_details['url']
    if 'types' in place_details:
        places_extended.loc[places_extended['place_id']==place_id, 'types'] = ", ".join(place_details['types'])
    
    address = pd.DataFrame.from_records(place_details['address_components'])
    address.loc[[len(x)==0 for x in address['types']], 'types'] = ['Unknown']
    address['types'] = [x[0] for x in address['types']]    
    if 'country' in address['types'].values:
        places_extended.loc[places_extended['place_id'] == place_id, 'country'] = address.loc[address['types'] == 'country', 'long_name'].values[0]
    if 'administrative_area_level_1' in address['types'].values:
        places_extended.loc[places_extended['place_id'] == place_id, 'adm_lvl_1'] = address.loc[address['types'] == 'administrative_area_level_1', 'long_name'].values[0]
    if 'administrative_area_level_2' in address['types'].values:
        places_extended.loc[places_extended['place_id'] == place_id, 'adm_lvl_2'] = address.loc[address['types'] == 'administrative_area_level_2', 'long_name'].values[0]
    if SPENT > MAX_SPENT:
        print('WARNING: more than 50 eur spent! breaking')
        break
    
if search_country:        
    places_extended = places_extended[places_extended['country'] == search_country]

print('COMPLETED!')
print(len(places_extended), 'places found')
print(SPENT, 'USD spent')

# SAVE RESULTS
if len(places_extended) > 0:
    # save in csv
    places_extended.to_csv(out_filename+'.csv')
    # save in shapefile
    gdf = gpd.GeoDataFrame(places_extended, geometry=gpd.points_from_xy(places_extended.place_long, places_extended.place_lat))
    gdf.to_file(out_filename+'.gpkg', layer='gmaps', driver="GPKG")
