import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', gap: '1rem', flexDirection: 'column' }}>
        <div className="animate-spin" style={{ width: '40px', height: '40px', border: '3px solid var(--border-light)', borderTop: '3px solid var(--primary)', borderRadius: '50%' }}></div>
        <p style={{ color: 'var(--text-secondary)' }}>Verificando autenticação...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};
