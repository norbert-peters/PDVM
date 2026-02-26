import React, { useState } from 'react';
import './TableView.css';

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

interface TableViewProps {
  data: PDVMEntry[];
  onDelete?: (id: number) => void;
}

const TableView: React.FC<TableViewProps> = ({ data, onDelete }) => {
  const [sortField, setSortField] = useState<keyof PDVMEntry>('id');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const handleSort = (field: keyof PDVMEntry) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const filteredData = data
    .filter((entry) => {
      // Status filter
      if (filterStatus !== 'all' && entry.status !== filterStatus) {
        return false;
      }
      // Search filter
      if (searchTerm) {
        const search = searchTerm.toLowerCase();
        return (
          entry.title.toLowerCase().includes(search) ||
          entry.description?.toLowerCase().includes(search) ||
          entry.category?.toLowerCase().includes(search)
        );
      }
      return true;
    })
    .sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];

      if (aValue === null) return 1;
      if (bValue === null) return -1;

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

  const uniqueStatuses = Array.from(new Set(data.map((e) => e.status)));

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusClass = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'status-active';
      case 'completed':
        return 'status-completed';
      case 'pending':
        return 'status-pending';
      default:
        return 'status-default';
    }
  };

  return (
    <div className="table-view-container">
      <div className="table-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search entries..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-box">
          <label htmlFor="status-filter">Status:</label>
          <select
            id="status-filter"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="all">All</option>
            {uniqueStatuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('id')}>
                ID {sortField === 'id' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('title')}>
                Title {sortField === 'title' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th>Description</th>
              <th onClick={() => handleSort('status')}>
                Status {sortField === 'status' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('category')}>
                Category {sortField === 'category' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('created_at')}>
                Created {sortField === 'created_at' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.length === 0 ? (
              <tr>
                <td colSpan={7} className="no-data">
                  No entries found
                </td>
              </tr>
            ) : (
              filteredData.map((entry) => (
                <tr key={entry.id}>
                  <td>{entry.id}</td>
                  <td className="title-cell">{entry.title}</td>
                  <td className="description-cell">
                    {entry.description || <em>No description</em>}
                  </td>
                  <td>
                    <span className={`status-badge ${getStatusClass(entry.status)}`}>
                      {entry.status}
                    </span>
                  </td>
                  <td>{entry.category || <em>None</em>}</td>
                  <td className="date-cell">{formatDate(entry.created_at)}</td>
                  <td className="actions-cell">
                    {onDelete && (
                      <button
                        onClick={() => onDelete(entry.id)}
                        className="delete-button"
                        title="Delete entry"
                      >
                        🗑️
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="table-footer">
        <span>Total: {filteredData.length} entries</span>
      </div>
    </div>
  );
};

export default TableView;
