from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Configure Chrome driver options for headless mode
options = Options()
options.add_argument("--headless=new")  # Use the new headless mode (more stable for some versions)
options.add_argument("--window-size=1920,1080")  # Set a default window size
options.add_argument("--disable-extensions")  # Disable extensions
options.add_argument("--disable-popup-blocking")  # Disable popup blocking
options.add_argument("--start-maximized")  # Simulate a maximized screen
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
    logging.info("Website loaded successfully.")

    # Search for IT jobs
    logging.info("Searching for IT jobs...")
    search_box = driver.find_element(By.ID, "keywords-input")
    search_box.send_keys("IT")
    search_box.send_keys(Keys.RETURN)

    # Wait for search results
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article[data-automation='normalJob']")))
    logging.info("Job search results loaded successfully.")

    # Scrape job postings from 10 pages
    for page_num in range(1, 11):
        logging.info(f"Scraping page {page_num}...")

        # Find job cards on the current page
        job_cards = driver.find_elements(By.CSS_SELECTOR, "article[data-automation='normalJob']")
        logging.info(f"Found {len(job_cards)} job postings on this page.")
        for card in job_cards:
            job_details = extract_job_details(card)
            job_list.append(job_details)

        if page_num < 10:
            try:
                # Find the "Next" button and ensure it is clickable
                next_button = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Next']"))
                )
                # Scroll to the next button to make sure it's in view
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                next_button.click()
                logging.info(f"Clicked on the 'Next' button for page {page_num + 1}. Waiting for the next page to load...")
                
                # Wait for the new job cards to load
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article[data-automation='normalJob']"))
                )
                logging.info(f"Page {page_num + 1} loaded successfully.")
            except TimeoutException:
                logging.error(f"Timeout occurred while waiting for the 'Next' button on page {page_num}.")
                break
        else:
            logging.info("Reached 10 pages. Exiting pagination loop.")
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
    logging.info("Browser closed.")
