import requests
from urllib.parse import urlparse
import json
import xmltodict

class LibraryAPI:
    def __init__(self, config):
        self.config = config
        self.base_url = self.config['URL']

    def fetch_data(self):
        """Placeholder for fetch data; should be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method.")
    
    def normalize_data(self, data):
        """Placeholder for normalizing data; should be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method.")
    
    def run_query(self, url, params, timeout=50):
        """Send a GET request to the provided URL with the given parameters."""
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()  # Raise an exception for HTTP errors
            xml_data = response.text
            json_data = json.dumps(xmltodict.parse(xml_data), indent=2)
            json_data = json.loads(json_data)
            return json_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
        
    def clean_doi(self, doi):
        """Normalize DOIs by stripping prefixes and standardizing format."""
        if doi is None:
            return None
        doi = doi.strip().lower()
        for prefix in ['https://doi.org/', 'http://doi.org/', 'doi.org/', 'doi:']:
            if doi.startswith(prefix):
                doi = doi.replace(prefix, '')
                break
        return doi
    

class FloraAPI(LibraryAPI):
    def __init__(self, config):
        super().__init__(config)
        self.params_query = self.config['parameters_query']
        self.params_record = self.config['parameters_record']
        self.session_id = None
        self.batch_size = 200

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
        if self.session_id:
            logout_url = f'{self.base_url}?method=logout&apiSession={self.session_id}'
            requests.get(logout_url)
            print("Logged out.")
        else:
            print("No session to log out.")

    def fetch_data(self):
        # Ensure we are logged in before fetching data
        if not self.session_id:
            self.session_id = self.login()
            if not self.session_id:
                print("Unable to login, aborting fetch_data.")
                return {}
        # Step 1: Fetch all IDs
        record_ids = self.fetch_ids()
        if not record_ids:
            print("No IDs fetched.")
            return {}
        print(f"Total results from Flora: {len(record_ids)}")
        
        # Step 2: Fetch detailed records
        records = self.fetch_records_in_batches(record_ids)
        return records
    
    def fetch_ids(self):
        try:
            url = f"{self.base_url}?apiSession={self.session_id}"
            data = self.run_query(url, self.params_query)
            ids = [item['@recordId'] for item in data['response']['digests']['digest']]
            return ids
        except requests.exceptions.RequestException as e:
            print(f"Error fetching IDs: {e}")
            return []
    
    def fetch_records_in_batches(self, record_ids):
        batch_size= self.batch_size
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
            except Exception as e:
                print(f"Unexpected error fetching batch {i // batch_size + 1}: {e}")
                # return []
        return all_records
    
    def normalize_data(self, data):
        normalize_data = []
        for item in data:
            infos = item['response']['records']['record']
            for info in infos:
                # id here
                id = info.get('@id')

                # doi here
                doi = info.get('CHAMP3')

                # title here
                title = info.get('DIGEST_TITLE')

                # journal title
                source = info.get('DIGEST_JRNAL_TITLE')

                # publish year here
                year = info.get('DIGEST_YEAR')

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
    

class OpenAlexAPI(LibraryAPI):
    def __init__(self, config):
        super().__init__(config)
        self.institution_id = self.config['ROR']
        self.year = self.config['PUBLICATION_YEAR']
        self.per_page = self.config['PER_PAGE']

    def fetch_data(self):
        params = {
        # "filter": f"authorships.institutions.lineage:{institution_id},publication_year:{year}",
        "filter": f"institutions.ror:{self.institution_id},publication_year:{self.year}",
        "per-page": self.per_page  
        }
        cursor = "*"
        all_results = []
        while cursor:
            params["cursor"] = cursor
            response = requests.get(self.base_url, params=params)
            if response.status_code != 200:
                return "Failed to fetch data", response.status_code
            data = response.json()
            this_page_results = data['results']
            all_results.extend(this_page_results)
            cursor = data["meta"]["next_cursor"]
        print(f"Total results OpenAlex: {len(all_results)}")
        return all_results
    
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

