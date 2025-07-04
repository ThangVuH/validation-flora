import React, { useState } from 'react';
import '../styles/FetchData.css';

function FetchData() {
  const [apiResponse, setApiResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Define the API base URL
  const API_BASE_URL = 'http://127.0.0.1:5000'; // Change this to match your backend URL

  const handleFetchData = async (dataType) => {
    setIsLoading(true);
    setApiResponse(null);
    setErrorMessage('');

    try {
      let endpoint = `${API_BASE_URL}/fetch_data`;
      
      // Add query parameters based on data type
      if (dataType === 'flora_data') {
        // Only fetch Flora data
        endpoint += '?source=flora';
      } else if (dataType === 'other_data') {
        // Fetch OpenAlex and HAL data
        endpoint += '?source=openalex';
      }
      // For 'all', we don't need to add any parameters

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'An error occurred while fetching data');
      }
      
      setApiResponse(data);
    } catch (error) {
      console.error('Error fetching data:', error);
      setErrorMessage(error.message || 'Failed to fetch data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderFetchOptions = () => (
    <div className="fetch-options">
      <h2>Select Data to Fetch</h2>
      <div className="button-group">
        <button 
          onClick={() => handleFetchData('flora_data')}
          className="option-button"
        >
          Flora Data
        </button>
        <button 
          onClick={() => handleFetchData('other_data')}
          className="option-button"
        >
          OpenAlex/HAL Data
        </button>
        <button 
          onClick={() => handleFetchData('all')}
          className="option-button"
        >
          All Sources
        </button>
        <button 
          onClick={() => handleFetchData('validate')}
          className="main-button"
          disabled
        >
          WoS data (Coming Soon)
        </button>
      </div>
    </div>
  );

  const renderResponse = () => {
    if (isLoading) {
      return <div className="loading">Fetching data... This may take a while.</div>;
    }

    if (errorMessage) {
      return <div className="error">{errorMessage}</div>;
    }

    if (apiResponse) {
      return (
        <div className="response">
          <h3>API Response:</h3>
          <pre>{JSON.stringify(apiResponse, null, 2)}</pre>
          {apiResponse.message && (
            <div className="success-message">
              {apiResponse.message}
            </div>
          )}
        </div>
      );
    }

    return null;
  };

  return (
    <div>
      {renderFetchOptions()}
      {renderResponse()}
    </div>
  );
}

export default FetchData;