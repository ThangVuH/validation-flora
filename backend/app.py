from flask import Flask, request, jsonify
from flask_cors import CORS
from models import Base, Publication, FloraPublication
from database import engine, SessionLocal
from fetch_data import fetch_flora_publications, fetch_combined_publications, get_db_session
import json

CONFIG_FILE = r"validation-flora\backend\config.json"

app = Flask(__name__)
CORS(app) 

# Create all tables (if they don't already exist)
Base.metadata.create_all(bind=engine)

@app.route('/')
def home():
    return "<h1>Bibliometric data</h1><p>Data is being fetched and stored.</p>"

@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    """
    Endpoint to trigger data fetching and storing.
    """
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    try:
        source = request.args.get('source', 'all')
        result = {'message': 'Data fetch initiated successfully', 'details': []}

        if source == 'flora' or source == 'all':
                # Fetch Flora data
                fetch_flora_publications(config)
                result['details'].append('Flora data fetched successfully')
        if source == 'openalex' or source == 'all':
                # Fetch OpenAlex and HAL data
                fetch_combined_publications(config)
                result['details'].append('OpenAlex and HAL data fetched successfully')

        return jsonify(result)
    except Exception as e:
        # Log the error for server-side debugging
        app.logger.error(f"Error during data fetch: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/publications', methods=['GET'])
def get_publications():
    """
    API endpoint to retrieve publication data.
    You can pass a query parameter `source` with value 'openalex' or 'flora' to filter by source.
    If not provided, you can return both combined or just one source.
    """
    session = SessionLocal()
    try:
        source = request.args.get('source', 'openalex')
        if source == 'openalex':
            pubs = (session.query(Publication)
            .order_by(Publication.year, Publication.id)
            .all())
        elif source == 'flora':
            pubs = session.query(FloraPublication).all()
        else:
            # Optionally combine both (here we simply return OpenAlex publications)
            pubs = (session.query(Publication)
                    .order_by(Publication.year, Publication.id)
                    .all())
        
        # Convert ORM objects to dictionaries
        result = []
        for pub in pubs:
            result.append({
                'id': pub.id,
                'title': pub.title,
                'doi': pub.doi,
                'type': pub.type,
                'source':pub.source,
                'year': pub.year,
                'isValid': pub.isValid,
                'comment': pub.comment
            })
        return jsonify(result)
    finally:
        session.close()
    
@app.route('/api/publications/<path:pub_id>/validate', methods=['PUT'])
def update_publication_validation(pub_id):
    with get_db_session() as session:
        data = request.json
        pub = session.query(Publication).filter(Publication.id == pub_id).first()

        if not pub:
            app.logger.warning(f"Publication not found: {pub_id}")
            return jsonify({'error': 'Publication not found', 'id': pub_id}), 404
        
        # Update isValid, converting to boolean to ensure correct type
        if 'isValid' in data:
            pub.isValid = bool(data.get('isValid', False))
        if 'comment' in data:
            pub.comment = str(data.get('comment', ''))

        return jsonify({
            'success': True, 
            'isValid': pub.isValid,
            'id': pub.id
        })

from fuzzywuzzy import fuzz
from sqlalchemy import func    
@app.route('/api/publications/match', methods=['GET'])
def match_publications():
    session = SessionLocal()
    try:
        # Matching configuration parameters
        title_threshold = float(request.args.get('title_threshold', 0.8))
        match_strategy = request.args.get('strategy', 'comprehensive')

        # Fetch Flora publications
        flora_pubs = session.query(FloraPublication).all()

        matches = []
        for flora_pub in flora_pubs:
            # Find matching publications in OpenAlex
            matching_candidates = find_publication_matches(
                session, 
                flora_pub, 
                title_threshold=title_threshold,
                strategy=match_strategy
            )
            matches.append({
                'flora_publication': {
                    'id': flora_pub.id,
                    'title': flora_pub.title,
                    'doi': flora_pub.doi,
                    'source': flora_pub.source,
                    'year': flora_pub.year
                },
                'matching_candidates': matching_candidates
            })
        
        return jsonify(matches)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# Find matching publications across databases
def find_publication_matches(session, flora_pub, title_threshold=0.8, strategy='comprehensive'):
    # Base query for OpenAlex publications
    query = session.query(Publication)
    matching_pubs = []
    if strategy =='exact':
        # Exact DOI match
        if flora_pub.doi:
            exact_match = query.filter(Publication.doi == flora_pub.doi).first()
            if exact_match:
                matching_pubs.append(publication_to_dict(exact_match))
    elif strategy == 'fuzzy':
        # Fuzzy title matching
        fuzzy_matches = query.all()
        for pub in fuzzy_matches:
            title_similarity = fuzz.ratio(
                flora_pub.title.lower(), 
                pub.title.lower()
            )
            if title_similarity >= (title_threshold * 100):
                pub_dict = publication_to_dict(pub)
                pub_dict['similarity'] = title_similarity
                matching_pubs.append(pub_dict)
    else:
        # Combine multiple matching criteria
        comprehensive_matches = query.filter(
            # Year within ±1 year
            func.abs(Publication.year - flora_pub.year) <= 1
        ).all()
        for pub in comprehensive_matches:
            # Check title similarity
            title_similarity = fuzz.ratio(
                flora_pub.title.lower(), 
                pub.title.lower()
            )
            # Additional match scoring
            match_score = 0
            if title_similarity >= (title_threshold * 100):
                match_score += 50
            if flora_pub.doi and pub.doi == flora_pub.doi:
                match_score += 50

            if match_score > 0:
                pub_dict = publication_to_dict(pub)
                pub_dict['similarity'] = title_similarity
                pub_dict['match_score'] = match_score
                matching_pubs.append(pub_dict)
    return matching_pubs

def publication_to_dict(pub):
    return {
        'id': pub.id,
        'title': pub.title,
        'doi': pub.doi,
        'type': pub.type,
        'source': pub.source,
        'year': pub.year,
        'isValid': pub.isValid,
        'comment': pub.comment
    }


if __name__ == '__main__':
    app.run(debug=True)