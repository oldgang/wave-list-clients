import threading
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# webdriver init
def driverInit():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("--log-level=3")
    chrome_prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", chrome_prefs)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.implicitly_wait(5)
    return driver

# login to site
def login(driver):
    with open('.venv/password.txt', 'r') as f:
        password = f.readline().strip()
    try:
        driver.get("https://panel.wave.com.pl/?co=logowanie&redirect=%2F") # login page url
    except WebDriverException:
        print("Page down")
        exit()
    elem = driver.find_element(By.NAME, "pass")
    elem.clear()
    elem.send_keys(password + Keys.RETURN) # password 
    return driver

# open the provided url
def open_url(url):
    driver = driverInit()
    driver = login(driver)
    driver.get(url)
    return driver

def find_service_gps(id, url):
    driver = open_url(url)
    # find the service id on site (it's located inside of an <a> element)
    location = driver.find_element(By.XPATH, f"//div/a[@name='{id}']/preceding::span[@class='edytowalny-text-gps']")
    return location.text