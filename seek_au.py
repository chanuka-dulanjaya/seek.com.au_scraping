from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Chrome driver options (headless mode for efficiency)
options = Options()
options.headless = True
driver = webdriver.Chrome(options=options)

# Initialize data storage
job_list = []

# Define a function to extract job details
def extract_job_details(card):
    try:
        job_title = card.find_element(By.CSS_SELECTOR, "h3 a").text
    except NoSuchElementException:
        job_title = "N/A"
    try:
        company_name = card.find_element(By.CSS_SELECTOR, "a[data-automation='jobCompany']").text
    except NoSuchElementException:
        company_name = "N/A"
    try:
        location = card.find_element(By.CSS_SELECTOR, "span[data-automation='jobCardLocation']").text
    except NoSuchElementException:
        location = "N/A"
    try:
        job_link = card.find_element(By.CSS_SELECTOR, "h3 a").get_attribute("href")
    except NoSuchElementException:
        job_link = "N/A"
    return {
        "Job Title": job_title,
        "Company Name": company_name,
        "Location": location,
        "Job Link": job_link
    }

try:
    # Open Seek.com.au
    logging.info("Opening Seek.com.au...")
    driver.get("https://www.seek.com.au/")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "keywords-input")))

    # Search for IT jobs
    search_box = driver.find_element(By.ID, "keywords-input")
    search_box.send_keys("IT")
    search_box.send_keys(Keys.RETURN)

    # Wait for search results
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article[data-automation='normalJob']")))

    # Scrape job postings
    while True:
        # Find job cards
        job_cards = driver.find_elements(By.CSS_SELECTOR, "article[data-automation='normalJob']")
        for card in job_cards:
            job_details = extract_job_details(card)
            job_list.append(job_details)

        # Navigate to the next page
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "a[data-automation='page-next']")
            if "aria-disabled" in next_button.get_attribute("outerHTML"):
                logging.info("Reached the last page.")
                break
            next_button.click()
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article[data-automation='normalJob']")))
        except NoSuchElementException:
            logging.info("No more pages available.")
            break

except TimeoutException as e:
    logging.error(f"Timeout occurred: {e}")
except Exception as e:
    logging.error(f"Unexpected error occurred: {e}")
finally:
    # Save data to a CSV file
    df = pd.DataFrame(job_list)
    df.to_csv("seek_jobs.csv", index=False)
    logging.info("Job data saved to seek_jobs.csv")

    # Close the browser
    driver.quit()
