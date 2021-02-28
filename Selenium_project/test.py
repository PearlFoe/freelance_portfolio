from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver

from urllib.parse import urljoin

import time
import os


url = 'https://bezkolejki.eu/luw-gorzow/'

sections = '''	
1 - Przyjmowanie wnioskow o pobyt w Polsce
2 - Sprawy cudzoziemcow- stemple i odciski palcow
3 - Odbior kart pobytu
4 - Sprawy dotyczace obywatelstwa polskiego
5 - Przyjmowanie wnioskow o paszport, wnioskow ob. UE, zaproszen
6 - Odbior paszportu, dokumentow ob. UE, zaproszen
'''

def scroll_to_bottom(driver):
	try:
		driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
	except Exception:
		pass

def choose_section(driver, section):
	actions = ActionChains(driver)

	_ = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'Operacja0')))
	section = driver.find_elements_by_xpath('//*[@class="mb-2 col-lg-8 offset-lg-2 col-12"]/button')[section]
	
	actions.move_to_element(section).perform()
	actions.click(section).perform()

	scroll_to_bottom(driver)

	confirm_btn = driver.find_element_by_xpath('//button[@class="btn footer-btn btn-secondary btn-lg btn-block"]')
	actions.move_to_element(confirm_btn).perform()
	actions.click(confirm_btn).perform()

def choose_time(driver):
	actions = ActionChains(driver)

	_ = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//div[@class="vc-w-full vc-relative"]')))
	scroll_to_bottom(driver)
	for i in range(2):
		try:
			date = driver.find_elements_by_xpath('//*[@class="vc-day-content vc-focusable vc-font-medium vc-text-sm vc-cursor-pointer focus:vc-font-bold vc-rounded-full"]')[0]
			break
		except Exception:
			if i == 1:
				return False
			btn = driver.find_elements_by_xpath('//*[@class="vc-arrows-container title-center"]/div')[-1]
			actions.move_to_element(btn).perform()
			actions.click(btn).perform()
	
	actions.move_to_element(date).perform()
	actions.click(date).perform()

	time = Select(driver.find_element_by_xpath('//select[@id="selectTime"]'))
	actions.pause(0.5)
	time.select_by_index(0)

	confirm_btn = driver.find_element_by_xpath('//div[@class="col-lg-2 offset-lg-10 col-12"]/button')
	actions.click(confirm_btn).perform()

	return True

def input_personal_data(driver, data):
	actions = ActionChains(driver)

	_ = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//div[@class="col-12"]/div/div')))
	scroll_to_bottom(driver)

	elements = driver.find_elements_by_xpath('//div[@class="col-12"]/div')
	for i in range(len(elements)):
		element = elements[i].find_element_by_tag_name('input')
		actions.click(element).perform()
		element.send_keys(data[i])

	confirm_btn = driver.find_element_by_xpath('//button[@class="btn footer-btn btn-secondary btn-lg btn-block"]')
	#actions.move_to_element(confirm_btn).perform()
	actions.click(confirm_btn).perform()

def final_confirm(driver, data):
	actions = ActionChains(driver)

	_ = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
												(By.XPATH, '//div[@class="custom-control custom-checkbox custom-control-inline"]')))
	scroll_to_bottom(driver)

	pre_confirm_btn = driver.find_element_by_xpath('//input[@id="__BVID__89"]')
	#actions.move_to_element(pre_confirm_btn).perform()
	actions.click(pre_confirm_btn).perform()

	confirm_btn = driver.find_element_by_xpath('//button[@class="btn footer-btn btn-secondary btn-lg btn-block"]')
	actions.move_to_element(confirm_btn).perform()
	actions.click(confirm_btn).perform()

	_ = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
												(By.XPATH, '//div[@class="col-md-8 col-lg-6 offset-md-2 offset-lg-3 col-12"]')))

	time.sleep(5)

	driver.save_screenshot(f'{data[0]} {data[1]}.png')

def main():
	data = []
	section = None
	flag = 0
	timeout = None

	while not flag:
		print('Введите номер операции:\n' + sections)
		section = int(input('Операция: '))

		timeout = float(input('Введите время дозвона к сайту(сек): '))

		first_name = input('Ведите имя: ')
		data.append(first_name)

		second_name = input('Введите фамилию: ')
		data.append(second_name)

		email = input('Введите email: ')
		data.append(email)

		print('\nВведенные данные:\n'+
				f'Номер операции: {section}\n'+
				f'Время дозвона: {timeout}\n'+
				f'Имя: {first_name}\n'+
				f'Фамилия: {second_name}\n'+
				f'Email: {email}\n')

		while True:
		    flag = input('Данные верны? (0 - нет/1 - да): ')
		    if not flag.isdigit():
		        print("Вы ввели не число. Попробуйте снова: ")
		    elif not 0 <= int(flag) <= 2:
		        print("Ваше число не диапазоне. Попробуйте снова")
		    else:
		        break

		if int(flag) == 1:
			break

		flag = 0
		
	options = webdriver.ChromeOptions()
	options.add_argument('headless')
	options.add_argument("window-size=1200,1080")
	driver = webdriver.Chrome(chrome_options=options)
	actions = ActionChains(driver)

	while True:
		driver.get(url)
		choose_section(driver=driver, section=section - 1)

		if not choose_time(driver=driver):
			time.sleep(timeout)
			continue
		else:
			try:
				input_personal_data(driver=driver, data=data)
				final_confirm(driver=driver, data=data)
				break
			except Exception:
				continue
		
	a = input('\n----Press Enter to exit----\n')
	driver.close()


if __name__ == "__main__":
	main()	
