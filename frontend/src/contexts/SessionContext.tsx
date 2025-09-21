import React, { createContext, useContext, useState, useEffect } from 'react';

interface Session {
  id: string;
  title: string;
  description: string;
  createdAt: string;
  queries: Query[];
}

interface Query {
  id: string;
  query: string;
  timestamp: string;
  results?: any;
}

interface SessionContextType {
  currentSession: Session | null;
  sessions: Session[];
  createSession: (title: string, description?: string) => string;
  setCurrentSession: (sessionId: string) => void;
  addQuery: (query: string, results?: any) => void;
  getSessionHistory: () => Session[];
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSessionState] = useState<Session | null>(null);

  useEffect(() => {
    const savedSessions = localStorage.getItem('deep-researcher-sessions');
    if (savedSessions) {
      setSessions(JSON.parse(savedSessions));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('deep-researcher-sessions', JSON.stringify(sessions));
  }, [sessions]);

  const createSession = (title: string, description = '') => {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newSession: Session = {
      id: sessionId,
      title,
      description,
      createdAt: new Date().toISOString(),
      queries: []
    };
    
    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionState(newSession);
    return sessionId;
  };

  const setCurrentSession = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setCurrentSessionState(session);
    }
  };

  const addQuery = (query: string, results?: any) => {
    if (!currentSession) return;

    const queryId = `query_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newQuery: Query = {
      id: queryId,
      query,
      timestamp: new Date().toISOString(),
      results
    };

    const updatedSession = {
      ...currentSession,
      queries: [...currentSession.queries, newQuery]
    };

    setCurrentSessionState(updatedSession);
    setSessions(prev => 
      prev.map(s => s.id === currentSession.id ? updatedSession : s)
    );
  };

  const getSessionHistory = () => sessions;

  return (
    <SessionContext.Provider value={{
      currentSession,
      sessions,
      createSession,
      setCurrentSession,
      addQuery,
      getSessionHistory
    }}>
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};
