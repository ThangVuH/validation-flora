import React, { useState, useEffect } from 'react';
import axios from 'axios';
// import '../styles/PublicationMatcher.css';

const PublicationMatcher = () => {
  const [publicationMatches, setPublicationMatches] = useState([]);
  const [matchingStrategy, setMatchingStrategy] = useState('comprehensive');
  const [similarityThreshold, setSimilarityThreshold] = useState(0.8);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchMatches = async () => {
      setIsLoading(true);
      try {
        const response = await axios.get('http://localhost:5000/api/publications/match', {
          params: {
            strategy: matchingStrategy,
            title_threshold: similarityThreshold
          }
        });
        setPublicationMatches(response.data);
      } catch (error) {
        console.error('Matching failed:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMatches();
  }, [matchingStrategy, similarityThreshold]);

  const handleValidationChange = async (candidateId, isValid) => {
    try {
      await axios.put(`http://localhost:5000/api/publications/${encodeURIComponent(candidateId)}/validate`, { 
        isValid 
      });
      
      // Update local state to reflect validation
      setPublicationMatches(prevMatches => 
        prevMatches.map(match => ({
          ...match,
          matching_candidates: match.matching_candidates.map(candidate => 
            candidate.id === candidateId 
              ? { ...candidate, isValid } 
              : candidate
          )
        }))
      );
    } catch (error) {
      console.error('Failed to update validation:', error);
    }
  };

  const handleCommentChange = async (candidateId, comment) => {
    try {
      await axios.put(`http://localhost:5000/api/publications/${encodeURIComponent(candidateId)}/validate`, { 
        comment 
      });
      
      // Update local state to reflect comment
      setPublicationMatches(prevMatches => 
        prevMatches.map(match => ({
          ...match,
          matching_candidates: match.matching_candidates.map(candidate => 
            candidate.id === candidateId 
              ? { ...candidate, comment } 
              : candidate
          )
        }))
      );
    } catch (error) {
      console.error('Failed to update comment:', error);
    }
  };

  return (
    <div className="publication-matcher">
      <h2>Publication Matching</h2>
      <div className="matcher-controls">
        <div>
          <label>
            Matching Strategy:
            <select 
              value={matchingStrategy}
              onChange={(e) => setMatchingStrategy(e.target.value)}
            >
              <option value="exact">Exact Match</option>
              <option value="fuzzy">Fuzzy Match</option>
              <option value="comprehensive">Comprehensive</option>
            </select>
          </label>
          <label>
            Similarity Threshold:
            <input 
              type="number" 
              step="0.1" 
              min="0" 
              max="1"
              value={similarityThreshold}
              onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
            />
          </label>
        </div>
      </div>

      {isLoading ? (
        <div className="loading">Loading matches...</div>
      ) : (
        <div className="matches-container">
          {publicationMatches.length > 0 ? publicationMatches.map((match, index) => (
            <div key={index} className="match-group">
              <div className="flora-publication">
                <h3>Flora Publication</h3>
                <table border="1" cellPadding="8" style={{ borderCollapse: 'collapse', width: '100%' }}>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Title</th>
                      <th>DOI</th>
                      <th>SOURCE</th>
                      <th>Year</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>{match.flora_publication.id}</td>
                      <td>{match.flora_publication.title}</td>
                      <td>{match.flora_publication.doi || 'N/A'}</td>
                      <td>{match.flora_publication.source || 'N/A'}</td>
                      <td>{match.flora_publication.year || 'N/A'}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="matching-candidates">
                <h4>Matching Candidates</h4>
                {match.matching_candidates.length > 0 ? (
                  <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>DOI</th>
                        <th>SOURCE</th>
                        <th>Year</th>
                        <th>Similarity</th>
                        <th>Valid</th>
                        <th>Comment</th>
                      </tr>
                    </thead>
                    <tbody>
                      {match.matching_candidates.map((candidate, candidateIndex) => (
                        <tr key={candidateIndex}>
                          <td>{candidate.id}</td>
                          <td>{candidate.title}</td>
                          <td>{candidate.doi || 'N/A'}</td>
                          <td>{candidate.source || 'N/A'}</td>
                          <td>{candidate.year}</td>
                          <td>{candidate.similarity ? `${candidate.similarity}%` : 'N/A'}</td>
                          <td>
                            <input
                              type="checkbox"
                              checked={candidate.isValid || false}
                              onChange={(e) => handleValidationChange(
                                candidate.id, 
                                e.target.checked
                              )}
                            />
                          </td>
                          <td>
                            <input
                              type="text"
                              value={candidate.comment || ''}
                              onChange={(e) => handleCommentChange(
                                candidate.id, 
                                e.target.value
                              )}
                              placeholder="Add comment..."
                              style={{ width: '100%' }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p>No matches found</p>
                )}
              </div>
            </div>
          )) : (
            <p>No publication matches found</p>
          )}
        </div>
      )}
    </div>
  );
};

export default PublicationMatcher;