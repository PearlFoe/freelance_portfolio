from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from fake_useragent import UserAgent
from loguru import logger
from glob import glob

import psutil
import operator
import pyautogui
import requests
import datetime
import shutil
import time
import random
import json
import os
import re

logger.add('main_log_file_2.log', format="{time} {level} {message}", level="ERROR")

def get_proxy(proxy_url):
	try:
		data = requests.get(proxy_url).json()
	except Exception:
		logger.debug('An error occured in getting proxies.')
		return None

	#modified = datetime.datetime.strptime(data['modified'], '%a, %d %b %Y %H:%M:%S %z')

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

def get_profiles():
	path = os.path.abspath(os.getcwd())
	profiles = os.listdir(f'{path}\\profiles')

	p = [{'time':int(re.search('\d{10}', i).group()), 'id':i} for i in profiles]
	p.sort(key=operator.itemgetter('time'))

	return [i['id'] for i in p]

def locate_notifiation(image_path):
	size = pyautogui.size()
	if pyautogui.locateOnScreen(image_path, region=(size[0]-440,size[1]-600, 450, 700)):
		return True
	else:
		return False

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
		

def delete_profile(profile_id, counter):
	path_to_dir = os.path.abspath(os.getcwd())
	profiles_folder = f'user-data-dir={path_to_dir}\\profiles\\{profile_id}'

	prefs = {
			'profile.default_content_settings.notifications':2,
			'profile.default_content_setting_values.notifications':2,
			'profile.contentSettings.notifications':2,
			'profile.content_settings.exceptions.notifications':2,
			'profile.managed_default_content_settings.notifications':2,
	}

	options = Options()
	options.add_argument(profiles_folder)
	#options.add_argument('profile-directory=Profile') #check if it works without this line
	#options.add_argument("--headless") #to run script in headless mode
	options.add_experimental_option('excludeSwitches', ['enable-logging']) #disables webdriver loggs
	options.add_experimental_option('prefs', prefs)

	driver = None
	try:
		driver = webdriver.Chrome(ChromeDriverManager().install(), options=options, service_log_path=os.path.devnull)
	except Exception:
		logger.error(f'{counter}. An error occured during driver creation.')
	else:
		time_to_sleep = config['SLEEP_BEFORE_PROFILE_DELETION']
		logger.info(f'{counter}. Deleting profile.')
		time.sleep(time_to_sleep)
		try:
			driver.close()
		except Exception:
			pass

		try:
			shutil.rmtree(f'{path_to_dir}\\profiles\\{profile_id}')
		except Exception:
			pass

	try:
		driver.quit()
	except Exception:
		kill_processes(driver)

def make_click(user_agent, profile_id, counter):
	path_to_dir = os.path.abspath(os.getcwd())
	profiles_folder = f'user-data-dir={path_to_dir}\\profiles\\{profile_id}'#\\Default'

	global proxies
	if not proxies:
		logger.error('Empty proxy list.')

	proxy = None
	while True:
		try:
			proxy = next(proxies)
			break
		except StopIteration:
			proxies = get_proxy(config['PROXY_URL'])
			logger.info('Geting now proxies.')
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
	except Exception:
		logger.error(f'{counter}. An error occured during driver creation.')
	else:
		logger.info(f'{counter}. Clicking.')
		start_time = time.time()

		number_of_clicks = random.randint(
					config['MIN_NUMBER_OF_CLICKS'], 
					config['MAX_NUMBER_OF_CLICKS']
		)
		while True:
			if time.time() - start_time < config['TIME_TO_WAIT_NOTIFICATION_FOR_CLICK']:
				if locate_notifiation('img//scr.png'):
					size = pyautogui.size()
					logger.info(f'{counter}. Clicking {number_of_clicks} times.')

					for _ in range(number_of_clicks):
						if locate_notifiation('img//scr.png'):
							pyautogui.click(x=(size[0] - 50), y=(size[1] - 60))
							time.sleep(config['TIME_TO_SLEEP_BETWEEN_NOTIFICATION_CLICK'])

					time.sleep(config['TIME_TO_SLEPP_AFTER_ALL_NOTIFICATION_CLICK'])
					break
			else:
				logger.debug(f'{counter}. There was no notification found in time.')	
				break

	try:
		driver.quit()
	except Exception:
		kill_processes(driver)

	delete_metrics(profile_id)

def dont_click(user_agent, profile_id, counter):
	path_to_dir = os.path.abspath(os.getcwd())
	profiles_folder = f'user-data-dir={path_to_dir}\\profiles\\{profile_id}'

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

	driver = None
	try:
		driver = webdriver.Chrome(ChromeDriverManager().install(), options=options, service_log_path=os.path.devnull)
	except Exception:
		logger.error(f'{counter}. An error occured during driver creation.')
	else:
		logger.info(f'{counter}. Ignoring.')
		start_time = time.time()
		while True:
			if time.time() - start_time < config['TIME_TO_WAIT_NOTIFICATION_FOR_IGNORE']:
				if locate_notifiation('img//scr.png'):
					break
			else:
				logger.debug(f'{counter}. There was no notification found in time.')	
				break

	time.sleep(config['SLEEP_BEFORE_PROCESS_KILL_FOR_IGNORE'])

	try:
		driver.quit()
	except Exception:
		kill_processes(driver)
		
	delete_metrics(profile_id)

def main():
	os.environ['WDM_LOG_LEVEL'] = '0'
	os.environ['WDM_PRINT_FIRST_LINE'] = 'False'

	pyautogui.FAILSAFE = False

	global config
	global proxies
	config = get_config('config_2.json')
	user_agent = get_user_agent('useragent.txt')
	proxies = get_proxy(config['PROXY_URL'])

	profile_id = 1
	counter = 1
	while True:
		profiles = get_profiles()
		if not profiles:
			logger.debug('There are not profiles in folder.')
			break
			
		for profile_id in profiles:
			if random.randint(0, 100) > config['PERCENT_TO_DELETE']: 
				if random.randint(0, 100) > config['PERCENT_TO_CLICK']: 
					dont_click(user_agent, profile_id, counter)
				else:
					make_click(user_agent, profile_id, counter)
			else:
				delete_profile(profiles[0], counter)
				profiles = get_profiles()

			counter += 1

if __name__ == '__main__':
	main()