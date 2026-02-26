import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from './client';
import TableView from './TableView';
import './Dashboard.css';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

interface PDVMEntry {
  id: number;
  title: string;
  description: string | null;
  status: string;
  category: string | null;
  user_id: number;
  created_at: string;
  updated_at: string | null;
}

const Dashboard: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [entries, setEntries] = useState<PDVMEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [userData, entriesData] = await Promise.all([
        apiClient.getCurrentUser(),
        apiClient.getEntries(),
      ]);
      setUser(userData);
      setEntries(entriesData);
    } catch (err: any) {
      setError('Failed to load data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    navigate('/login');
  };

  const handleCreateEntry = async () => {
    const title = prompt('Enter entry title:');
    if (!title) return;

    const description = prompt('Enter entry description (optional):');

    try {
      await apiClient.createEntry({
        title,
        description: description || undefined,
        status: 'active',
      });
      loadData(); // Reload data
    } catch (err) {
      alert('Failed to create entry');
    }
  };

  const handleDeleteEntry = async (id: number) => {
    if (!confirm('Are you sure you want to delete this entry?')) return;

    try {
      await apiClient.deleteEntry(id);
      loadData(); // Reload data
    } catch (err) {
      alert('Failed to delete entry');
    }
  };

  if (loading) {
    return <div className="dashboard-loading">Loading...</div>;
  }

  if (error) {
    return <div className="dashboard-error">{error}</div>;
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>PDVM Dashboard</h1>
        <div className="header-info">
          <span className="user-info">
            Welcome, <strong>{user?.full_name || user?.username}</strong>
          </span>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-stats">
          <div className="stat-card">
            <h3>Total Entries</h3>
            <p className="stat-value">{entries.length}</p>
          </div>
          <div className="stat-card">
            <h3>Active</h3>
            <p className="stat-value">
              {entries.filter((e) => e.status === 'active').length}
            </p>
          </div>
          <div className="stat-card">
            <h3>Completed</h3>
            <p className="stat-value">
              {entries.filter((e) => e.status === 'completed').length}
            </p>
          </div>
        </div>

        <div className="dashboard-actions">
          <button onClick={handleCreateEntry} className="create-button">
            + Create New Entry
          </button>
          <button onClick={loadData} className="refresh-button">
            🔄 Refresh
          </button>
        </div>

        <TableView
          data={entries}
          onDelete={handleDeleteEntry}
          onRefresh={loadData}
        />
      </main>
    </div>
  );
};

export default Dashboard;
