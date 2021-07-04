# -*- coding: utf-8 -*-
import scrapy
from rezka.items import RezkaItem


class SpSpider(scrapy.Spider):
	name = 'sp'
	allowed_domains = ['rezka.ag']

	def start_requests(self):
		start_urls = ['https://rezka.ag/', 
						'https://rezka.ag/films/',
						'https://rezka.ag/series/', 
						'https://rezka.ag/cartoons/', 
						'https://rezka.ag/animation/'
						]
		for url in start_urls:
			yield scrapy.Request(url=url, callback=self.get_category_data)

	def get_category_data(self, response):
		page_number = response.xpath('//div[@class="b-navigation"]/a[last()-1]/text()').get()

		for page in range(1, int(page_number) + 1):
			if page == 1:
				yield scrapy.Request(url=response.url, callback=self.parse_items)
			else:
				url = response.urljoin(f'/page/{page}/')
				yield scrapy.Request(url=url, callback=self.parse_items)	

	def parse_items(self, response):
		for film in response.xpath('//div[@class="b-content__inline_items"]/div')[:-1]:
			film_url = film.xpath('.//div[@class="b-content__inline_item-cover"]/a/@href').get()
			yield scrapy.Request(url=film_url, callback=self.parse_film_info)

	def parse_film_info(self, response):

		item = RezkaItem()
						
		item['film_name'] = response.xpath('.//div[@class="b-post__title"]/h1/text()').get()
		item['category'] =response.url.split('https://rezka.ag/')[-1].split('/')[0]

		for param in response.xpath('//div[@class="b-post__infotable_right_inner"]/table/tr'):
			param_name = param.xpath('./td[1]/h2/text()').get()
			if param_name == 'Рейтинги':
				item['rating'] = param.xpath('./td/span[1]/span/text()').get()
			elif param_name == 'Дата выхода' or param_name == 'Год' or param_name == 'Год:':
				try:
					item['release_date'] = param.xpath('./td[last()]/text()').get() + param.xpath('./td[last()]/a/text()').get()
				except TypeError:
					item['release_date'] = param.xpath('./td[last()]/a/text()').get()
			elif param_name == 'Страна':
				item['country'] = param.xpath('./td[last()]/a[last()]/text()').get()
			elif param_name == 'Режиссер':
				data = param.xpath('.//span[@itemprop="name"]/text()').get()
				if not data:
					data = param.xpath('.//span[@class="item"]/text()').get()
				item['producer'] = data
			elif param_name == 'Жанр':
				genres = []
				for genre in param.xpath('.//span[@itemprop="genre"]/text()'):
					genres.append(genre.get())
				item['genre'] = ','.join(genres)
			elif param_name == 'Возраст':
				item['age_category'] = param.xpath('./td[last()]/span/text()').get()

		item['description'] = response.xpath('//div[@class="b-post__description_text"]/text()').get()
		item['film_url'] = response.url
		item['film_photo_url'] = response.xpath('//div[@class="b-sidecover"]/a/img/@src').get()

		return item
