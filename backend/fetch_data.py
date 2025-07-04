from fetchers.base_fetcher import HalAPI, OpenAlexAPI, FloraAPI
from contextlib import contextmanager
from models import FloraPublication, Publication
from database import SessionLocal


@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def bulk_insert(session, data: list):
    session.bulk_save_objects(data)
    session.commit()

def get_existing_ids(session, model_class):
    existing_ids = session.query(model_class.id).all()
    return {id[0] for id in existing_ids}

def fetch_and_store_data(model_class, fetcher, normalize_func=None):
    """
    Generic function to fetch and store data
    
    Args:
        model_class: SQLAlchemy model class to store data in
        fetcher: Fetcher instance or object with fetch_data method
        normalize_func: Function to normalize data (if None, uses fetcher.normalize_data)
    """
    # Fetch data
    data = fetcher.fetch_data()
    # Normalize data
    if normalize_func:
        normalized_data = normalize_func(data)
    else:
        normalized_data = fetcher.normalize_data(data)
    
    print(f"Total records from {fetcher.__class__.__name__}: {len(normalized_data)}")

    if normalized_data:
        with get_db_session() as session:
            existing_ids = get_existing_ids(session, model_class)
            new_data = [record for record in normalized_data if record['id'] not in existing_ids]
            
            if new_data:
                # Convert dictionaries to SQLAlchemy model instances
                model_instances = [model_class(**record) for record in new_data]
                
                # Store only new data in the database
                bulk_insert(session, model_instances)
                print(f"New data stored successfully! Added {len(new_data)} records to {model_class.__tablename__}")
            else:
                print("No new data to store.")
    else:
        print("No data fetched.")

    # Cleanup if the fetcher has a logout method
    if hasattr(fetcher, 'logout') and callable(fetcher.logout):
        fetcher.logout()
        
    return normalized_data

def fetch_combined_publications(config):
    openalex_fetcher = OpenAlexAPI(config["OpenAlex"])
    openalex_data = fetch_and_store_data(Publication, openalex_fetcher)

    # Fetch and normalize data from Archives Ouvertes
    hal_fetcher = HalAPI(config["HAL"])
    hal_data = fetch_and_store_data(Publication, hal_fetcher)

    return len(openalex_data) + len(hal_data)

def fetch_flora_publications(config):
    flora_fetcher = FloraAPI(config['Flora'])
    flora_fetcher.login()
    flora_data = fetch_and_store_data(FloraPublication, flora_fetcher)
    # flora_fetcher.logout()
    return len(flora_data)

import json
CONFIG_FILE = r"validation-flora\backend\config.json"
if __name__ == "__main__":
    # Example usage
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    # Test fetching Flora data
    # fetch_flora_publications(config)

    fetch_combined_publications(config)
