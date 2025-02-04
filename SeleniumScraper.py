#INSTALLATION GUIDE:
#https://www.youtube.com/watch?v=Xjv1sY630Uc

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

# FOR TESTING

# path to your executable
PATH = r"C:\Program Files\chromedriver-win64\chromedriver.exe"

service = Service(executable_path=PATH)

driver = webdriver.Chrome(service=service)

# test_url = "https://youtube.com"

# driver.get(test_url)

# time.sleep(2)

# driver.quit()

#For scraping station IDs

station_id = []

URL = "https://tidesandcurrents.noaa.gov/stations.html?type=Water+Levels"

driver.get(URL)

wait = WebDriverWait(driver, 10)

a_elements = wait.until(
    EC.presence_of_all_elements_located((By.XPATH, '//a[@style="color: #015FA9;"]'))
)

for element in a_elements:
    # regex for extracting 7-digit station id
    match = re.search(r'waterlevels\.html\?id=(\d{7})', element.get_attribute('href'))
    if match:
        station_id.append(match.group(1))

print(len(station_id)) #test if correctly collected
print(station_id[0])

driver.quit()