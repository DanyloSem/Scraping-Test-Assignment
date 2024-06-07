import time
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from config import PROXY, INTERVAL


logging.basicConfig(
    filename='scraper.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_driver(proxy=None):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=chrome_options
    )
    return driver

def wait_for_element(driver, by, value, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )

def scroll_to(driver, element):
    driver.execute_script(
        "window.scrollTo(0, arguments[0]);", 
        element.location['y'] - 50
    )
    time.sleep(2)

def scrape_data(driver):
    url = "https://defillama.com/chains"
    driver.get(url)
    
    table_xpath = "//span[text()='Name']/../../../../../div[2]"
    table = wait_for_element(driver, By.XPATH, table_xpath)
    
    data = []
    last_count = -1

    while len(data) > last_count:
        last_count = len(data)
        chains = table.find_elements(By.XPATH, "./div")
        for chain in chains:
            name = wait_for_element(chain, By.XPATH, "./div/span/a").text
            if not any(d["Name"] == name for d in data):
                protocols = chain.find_element(By.XPATH, "./div[2]").text
                tvl = chain.find_element(By.XPATH, "./div[7]").text
                data.append({
                    "Name": name,
                    "Protocols": protocols,
                    "TVL": tvl
                })
        scroll_to(driver, chains[-1])
    return data

def save_data(data):
    df = pd.DataFrame(data)
    df.to_csv('defillama_data.csv', index=False)

def main(proxy=None, interval=300):
    driver = setup_driver(proxy)
    try:
        while True:
            data = scrape_data(driver)
            save_data(data)
            logging.info("Scraping successful, data saved.")
            time.sleep(interval)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    proxy = PROXY
    interval = INTERVAL * 60
    
    main(proxy, interval)