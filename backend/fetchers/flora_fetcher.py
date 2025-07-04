import requests
import json
import csv
import os
import xmltodict

CONFIG_FILE = r"validation-flora\backend\config.json"

import requests
import json
import xmltodict

class FloraFetcher:
    def __init__(self, config):
        self.config = config
        self.base_url = self.config['URL']
        self.params_query = self.config['parameters_query']
        self.params_record = self.config['parameters_record']
        self.session_id = None
        self.timeout= 50

    def login(self):
        USER = self.config['USER']
        PASSWORD = self.config['PASSWORD']
        login_url = f'{self.base_url}?method=login&code={USER}&password={PASSWORD}'
        response = requests.get(login_url)
        if response.ok:
            self.session_id = response.text.split('apiSession>')[1].split('</')[0]
            print(f"SESSION_ID: {self.session_id}")
            return self.session_id
        else:
            print("Login failed.")
            return None
    
    def logout(self):
        logout_url = f'{self.base_url}?method=logout&apiSession={self.session_id}'
        requests.get(logout_url)
        print("Logged out.")

    def run_query(self, url, params):
        # url = f"{self.base_url}?apiSession={self.session_id}"
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status() # Ensure we catch HTTP errors (e.g., 404, 500)
            xml_data = response.text
            json_data = json.dumps(xmltodict.parse(xml_data), indent=2)
            json_data = json.loads(json_data)
            return json_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
        
    def fetch_ids(self):
        self.params_query 
        try:
            url = f"{self.base_url}?apiSession={self.session_id}"
            data = self.run_query(url, self.params_query)
            ids = [item['@recordId'] for item in data['response']['digests']['digest']]
            return ids
        except requests.exceptions.RequestException as e:
            print(f"Error fetching IDs: {e}")
            return []
        
    def fetch_records_in_batches(self, record_ids):
        batch_size=200
        all_records = []
        for i in range(0, len(record_ids), batch_size):
            batch = record_ids[i:i + batch_size]
            record_id_params = "&".join([f"recordId={record_id}" for record_id in batch])
            self.session_id = self.login()
            url = f"{self.base_url}?apiSession={self.session_id}&{record_id_params}"
            try:
                data = self.run_query(url, self.params_record)
                all_records.append(data)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching batch {i // batch_size + 1}: {e}")
                return []
        return all_records

    def fetch_data(self):
        # Step 1: Fetch all IDs
        record_ids = self.fetch_ids()
        if not record_ids:
            print("No IDs fetched.")
            return {}
        
        # Step 2: Fetch detailed records
        records = self.fetch_records_in_batches(record_ids)
        return records

    def clean_doi(self,doi):
        if doi is None:
            return None
        doi = doi.strip().lower()
        for prefix in ['https://doi.org/', 'http://doi.org/', 'doi.org/', 'doi:']:
            if doi.startswith(prefix):
                doi = doi.replace(prefix, '')
                break
        return doi
    
    def normalize_data(self, data):
        normalize_data = []
        for item in data:
            infos = item['response']['records']['record']
            for info in infos:
                # id here
                if info.get('DIGEST_NUMBER') == None:
                    id = info.get('@id')
                else:
                    id = info.get('DIGEST_NUMBER')

                # doi here
                if info.get('CHAMP3') == None:
                    doi = None
                else:
                    doi = info.get('CHAMP3')

                # title here
                if info.get('DIGEST_TITLE') == None:
                    title = None
                else:
                    title = info.get('DIGEST_TITLE')

                # journal title
                if info.get('DIGEST_JRNAL_TITLE') == None:
                    source = None
                else:
                    source = info.get('DIGEST_JRNAL_TITLE')

                # publish year here
                if info.get('DIGEST_YEAR') == None:
                    year = None
                else:
                    year = info.get('DIGEST_YEAR')

                normalize_data.append({
                    'id':id,
                    'doi': self.clean_doi(doi),
                    'title': title,
                    'source': source,
                    'year': year
                })
        return normalize_data
    
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
    config = load_config(CONFIG_FILE)
    
    flora_api = FloraFetcher(config['Flora'])
    flora_api.login()
    flora_data = flora_api.fetch_data()
    data = flora_api.normalize_data(flora_data)
    print(f"Fetched Flora records: {len(flora_data)}")
    # print(flora_data)
    print(len(data))
    flora_api.logout()

    # save as csv file
    download_folder = config['Flora']["download_folder"]
    for i, key in enumerate(config.keys()):
        if key == "Flora":
            file_name = f"{list(config.keys())[i]}_{config['Flora']['PUBLICATION_YEAR']}.csv"
            break  # Exit the loop once the condition is met
    new_file_path = os.path.join(download_folder, file_name)
    generate_csv_file(new_file_path, data)
    

if __name__ == "__main__":
    CONFIG_FILE = r"validation-flora\backend\config.json"
    main(CONFIG_FILE)

    