import requests
import threading
import json
import csv
import os
from urllib.parse import urlparse

class OpenAlexFetcher:
    def __init__(self, config):
        self.config = config
        self.base_url = self.config["URL"]
        self.year = self.config["PUBLICATION_YEAR"]
        self.institution_id = self.config["ROR"]

    def fetch_single_query(self, params, results, lock):
        """
        Fetch data for a single query with cursor pagination.
        """
        cursor = "*"
        while cursor:
            params["cursor"] = cursor
            response = requests.get(self.base_url, params=params)
            if response.status_code != 200:
                print(f"Failed to fetch data for {params}")
                return
            data = response.json()
            this_page_results = data.get("results", [])
            lock.acquire()  # Ensure thread-safe appending to the shared list
            results.extend(this_page_results)
            lock.release()
            cursor = data["meta"].get("next_cursor")

    def fetch_data_multithreaded(self, queries):
        """
        Fetch data for multiple queries using multithreading.
        queries: List of parameter dictionaries for each query.
        """
        threads = []
        results = []
        lock = threading.Lock()  # Lock to manage shared resource (results list)
        # Create and start a thread for each query
        for params in queries:
            thread = threading.Thread(target=self.fetch_single_query, args=(params, results, lock))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        print(f"Total results: {len(results)}")
        return results
    
    # def fetch_data(self):
    #     base_url = "https://api.openalex.org/works"
    #     params = {
    #     # "filter": f"authorships.institutions.lineage:{institution_id},publication_year:{year}",
    #     "filter": f"institutions.ror:{self.institution_id},publication_year:{self.year}",
    #     "per-page": 100  
    #     }
    #     cursor = "*"
    #     all_results = []
    #     while cursor:
    #         params["cursor"] = cursor
    #         response = requests.get(base_url, params=params)
    #         if response.status_code != 200:
    #             return "Failed to fetch data", response.status_code
    #         data = response.json()
    #         this_page_results = data['results']
    #         all_results.extend(this_page_results)
    #         cursor = data["meta"]["next_cursor"]
    #     print(f"Total results OpenAlex: {len(all_results)}")
    #     return all_results

    def clean_doi(self, doi):
        if doi is None:
            return None
        doi = doi.strip().lower()
        for prefix in ['https://doi.org/', 'http://doi.org/', 'doi.org/', 'doi:']:
            if doi.startswith(prefix):
                doi = doi.replace(prefix, '')
                break
        return doi
    
    def normalize_data(self, data):
        return [
            {
                'id': f"{urlparse(item.get('id')).netloc}{urlparse(item.get('id')).path}",
                'doi': self.clean_doi(f"{urlparse(item.get('doi')).netloc}{urlparse(item.get('doi')).path}")if item.get('doi') else None,
                'title': item.get('title'),
                'type': item.get('type'),
                'source': f"{item['primary_location']['source']['issn_l']} | {item['primary_location']['source']['display_name']}" if item['primary_location'] and item['primary_location']['source'] else None,
                'year': item.get('publication_year')
            }
            for item in data
        ]
    

def load_config(config_path="config.json"):
    """Load configuration from a JSON file."""
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file '{config_path}' not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in '{config_path}'.")
    
def generate_csv_file(file_name, data):
    if not data:
        raise ValueError("The data list is empty. Cannot generate CSV file.")
    try:
        with open(file_name, mode='w', newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(data[0].keys())  # Write header
            for item in data:
                writer.writerow(item.values())  # Write rows
        print(f"File '{file_name}' has been created successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    CONFIG_FILE = r"validation-flora\backend\config.json"
    config = load_config(CONFIG_FILE)
    queries = [
        {"filter": f"institutions.ror:{config['OpenAlex']['ROR']},publication_year:{config['OpenAlex']['PUBLICATION_YEAR']}", "per-page": config['OpenAlex']["PER_PAGE"]},
        {"filter": f"authorships.institutions.lineage:!{config['OpenAlex']['INSTITUTION_ID']},publication_year:{config['OpenAlex']['PUBLICATION_YEAR']},default.search:{config['OpenAlex']['query']}", "per-page": config['OpenAlex']["PER_PAGE"]}
        ]
    
    openalex_api = OpenAlexFetcher(config['OpenAlex'])
    all_results = openalex_api.fetch_data_multithreaded(queries)
    data = openalex_api.normalize_data(all_results)

    # save as csv file
    download_folder = config['OpenAlex']["download_folder"]
    for i, key in enumerate(config.keys()):
        if key == "OpenAlex":
            file_name = f"{list(config.keys())[i]}_{config['OpenAlex']['PUBLICATION_YEAR']}.csv"
            break  # Exit the loop once the condition is met
    new_file_path = os.path.join(download_folder, file_name)
    generate_csv_file(new_file_path, data)