import React, { useState } from 'react';
import { 
  History, 
  Search, 
  Clock, 
  Eye, 
  Copy,
  Calendar,
  MessageSquare,
  TrendingUp
} from 'lucide-react';
import { useSession } from '../contexts/SessionContext';
import { useApi } from '../contexts/ApiContext';
import toast from 'react-hot-toast';

const SessionHistory: React.FC = () => {
  const { sessions, setCurrentSession, createSession } = useSession();
  const { conductResearch } = useApi();
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 48) return 'Yesterday';
    return date.toLocaleDateString();
  };

  const handleSessionClick = (sessionId: string) => {
    setSelectedSession(selectedSession === sessionId ? null : sessionId);
    setCurrentSession(sessionId);
  };

  const handleQueryClick = async (query: string) => {
    try {
      const result = await conductResearch(query);
      if (result.success) {
        toast.success('Research completed');
      } else {
        toast.error('Research failed: ' + result.error);
      }
    } catch (error: any) {
      toast.error('Research failed: ' + error.message);
    }
  };

  const copyQuery = (query: string) => {
    navigator.clipboard.writeText(query);
    toast.success('Query copied to clipboard');
  };

  const createNewSession = () => {
    const title = prompt('Enter session title:');
    if (title) {
      const description = prompt('Enter session description (optional):') || '';
      createSession(title, description);
      toast.success('New session created');
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Session History
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            View and manage your research sessions
          </p>
        </div>
        <button
          onClick={createNewSession}
          className="btn-primary"
        >
          <MessageSquare className="w-4 h-4 mr-2" />
          New Session
        </button>
      </div>

      {/* Search Sessions */}
      <div className="card p-6 mb-6">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search sessions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-field pl-10"
            />
          </div>
        </div>
      </div>

      {/* Sessions List */}
      <div className="space-y-4">
        {filteredSessions.length === 0 ? (
          <div className="card p-8 text-center">
            <History className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No sessions found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {searchQuery ? 'Try adjusting your search terms' : 'Start a new research session to see your history here'}
            </p>
            {!searchQuery && (
              <button
                onClick={createNewSession}
                className="btn-primary"
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                Create First Session
              </button>
            )}
          </div>
        ) : (
          filteredSessions.map((session) => (
            <div key={session.id} className="card p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <button
                      onClick={() => handleSessionClick(session.id)}
                      className="flex items-center space-x-2 text-left hover:text-primary-600 transition-colors"
                    >
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {session.title}
                      </h3>
                      {selectedSession === session.id ? (
                        <TrendingUp className="w-4 h-4 text-primary-500" />
                      ) : (
                        <MessageSquare className="w-4 h-4 text-gray-400" />
                      )}
                    </button>
                  </div>
                  
                  {session.description && (
                    <p className="text-gray-600 dark:text-gray-400 mb-3">
                      {session.description}
                    </p>
                  )}

                  <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                    <div className="flex items-center space-x-1">
                      <Calendar className="w-4 h-4" />
                      <span>{formatDate(session.createdAt)}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <MessageSquare className="w-4 h-4" />
                      <span>{session.queries.length} queries</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Session Queries */}
              {selectedSession === session.id && (
                <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-4">
                    Queries ({session.queries.length})
                  </h4>
                  
                  {session.queries.length === 0 ? (
                    <p className="text-gray-500 dark:text-gray-400 italic">
                      No queries in this session yet
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {session.queries.map((query) => (
                        <div
                          key={query.id}
                          className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-gray-900 dark:text-white mb-2">
                                {query.query}
                              </p>
                              <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                                <div className="flex items-center space-x-1">
                                  <Clock className="w-3 h-3" />
                                  <span>{formatDate(query.timestamp)}</span>
                                </div>
                                {query.results && (
                                  <div className="flex items-center space-x-1">
                                    <Eye className="w-3 h-3" />
                                    <span>Completed</span>
                                  </div>
                                )}
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-2 ml-4">
                              <button
                                onClick={() => copyQuery(query.query)}
                                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                                title="Copy query"
                              >
                                <Copy className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleQueryClick(query.query)}
                                className="p-1 text-gray-400 hover:text-primary-600 transition-colors"
                                title="Re-run query"
                              >
                                <Search className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Statistics */}
      {sessions.length > 0 && (
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card p-4 text-center">
            <div className="text-2xl font-bold text-primary-600 dark:text-primary-400 mb-1">
              {sessions.length}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Total Sessions
            </div>
          </div>
          <div className="card p-4 text-center">
            <div className="text-2xl font-bold text-primary-600 dark:text-primary-400 mb-1">
              {sessions.reduce((total, session) => total + session.queries.length, 0)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Total Queries
            </div>
          </div>
          <div className="card p-4 text-center">
            <div className="text-2xl font-bold text-primary-600 dark:text-primary-400 mb-1">
              {sessions.filter(s => s.queries.length > 0).length}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Active Sessions
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionHistory;
