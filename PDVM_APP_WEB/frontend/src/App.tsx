import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './Login';
import Dashboard from './Dashboard';
import './App.css';

function App() {
  const isAuthenticated = () => {
    return localStorage.getItem('access_token') !== null;
  };

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={
            isAuthenticated() ? <Navigate to="/dashboard" replace /> : <Login />
          } 
        />
        <Route 
          path="/dashboard" 
          element={
            isAuthenticated() ? <Dashboard /> : <Navigate to="/login" replace />
          } 
        />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
