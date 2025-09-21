import React, { useState, useRef, useEffect } from 'react';
import { Search, Send, Loader2, Sparkles } from 'lucide-react';
import { useApi } from '../contexts/ApiContext';
import { useSession } from '../contexts/SessionContext';
import toast from 'react-hot-toast';

interface SearchInterfaceProps {
  onSearch: (query: string) => void;
  isSearching: boolean;
}

const SearchInterface: React.FC<SearchInterfaceProps> = ({ onSearch, isSearching }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const { getSuggestions } = useApi();
  const { currentSession, addQuery } = useSession();
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isSearching) return;

    try {
      // Add query to session
      if (currentSession) {
        addQuery(query);
      }

      // Conduct research
      onSearch(query);
      setQuery('');
      setShowSuggestions(false);
    } catch (error) {
      toast.error('Failed to process query');
    }
  };

  const handleInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);

    if (value.trim().length > 2) {
      try {
        const response = await getSuggestions(value, currentSession?.id);
        if (response.success && response.suggestions) {
          const suggestionTexts = response.suggestions.map((s: any) => s.suggested_query);
          setSuggestions(suggestionTexts);
          setShowSuggestions(true);
        }
      } catch (error) {
        // Silently fail for suggestions
      }
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const exampleQueries = [
    "What are the latest trends in artificial intelligence?",
    "How does climate change affect global agriculture?",
    "What are the benefits and risks of renewable energy?",
    "Explain the impact of quantum computing on cybersecurity"
  ];

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Main search form */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="Ask anything... What would you like to research?"
            className="input-field pl-12 pr-12 text-lg"
            disabled={isSearching}
          />
          <button
            type="submit"
            disabled={!query.trim() || isSearching}
            className="absolute inset-y-0 right-0 pr-4 flex items-center"
          >
            {isSearching ? (
              <Loader2 className="h-5 w-5 text-primary-500 animate-spin" />
            ) : (
              <Send className="h-5 w-5 text-primary-500 hover:text-primary-600 transition-colors" />
            )}
          </button>
        </div>

        {/* Suggestions dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div
            ref={suggestionsRef}
            className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10 max-h-60 overflow-y-auto"
          >
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors first:rounded-t-lg last:rounded-b-lg"
              >
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-primary-500" />
                  <span className="text-gray-900 dark:text-gray-100">{suggestion}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </form>

      {/* Example queries */}
      {!query && !isSearching && (
        <div className="mt-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">Try these examples:</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {exampleQueries.map((example, index) => (
              <button
                key={index}
                onClick={() => setQuery(example)}
                className="text-left p-3 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200 text-sm"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Search status */}
      {isSearching && (
        <div className="mt-4 flex items-center justify-center space-x-2 text-primary-600 dark:text-primary-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Analyzing your query and gathering insights...</span>
        </div>
      )}
    </div>
  );
};

export default SearchInterface;
