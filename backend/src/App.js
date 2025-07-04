// import PublicationCorpusHelper from './components/PublicationHelper_0';
// import FetchData from './components/FetchData';

// function App() {
//   return (
//     <div className="App">
//       <PublicationCorpusHelper />   
//     </div>
//   );
// }

// export default App;

// ==========================================

import React, { useState } from 'react';
import FetchData from './components/FetchData';
import PublicationHelper from './components/PublicationHelper';
import './styles/FetchData.css';

function App() {
  const [activePage, setActivePage] = useState('home');

  const renderHomePage = () => (
    <div className="home-options">
      <h2>Bibliometric Data Management</h2>
      <div className="button-group">
        <button 
          onClick={() => setActivePage('fetchData')}
          className="main-button"
        >
          Fetch Data
        </button>
        <button 
          onClick={() => setActivePage('validatePublication')}
          className="main-button"
        >
          Validate Publications
        </button>

        <button 
          onClick={() => setActivePage('fetchData')}
          className="main-button"
          disabled
        >
          Citation Network (Coming Soon)
        </button>
        <button 
          onClick={() => setActivePage('fetchData')}
          className="main-button"
          disabled
        >
          Patent Network (Coming Soon)
        </button>
      </div>
    </div>
  );

  const renderPage = () => {
    switch (activePage) {
      case 'fetchData':
        return (
          <>
            <FetchData />
            <button 
              onClick={() => setActivePage('home')}
              className="back-button"
            >
              Back
            </button>
          </>
        );
      case 'validatePublication':
        return (
          <>
            <PublicationHelper />
            <button 
              onClick={() => setActivePage('home')}
              className="back-button"
            >
              Back
            </button>
          </>
        );
      default: // Home page
        return renderHomePage();
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Bibliometric Data Application</h1>
      </header>
      <main>
        {renderPage()}
      </main>
      <footer>
        <p>&copy; 2025 Bibliometric Data Manager</p>
      </footer>
    </div>
  );
}

export default App;