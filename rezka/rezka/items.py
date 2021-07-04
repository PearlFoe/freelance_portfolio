# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RezkaItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    film_name = scrapy.Field()
    category = scrapy.Field()
    rating = scrapy.Field()
    release_date = scrapy.Field()
    country = scrapy.Field()
    producer = scrapy.Field()
    genre = scrapy.Field()
    age_category = scrapy.Field()
    description = scrapy.Field()
    film_url = scrapy.Field()
    film_photo_url = scrapy.Field()
