import React, { useState } from 'react';
import TranslationPage from '../components/translation/TranslationPage';
import ConversionPage from '../components/conversion/ConversionPage';
import { BackendStatus } from '../components/status/BackendStatus';
import { Languages, ArrowLeftRight } from 'lucide-react';
import '../styles/app/App.css';

import { useEffect } from 'react';

const AppContent = () => {
  const [activeTab, setActiveTab] = useState('translate');

  useEffect(() => {
    if (window.location.pathname === '/convert') {
      window.history.replaceState(null, '', '/');
    }
  }, []);

  return (
    <div className="app">
      <nav className="app-nav">
        <div className="nav-links">
          <button
            type="button"
            className={`nav-link ${activeTab === 'translate' ? 'active' : ''}`}
            onClick={() => setActiveTab('translate')}
          >
            <Languages size={20} /> Перевод
          </button>
          <button
            type="button"
            className={`nav-link ${activeTab === 'convert' ? 'active' : ''}`}
            onClick={() => setActiveTab('convert')}
          >
            <ArrowLeftRight size={20} /> Конвертер
          </button>
        </div>
      </nav>
      {activeTab === 'translate' ? <TranslationPage /> : <ConversionPage />}
    </div>
  );
};

const App = () => (
  <BackendStatus>
    <AppContent />
  </BackendStatus>
);

export default App;
