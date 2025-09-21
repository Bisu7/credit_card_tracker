import React, { createContext, useContext, useState } from 'react';
import axios from 'axios';

interface ApiContextType {
  isConnected: boolean;
  systemStatus: any;
  checkConnection: () => Promise<boolean>;
  getSystemStatus: () => Promise<any>;
  uploadDocuments: (files: File[]) => Promise<any>;
  conductResearch: (query: string, sessionId?: string) => Promise<any>;
  getSuggestions: (query: string, sessionId?: string) => Promise<any>;
}

const ApiContext = createContext<ApiContextType | undefined>(undefined);

export const ApiProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);

  const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:9000',
    timeout: 30000,
  });

  const checkConnection = async (): Promise<boolean> => {
    try {
      const response = await api.get('/');
      setIsConnected(response.status === 200);
      return response.status === 200;
    } catch (error) {
      setIsConnected(false);
      return false;
    }
  };

  const getSystemStatus = async () => {
    try {
      const response = await api.get('/status');
      setSystemStatus(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to get system status:', error);
      throw error;
    }
  };

  const uploadDocuments = async (files: File[]) => {
    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await api.post('/ingest', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data;
    } catch (error) {
      console.error('Document upload failed:', error);
      throw error;
    }
  };

  const conductResearch = async (query: string, sessionId?: string) => {
    try {
      const response = await api.post('/research', {
        query,
        session_id: sessionId,
        max_sources: 10
      });

      return response.data;
    } catch (error) {
      console.error('Research failed:', error);
      throw error;
    }
  };

  const getSuggestions = async (query: string, sessionId?: string) => {
    try {
      const response = await api.post('/suggest', {
        query,
        session_id: sessionId
      });

      return response.data;
    } catch (error) {
      console.error('Failed to get suggestions:', error);
      throw error;
    }
  };

  return (
    <ApiContext.Provider value={{
      isConnected,
      systemStatus,
      checkConnection,
      getSystemStatus,
      uploadDocuments,
      conductResearch,
      getSuggestions
    }}>
      {children}
    </ApiContext.Provider>
  );
};

export const useApi = () => {
  const context = useContext(ApiContext);
  if (context === undefined) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
};
