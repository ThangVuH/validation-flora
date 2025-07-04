import random
import os
import time
import pandas as pd
import glob
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC

def click_element(driver, by, value, timeout=20):
    """Helper function to click an element with a WebDriverWait."""
    element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
    element.click()

def get_most_recent_file(download_folder):
    # Look for Excel files (.xlsx or .xls)
    list_of_files = glob.glob(os.path.join(download_folder, "*.xls*"))
    if not list_of_files:
        return None
    latest_file = max(list_of_files, key=os.path.getctime)  # Get the most recently created file
    return latest_file

def rename_file(old_path, new_name, download_folder):
    file_extension = os.path.splitext(old_path)[1]
    new_file_path = os.path.join(download_folder, new_name + file_extension)
    if os.path.exists(new_file_path):
        raise FileExistsError(f"Target file {new_file_path} already exists.")
    os.rename(old_path, new_file_path)
    return new_file_path

# # Define the function to analyze the Excel file with Pandas
# def analyze_excel_file(file_path):
#     df = pd.read_excel(file_path)
#     columns = ['UT (Unique WOS ID)', 'DOI', 'Article Title', 'Publication Type', 
#                'Source Title', 'ISSN', 'Publication Year']
#     new_df = df[columns]
#     # Save the filtered DataFrame to a CSV file
#     csv_file_path = file_path.replace('.xls', '.csv')  # Replace .xls with .csv
#     new_df.to_csv(csv_file_path, index=False)  # `index=False` avoids saving the index as a column
#     print(f"Data saved to {csv_file_path }")

def analyze_excel_file(file_path):
    df = pd.read_excel(file_path)
    columns = {
        'UT (Unique WOS ID)': 'id',
        'DOI': 'doi',
        'Article Title': 'title',
        'Publication Type': 'type',
        'Source Title': 'source',
        'ISSN': 'issn',
        'Publication Year': 'year'
    }
    df = df[list(columns.keys())]  # Select only the required columns
    df.rename(columns=columns, inplace=True)  # Rename columns
    # Merge 'ISSN' and 'Source Title' into a single column called 'source'
    df['source'] = df.apply(lambda row: f"{row['issn']} | {row['source']}", axis=1)
    df.drop(columns=['issn'], inplace=True)
    # clean DOI
    df['doi'] = df['doi'].apply(clean_doi)
    # Save the updated DataFrame to a CSV file
    csv_file_path = file_path.replace('.xls', '.csv')  # Replace .xls with .csv
    df.to_csv(csv_file_path, index=False)  # `index=False` avoids saving the index
    print(f"Data saved to {csv_file_path}")

def clean_doi(doi):
        if pd.isna(doi):
            return None
        doi = doi.strip().lower()
        for prefix in ['https://doi.org/', 'http://doi.org/', 'doi.org/', 'doi:']:
            if doi.startswith(prefix):
                doi = doi.replace(prefix, '')
                break
        return doi

def clean_data(download_folder, config):
    wos_config = config["WoS"]
    # Verify download
    downloaded_file = get_most_recent_file(download_folder)
    if downloaded_file:
        print(f"File downloaded successfully: {downloaded_file}")

        for i, key in enumerate(config.keys()):
            if key == "WoS":
                file_name = f"{list(config.keys())[i]}_{config['WoS']['PUBLICATION_YEAR']}.xls"
                break  # Exit the loop once the condition is met
        file_path = os.path.join(download_folder, file_name)
        if downloaded_file != file_path:
            new_file_path = rename_file(downloaded_file, f"{list(config.keys())[-1]}_{wos_config['PUBLICATION_YEAR']}", download_folder)
        else:
            new_file_path = file_path


        # new_file_path = rename_file(downloaded_file, f"{list(config.keys())[-1]}_{wos_config['PUBLICATION_YEAR']}", download_folder)
        print(f"File renamed to: {new_file_path}")
        analyze_excel_file(new_file_path)
    else:
        raise FileNotFoundError("No Excel file found in the download folder.")

def scrape_web(download_folder, config):
    wos_config = config["WoS"]
    options = Options()
    options.set_preference("browser.download.folderList", 2)  # Use custom folder
    options.set_preference("browser.download.dir", download_folder)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    driver = webdriver.Firefox(options=options)

    try:
        # Access website using config URL
        driver.get(wos_config["URL"])
        time.sleep(random.randint(2, 6))

        # Manage cookies
        click_element(driver, By.ID, "onetrust-accept-btn-handler")
        time.sleep(random.randint(2, 6))

        # Search query using config values
        search_query = driver.find_element(By.ID, "advancedSearchInputArea")
        query_string = f"(ALL=({wos_config['PUBLICATION_YEAR']} {wos_config['query']})) OR (PY=({wos_config['PUBLICATION_YEAR']}) AND OG=({wos_config['ROR']}))"
        search_query.send_keys(query_string)
        time.sleep(random.randint(2, 6))

        click_element(driver, By.XPATH, "//button[@class='mat-focus-indicator search mat-flat-button mat-button-base mat-primary ng-star-inserted']")
        time.sleep(random.randint(2, 6))

        # Export options
        click_element(driver, By.XPATH, "//button[@class='mat-focus-indicator mat-menu-trigger margin-right-10--reversible new-wos-btn-style full-record-breadcrumbs-styles mat-stroked-button mat-button-base mat-primary']//span[@class='mat-button-wrapper']")
        time.sleep(random.randint(2, 6))

        click_element(driver, By.XPATH, "//button[@id='exportToExcelButton']")
        time.sleep(random.randint(2, 6))

        click_element(driver, By.XPATH, "//mat-radio-button[@id='radio3']//label[@class='mat-radio-label']")
        time.sleep(random.randint(2, 6))

        # Export and wait for download
        click_element(driver, By.XPATH, "//button[@id='exportButton']")
        time.sleep(10)  # Give extra time for download to start

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        driver.quit()
    
def load_config(config_path="config.json"):
    """Load configuration from a JSON file."""
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file '{config_path}' not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in '{config_path}'.")
    
def main(CONFIG_FILE):
    # Load configuration
    config = load_config(CONFIG_FILE)
    wos_config = config["WoS"]
    download_folder = wos_config["download_folder"]

    # scrape_web(download_folder, wos_config)
    clean_data(download_folder, config)

CONFIG_FILE = r"validation-flora\backend\config.json"
if __name__ == "__main__":
    main(CONFIG_FILE)