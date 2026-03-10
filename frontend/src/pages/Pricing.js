import React, { useState } from 'react';
import { getPricing } from '../services/api';

function Pricing() {
  const [provider, setProvider] = useState('AWS');
  const [service, setService] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    getPricing(provider, service)
      .then(res => setResults(res.data))
      .catch(() => setError('Failed to fetch pricing. Check if backend is running.'))
      .finally(() => setLoading(false));
  };

  return (
    <div className="page">
      <h2>💰 Cloud Pricing</h2>

      <div className="form-card">
        <h3>Look Up Service Pricing</h3>
        <form onSubmit={handleSearch} className="form-grid">
          <select value={provider} onChange={e => setProvider(e.target.value)}>
            <option value="AWS">AWS</option>
            <option value="Azure">Azure</option>
            <option value="GCP">GCP</option>
          </select>
          <input placeholder="Service name (e.g. EC2, S3, Lambda)" value={service}
            onChange={e => setService(e.target.value)} required />
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Searching...' : '🔍 Search Pricing'}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
      </div>

      {results && (
        <div className="table-container">
          <h3>Results for {provider} - {service}</h3>
          {Array.isArray(results) && results.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  {Object.keys(results[0]).map(k => <th key={k}>{k}</th>)}
                </tr>
              </thead>
              <tbody>
                {results.map((row, i) => (
                  <tr key={i}>
                    {Object.values(row).map((v, j) => <td key={j}>{String(v)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">No pricing data found for this service.</div>
          )}
        </div>
      )}
    </div>
  );
}

export default Pricing;
