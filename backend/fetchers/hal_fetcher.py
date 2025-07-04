import requests
import json
import xmltodict
from urllib.parse import urlparse

class HalFetcher:
    def __init__(self, query, year=2015):
        self.query = query
        self.year = year

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
    
    def fetch_data(self):
        base_url = "https://api.archives-ouvertes.fr/search"

        cursor_mark = "*"
        has_more = True

        all_results = []
        while has_more:
            # Define the query parameters
            params = {
                'q': self.query,
                'rows': 1000,
                'cursorMark': cursor_mark,
                'wt': 'json',
                'fq': f'submittedDateY_i:{self.year}',
                'sort': 'docid asc'  
            }
            response = requests.get(base_url, params=params)
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
                # 'source': id.split('/')[-2],
                'title': title,
                'type': type,
                'year': year
            })

        return normalize_data
    
    
if __name__ == "__main__":
    query = "(\"Laue Langevin\" AND docType_s:THESE)"
    hal_api = HalFetcher(query)
    data_archives_ouvertes = hal_api.fetch_data()
    normalized_hal_data = hal_api.normalize_data(data_archives_ouvertes)
    print(len(normalized_hal_data))