import React, { useState, useEffect } from 'react';
import axios from 'axios';

function PublicationValidation() {
  const [publications, setPublications] = useState([]);
  const [filter, setFilter] = useState('');
  const [showUnvalidatedOnly, setShowUnvalidatedOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch publication data on component mount
  useEffect(() => {
    setLoading(true);
    axios.get('http://localhost:5000/api/publications?source=openalex')
      .then(response => {
        setPublications(sortPublications(response.data));
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching publications:', err);
        setError('Failed to load publications. Please try again later.');
        setLoading(false);
      });
  }, []);

  // Sorting and filtering publications
  const sortPublications = (pubs) => {
    return pubs.sort((a, b) => {
      // First, sort by year
      if (a.year !== b.year) {
        return a.year - b.year;
      }
      // If years are the same, sort by ID
      return a.id.localeCompare(b.id);
    });
  };

  const handleValidationChange = (id, isValid) => {
    axios.put(`http://localhost:5000/api/publications/${encodeURIComponent(id)}/validate`, { isValid })
      .then(() => {
        setPublications(prev => {
          const updatedPubs = prev.map(pub =>
            pub.id === id ? { ...pub, isValid: isValid } : pub
          );
          return sortPublications(updatedPubs);
        });
      })
      .catch(err => {
        console.error('Error updating validation:', err.response ? err.response.data : err);
        alert('Failed to update publication validation');
      });
  };

  const handleCommentChange = (id, comment) => {
    axios.put(`http://localhost:5000/api/publications/${encodeURIComponent(id)}/validate`, { comment })
      .then(() => {
        setPublications(prev => prev.map(pub =>
          pub.id === id ? { ...pub, comment } : pub
        ));
      })
      .catch(err => console.error('Error adding comment:', err));
  };

  // Filter publications by title and validation status
  const filteredPublications = publications
    .filter(pub => {
      // Filter by title (case insensitive)
      const titleMatch = pub.title.toLowerCase().includes(filter.toLowerCase());
      
      // Filter by validation status if showUnvalidatedOnly is true
      // const validationMatch = !showUnvalidatedOnly || pub.isValid === false;
      const validationMatch = showUnvalidatedOnly || pub.isValid === true;
      
      return titleMatch && validationMatch;
    });

  if (loading) {
    return <div className="loading">Loading publications...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="publication-validation">
      <h2>Publication Validation</h2>
      <div className="filter-controls">
        <div className="filter-option">
          <input 
            type="checkbox" 
            id="showUnvalidated"
            checked={showUnvalidatedOnly}
            onChange={(e) => setShowUnvalidatedOnly(e.target.checked)}
          />
          <label htmlFor="showUnvalidated">Show unvalidated only</label>
        </div>
        
        <div className="search-box">
          <input
            type="text"
            placeholder="Filter by title..."
            value={filter}
            onChange={e => setFilter(e.target.value)}
            style={{ width: '300px', padding: '5px' }}
          />
        </div>
      </div>
      
      <div className="publications-table">
        <table border="1" cellPadding="8" style={{ borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>DOI</th>
              <th>Type</th>
              <th>SOURCE</th>
              <th>Year</th>
              <th>Valid</th>
              <th>Comment</th>
            </tr>
          </thead>
          <tbody>
            {filteredPublications.map(pub => (
              <tr key={pub.id}>
                <td>{pub.id}</td>
                <td>{pub.title}</td>
                <td>{pub.doi}</td>
                <td>{pub.type}</td>
                <td>{pub.source}</td>
                <td>{pub.year}</td>
                <td style={{ textAlign: 'center' }}>
                  <input
                    type="checkbox"
                    checked={pub.isValid || false}
                    onChange={e => handleValidationChange(pub.id, e.target.checked)}
                  />
                </td>
                <td>
                  <input
                    type="text"
                    value={pub.comment || ''}
                    onChange={e => handleCommentChange(pub.id, e.target.value)}
                    placeholder="Add comment..."
                    style={{ width: '100%' }}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default PublicationValidation;