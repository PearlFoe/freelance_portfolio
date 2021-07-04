from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from fake_useragent import UserAgent
from loguru import logger

import subprocess
import psutil
import requests
import datetime
import time
import random
import json
import os

logger.add('main_log_file.log', format="{time} {level} {message}", level="ERROR")

def get_blacklist(file_name):
	data = None
	try:
		with open(file_name) as f:
			data = json.loads(f.read())
	except FileNotFoundError:
		data = []

	if not data:
		return []
	else:
		return data

def dump_blacklist(file_name, data):
	with open(file_name, 'w') as f:
		json.dump(data, f)

def check_proxy(proxy):
	full_list = get_blacklist('blacklist.json')

	if full_list:
		proxies = [i['proxy'] for i in full_list]

		for i in full_list:
			delta = datetime.datetime.now() - datetime.datetime.strptime(i['datetime'], '%Y-%m-%d %H:%M:%S.%f')
			if (delta.days*86400 + delta.seconds) >= (config['HOURS_TO_STAY_IN_BALCKLIST'] * 3600):
				full_list.remove(i)

		if proxy[1] in proxies: 
			return False
		else:
			full_list.append({
				'proxy':proxy[1],
				'datetime':str(datetime.datetime.now())
			})
	else:
		full_list.append({
			'proxy':proxy[1],
			'datetime':str(datetime.datetime.now())
		})

	dump_blacklist('blacklist.json', full_list)

	return True

def get_proxy(proxy_url):
	try:
		data = requests.get(proxy_url).json()
	except Exception:
		logger.debug('An error occured in getting proxies.')
		return None

	#modified = datetime.datetime.strptime(data['modified'], '%a, %d %b %Y %H:%M:%S %z')

	if not data['ok']:
		return None

	proxies = [[i['proxy'], i['IP']] for i in data['list']]

	for proxy in proxies:
		if proxy:
			yield proxy

def get_user_agent(file_name):
	user_agents = []
	with open(file_name) as f:
		user_agents = f.read().split('\n')

	while True:
		for _ in user_agents:
			yield random.choice(user_agents)

def get_config(file_name):
	data = None
	with open(file_name) as f:
		data = json.loads(f.read())

	return data

def kill_processes(driver):
	try:
		p = psutil.Process(driver.service.process.pid)
		for i in p.children(recursive=True):
			try:
				i.kill()
			except Exception:
				pass
		p.kill()
	except Exception:
		logger.debug('An error occured in killing processes.')

def make_request(user_agent):
	options = Options()
	#options.add_argument("--headless") #to run script in headless mode
	options.add_experimental_option('excludeSwitches', ['enable-logging']) #disables webdriver loggs

	#options.add_argument(f"user-agent={user_agent.random}") #to use ua from package
	options.add_argument(f"user-agent={next(user_agent)}") #to user ua from file

	global proxies
	if not proxies:
		logger.error('Empty proxy list.')

	proxy = None
	while True:
		try:
			proxy = next(proxies)
			while not check_proxy(proxy):
				proxy = next(proxies)
			break
		except StopIteration:
			proxies = get_proxy(config['PROXY_URL'])
			logger.info('Waiting new proxies.')
			time.sleep(10)

	options.add_argument(f'--proxy-server={proxy[0]}')
	
	driver = None
	try:
		driver = webdriver.Chrome(ChromeDriverManager().install(), options=options, service_log_path=os.path.devnull)
		driver.set_page_load_timeout(config['MAX_TIME_PAGE_LOADING'])
	except Exception:
		logger.error('An error occured during driver creation.')

	try:
		driver.get(config['URL'])
		driver.implicitly_wait(config['MAX_TIME_PAGE_LOADING'])
	except Exception:
		logger.debug(f"Page haven't been loaded in time.")
	else:
		time_to_wait = random.randint(
							config['MIN_TIME_TO_SLEEP'],
							config['MAX_TIME_TO_SLEEP']
							)
		logger.info(f'Page loaded successfully. Waiting {time_to_wait} seconds.')
		time.sleep(time_to_wait)

	try:
		driver.quit()
	except Exception:
		kill_processes(driver)

@logger.catch
def main():
	os.environ['WDM_LOG_LEVEL'] = '0'
	os.environ['WDM_PRINT_FIRST_LINE'] = 'False'

	global config
	global proxies
	config = get_config('config.json')
	user_agent = get_user_agent('useragent.txt')
	proxies = get_proxy(config['PROXY_URL'])

	while True:
		make_request(user_agent)
		
if __name__ == '__main__':
	main()