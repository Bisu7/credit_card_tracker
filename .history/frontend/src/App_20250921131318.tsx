import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Header from './components/Header';
import SearchInterface from './components/SearchInterface';
import ResultsDisplay from './components/ResultsDisplay';
import DocumentUpload from './components/DocumentUpload';
import SessionHistory from './components/SessionHistory';
import { ThemeProvider } from './contexts/ThemeContext';
import { SessionProvider } from './contexts/SessionContext';
import { ApiProvider } from './contexts/ApiContext';

function App() {
  return (
    <ThemeProvider>
      <ApiProvider>
        <SessionProvider>
          <Router>
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
              <Header />
              <main className="container mx-auto px-4 py-8">
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/upload" element={<DocumentUpload />} />
                  <Route path="/history" element={<SessionHistory />} />
                </Routes>
              </main>
              <Toaster 
                position="top-right"
                toastOptions={{
                  duration: 4000,
                  style: {
                    background: 'var(--toast-bg)',
                    color: 'var(--toast-color)',
                  },
                }}
              />
            </div>
          </Router>
        </SessionProvider>
      </ApiProvider>
    </ThemeProvider>
  );
}

function HomePage() {
  const [searchResults, setSearchResults] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (query: string) => {
    setIsSearching(true);
    setSearchResults(null);
    
    try {
      const response = await fetch('https://deepresearch-2fou.onrender.com/research', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      
      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          Deep Researcher
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          AI-powered research assistant for deep analysis and insights
        </p>
      </div>
      
      <SearchInterface onSearch={handleSearch} isSearching={isSearching} />
      
      {searchResults && (
        <ResultsDisplay results={searchResults} />
      )}
    </div>
  );
}

export default App;
