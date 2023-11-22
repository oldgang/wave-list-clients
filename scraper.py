import threading
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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

# find the gps coordinates of the service
def find_service_gps(id, url):
    driver = open_url(url)
    location = driver.find_element(By.XPATH, f"//div/a[@name='{id}']/preceding::span[@class='edytowalny-text-gps']").text
    lat, lon = location.split(',')
    height = '10' # arbitrary value of 10 meters
    return (lon, lat, height)

# find the gps coordinates of the access point
def find_AP_gps(ip):
    octets = ip.split('.')
    id = f"{octets[1]}-{octets[2]}"
    url = f"https://panel.wave.com.pl/?co=alias&alias={id}"
    driver = open_url(url)
    locationSpan = driver.find_element(By.CLASS_NAME, "edytowalny-text-gps")
    location = locationSpan.find_element(By.TAG_NAME, "a").text
    height = driver.find_element(By.CLASS_NAME, "edytowalny-text-wysokosc").text
    lat, lon = location.split(',')
    if height in ('', '0'):
        height = '15' # arbitrary value of 15 meters
    return (lon, lat, height)

# for testing purposes
if __name__ == "__main__":
    print(find_AP_gps('10.1.54.21'))