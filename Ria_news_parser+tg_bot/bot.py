import config
import telebot
import time

from bs4 import BeautifulSoup
from urllib.request import urlopen

bot = telebot.TeleBot(config.token)

root 		  = None
ria_last_time = None

def minutes(time):
	hours, minutes = time.split(':')
	minutes = int(minutes) + (int(hours) * 60)
	return minutes

def ria_news_request():
	html = urlopen('https://ria.ru/')
	soup = BeautifulSoup(html.read(), 'lxml')
	global root
	root = soup.find('div',  {'class':'lenta__item'})

def ria_news_time(root):

	return root.find('span', {'class':'lenta__item-date'}).text

def ria_news_print(root):

	bot.send_message(config.chat_id, root.find('span', {'class':'lenta__item-date'}).text + '\t' + root.find('span', {'class':'lenta__item-text'}).text + '\n' + root.a.attrs['href'])

def ria_news():
	ria_news_request()
	global ria_last_time
	new_time = ria_news_time(root)
	if (minutes(ria_last_time) < minutes(new_time)) or (minutes(new_time) < 90):
		ria_last_time = new_time
		time.sleep(10)
		ria_news_print(root)

ria_news_request()
ria_last_time = ria_news_time(root)

while True:
	ria_news()
	time.sleep(60)


