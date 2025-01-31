import scrapy
import csv
from datetime import datetime
from os import path
from geopy.geocoders import Nominatim
from scrapy.spiders import Spider
from scrapy import Request
from scrapy import Selector
import psycopg2
import os
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

class FlatSpiderPsql(Spider):
    name = "flat_spider_pqsl"
    allowed_domains = ["inberlinwohnen.de"]
    start_urls = ["https://inberlinwohnen.de/wohnungsfinder/"]
    custom_settings = {
        "USER_AGENT": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": True
    }
    
    def start_requests(self):
        # Load existing links from the results table or create it if it doesn't exist
        existing_links = set()
        
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        
        connection = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port="5432")
        cursor = connection.cursor()
        cursor.execute("SELECT link FROM results")
        existing_links = set(link[0] for link in cursor.fetchall())
        cursor.close()
        connection.close()

        # Make requests for each flat page
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, meta={'existing_links': existing_links})

    def parse(self, response):
        id_counter = 1
        existing_links = response.meta.get('existing_links', set())
        rows = []

        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        
        connection = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port="5432")
        cursor = connection.cursor()

        cursor.execute("SELECT MAX(id) FROM results")
        result = cursor.fetchone()
        max_id = result[0] if result[0] else 0
        id_counter = max_id + 1
        # Read existing links from the results table
        cursor.execute("SELECT link FROM results")
        existing_links.update(link[0] for link in cursor.fetchall())

        # Initialize the geolocator
        geolocator = Nominatim(user_agent="my_app")

        def get_area_code(latitude, longitude):
            geolocator = Nominatim(user_agent="flatbot")  # Replace "your_app_name" with your user agent
            location = geolocator.reverse((latitude, longitude), exactly_one=True)
            if location:
                address = location.raw['address']
                area_code = address.get('postcode', '')
                neighbourhood = address.get('suburb', '')
                city = address.get('city', '')
                return area_code, neighbourhood, city
            return '', '', ''
        
        for flat in response.css('li[id^="flat_"]'):
            link = flat.css('a::attr(href)').get()
            if link in existing_links:
                continue

            rooms = flat.css('strong:nth-of-type(1)::text').get()
            size = flat.css('strong:nth-of-type(2)::text').get()
            price = flat.css('strong:nth-of-type(3)::text').get()

            # Remove '.' and replace ',' with '.' in rooms, price, and size
            rooms = rooms.replace('.', '').replace(',', '.') if rooms else None
            size = size.replace('.', '').replace(',', '.') if size else None
            price = price.replace('.', '').replace(',', '.') if price else None

            # Convert rooms, size, and price to float and divide price and size by 100
            rooms = float(rooms) if rooms else None
            size = float(size) if size else None
            price = float(price) if price else None

            # Geocode the address to fetch latitude and longitude
            address = flat.css('a.map-but::text').get()
            location = geolocator.geocode(address)
            latitude = location.latitude if location else None
            longitude = location.longitude if location else None
            area_code, neighbourhood, city = get_area_code(latitude, longitude)

            rows.append({
                'ID': str(id_counter),
                'address': address,
                'rooms': rooms,
                'size': size,
                'price': price,
                'link': link,
                'image_url': flat.css('figure.flat-image::attr(style)').get().split('(')[1][:-3],
                'latitude': latitude,
                'longitude': longitude,
                'postcode': int(area_code) if area_code else None,
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'neighbourhood': neighbourhood,
                'city': city
            })

            id_counter += 1

        # Insert new results into the results table
        for row in rows:
            cursor.execute(
                "INSERT INTO results (ID, address, rooms, size, price, link, image_url, latitude, longitude, postcode, datetime, neighbourhood, city) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    row['ID'],
                    row['address'],
                    row['rooms'],
                    row['size'],
                    row['price'],
                    row['link'],
                    row['image_url'],
                    row['latitude'],
                    row['longitude'],
                    row['postcode'],
                    row['datetime'],
                    row['neighbourhood'],
                    row['city']
                )
            )

        # Commit the transaction and close the cursor and connection
        connection.commit()
        cursor.close()
        connection.close()
