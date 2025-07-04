import React, { useState } from 'react';
import PublicationValidation from './PublicationValidation';
import PublicationMatcher from './PublicationMatcher';
import '../styles/PublicationHelper.css';

function PublicationHelper() {
  const [activeTab, setActiveTab] = useState('validation');

  return (
    <div className="publication-helper">
      <div className="tabs">
        <button 
          onClick={() => setActiveTab('validation')}
          className={`tab-button ${activeTab === 'validation' ? 'active' : ''}`}
        >
          Publications Validation
        </button>
        <button 
          onClick={() => setActiveTab('matching')}
          className={`tab-button ${activeTab === 'matching' ? 'active' : ''}`}
        >
          Publication Matching
        </button>
      </div>

      {/* <div className="tab-content"> */}
      <div>
        {activeTab === 'validation' && <PublicationValidation />}
        {activeTab === 'matching' && <PublicationMatcher />}
      </div>
    </div>
  );
}

export default PublicationHelper;