class HalAPI(LibraryAPI):
    def __init__(self, config):
        super().__init__(config)
        self.query = self.config['query']
        self.year = self.config['PUBLICATION_YEAR']
        self.rows = self.config['row']
        self.wt = self.config['write_type']
        self.sort = self.config['sort']

    def fetch_data(self):    
        cursor_mark = "*"
        has_more = True

        all_results = []
        while has_more:
            params = {
                'q': self.query,
                'rows': self.rows,
                'cursorMark': cursor_mark,
                'wt': self.wt,
                'fq': f'submittedDateY_i:{self.year}',
                'sort': self.sort 
            }
            response = requests.get(self.base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                for doc in data['response']['docs']:
                    doc['metadata_url'] = doc['uri_s'] + '/metadata'
                    xml_data = requests.get(doc['metadata_url'])
                    json_data = json.loads(json.dumps(xmltodict.parse(xml_data.content), indent=2))

                    all_results.append(json_data)


                next_cursor_mark = data['nextCursorMark']
                if cursor_mark == next_cursor_mark:
                    has_more = False
                else:
                    cursor_mark = next_cursor_mark
        print(f"Total results from Archives Ouvertes: {data['response']['numFound']}")
        return all_results
    
    def normalize_data(self, data):
        id_keys = ['TEI', 'text', 'body', 'listBibl', 'biblFull', 'publicationStmt', 'idno']
        title_keys = ['TEI', 'text', 'body', 'listBibl', 'biblFull', 'titleStmt', 'title']
        type_keys = ['TEI', 'text', 'body', 'listBibl', 'biblFull', 'profileDesc', 'textClass', 'classCode']
        date_keys = ['TEI', 'text', 'body', 'listBibl', 'biblFull', 'editionStmt', 'edition', 'date']

        normalize_data = []
        for info in data:
            # id here
            id_data = self.get_nested_value(info, id_keys, default="No id")
            for entry in id_data:
                if entry.get('@type') == 'halUri':
                    id = entry.get('#text')
            
            # title here
            title_data = self.get_nested_value(info, title_keys, default={})
            if isinstance(title_data, list):
                title = title_data[0].get('#text', "No Title")
            elif isinstance(title_data, dict):
                title = title_data.get('#text', "No Title")
            else:
                title = "No Title"

            # docType here
            type_data = self.get_nested_value(info, type_keys, default="No type")
            for entry in type_data:
                if entry.get('@scheme') == 'halTypology':
                    type = entry.get('#text')

            # publish year here
            date_data = self.get_nested_value(info, date_keys, default=[])
            year = "No year"
            for entry in date_data:
                if entry.get('@type') == 'whenReleased':
                    year = entry.get('#text').split('-')[0]  # Extract the year part
                    break
            
            normalize_data.append({
                'id': f"{urlparse(id).netloc}{urlparse(id).path}",
                'title': title,
                'type': type,
                'source': id.split('/')[-2],
                'year': year
            })

        return normalize_data
    
    @staticmethod
    def get_nested_value(d, keys, default=None):
        for key in keys:
            if isinstance(d, dict):
                d = d.get(key, default)
            elif isinstance(d, list) and isinstance(key, int) and key < len(d):
                d = d[key]
            else:
                print(f"Key '{key}' not found in: {d}")
                return default
        return d
    


CONFIG_FILE = r"validation-flora\backend\config.json"
if __name__ == "__main__":
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        
    try:
#         # Hal api
#         hal_api = HalAPI(config["HAL"])
#         data_archives_ouvertes = hal_api.fetch_data()
#         normalized_hal_data = hal_api.normalize_data(data_archives_ouvertes)

        # OpenAlex api
        openalex_api = OpenAlexAPI(config["OpenAlex"])
        data_openalex = openalex_api.fetch_data()
        normalized_openalex_data = openalex_api.normalize_data(data_openalex)
        for i in normalized_openalex_data:
            print(i['id'], i['doi'])

        # # Flora api
        # flora_api = FloraAPI(config['Flora'])
        # flora_api.login()
        # flora_data = flora_api.fetch_data()
        # normalized_flora_data = flora_api.normalize_data(flora_data)
        # flora_api.logout()
        # for i in normalized_flora_data:
        #     print(i['id'], i['doi'])
# 
    except Exception as e:
        print("An error occurred:", e)
