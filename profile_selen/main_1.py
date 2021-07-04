from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from fake_useragent import UserAgent
from loguru import logger
from glob import glob

import psutil
import pyautogui
import requests
import datetime
import shutil
import time
import random
import json
import os

logger.add('main_log_file_1.log', format="{time} {level} {message}", level="ERROR")

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

	if not data['ok']:
		return None

	proxies = [[i['proxy'], i['IP'], i['status']] for i in data['list'] if i['status'] in config['PROXY_STATUS_TO_USE']]
	random.shuffle(proxies)

	for proxy in proxies:
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

	time.sleep(config['TIME_TO_SLEEP_AFTER_KILLIN_PROCESS'])

def remove_profile(profile_id):
	path_to_profile = f'{os.path.abspath(os.getcwd())}\\profiles\\{profile_id}'
	try:
		shutil.rmtree(path_to_profile)
	except Exception:
		logger.debug(f'Failed to delete profile {profile_id}.')

def delete_metrics(profile_id):
	path = os.path.abspath(os.getcwd())
	try:
		while 'BrowserMetrics' in os.listdir(f'{path}\\profiles\\{profile_id}'):
			try:
				shutil.rmtree(f'{path}\\profiles\\{profile_id}\\BrowserMetrics')
			except PermissionError:
				logger.debug(f'Failed to delete metrics in profile {profile_id}.')
				break
			time.sleep(0.5)
	except FileNotFoundError:
		logger.debug(f"Can't find profile {profile_id} to delete metrics.")

def locate_image(image_path, driver):
	size = driver.get_window_rect()
	if pyautogui.locateOnScreen(image_path, region=(size['x']+190,size['y']+225, 265, 120)):
		return True
	else:
		return False

def make_request(user_agent, profile_id):
	path_to_dir = os.path.abspath(os.getcwd())
	profiles_folder = f'user-data-dir={path_to_dir}\\profiles\\{profile_id}'

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
			time.sleep(config['PROXY_WAITING_TIMEOUT'])

	prefs = {
			'profile.default_content_settings.notifications':1,
			'profile.default_content_setting_values.notifications':1,
			'profile.contentSettings.notifications':1,
			'profile.content_settings.exceptions.notifications':1,
			'profile.managed_default_content_settings.notifications':1,
	}

	options = Options()
	options.add_argument(profiles_folder)
	#options.add_argument('profile-directory=Profile') #check if it works without this line
	#options.add_argument("--headless") #to run script in headless mode
	options.add_experimental_option('excludeSwitches', ['enable-logging']) #disables webdriver loggs
	#options.add_argument(f"user-agent={user_agent.random}") #to use ua from package
	options.add_argument(f"user-agent={next(user_agent)}") #to user ua from file
	options.add_experimental_option('prefs', prefs)
	options.add_argument(f'--proxy-server={proxy[0]}')

	driver = None
	try:
		driver = webdriver.Chrome(ChromeDriverManager().install(), options=options, service_log_path=os.path.devnull)
		driver.set_page_load_timeout(config['MAX_TIME_PAGE_LOADING'])
	except Exception:
		logger.error('An error occured during driver creation.')
		try:
			driver.quit()
		except Exception:
			kill_processes(driver)
		remove_profile(profile_id)

	try:
		driver.get(config['URL'])
		driver.implicitly_wait(config['MAX_TIME_PAGE_LOADING'])
	except Exception:
		logger.debug(f"Page haven't been loaded in time.")
		try:
			driver.quit()
		except Exception:
			kill_processes(driver)
		remove_profile(profile_id)
	else:
		time_to_sleep = config['TIME_TO_SLEEP_AFTER_LOADING']
		time.sleep(1)
		try:
			element = driver.find_element_by_xpath('//div[@class="icon icon-generic"] | //img[@alt="Google"]')
		except (NoSuchElementException, TimeoutException) as e:
			logger.info(f'Page loaded successfully. Waiting {time_to_sleep} seconds.')
			time.sleep(time_to_sleep)
		else:
			logger.debug('Page loaded with error.')
			try:
				driver.quit()
			except Exception:
				kill_processes(driver)
			remove_profile(profile_id)

	try:
		driver.quit()
	except Exception:
		kill_processes(driver)
		
	delete_metrics(profile_id)

@logger.catch
def main():
	os.environ['WDM_LOG_LEVEL'] = '0'
	os.environ['WDM_PRINT_FIRST_LINE'] = 'False'

	global config
	global proxies
	config = get_config('config_1.json')
	user_agent = get_user_agent('useragent.txt')
	proxies = get_proxy(config['PROXY_URL'])

	profile_id = 1

	while True:
		n = datetime.datetime.now()
		profile_id = str(int(time.mktime(n.timetuple()))) + '_' + n.strftime('%d-%m-%Y') #datetime in format 1624349992_22-06-2021
		make_request(user_agent, profile_id)

if __name__ == '__main__':
	main()