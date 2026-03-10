import React, { useEffect, useState } from 'react';
import { getScenarios, createScenario, deleteScenario } from '../services/api';

const EMPTY_FORM = { name: '', description: '', cloud_provider: 'AWS' };

function Scenarios() {
  const [scenarios, setScenarios] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchScenarios = () => {
    setLoading(true);
    getScenarios()
      .then(res => setScenarios(res.data || []))
      .catch(() => setError('Failed to load scenarios.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchScenarios(); }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    createScenario(form)
      .then(() => { setForm(EMPTY_FORM); fetchScenarios(); })
      .catch(() => setError('Failed to create scenario.'));
  };

  const handleDelete = (id) => {
    deleteScenario(id).then(fetchScenarios).catch(() => setError('Failed to delete.'));
  };

  const providers = ['AWS', 'Azure', 'GCP', 'On-Premise'];

  return (
    <div className="page">
      <h2>🔀 Scenarios</h2>

      <div className="form-card">
        <h3>Create New Scenario</h3>
        <form onSubmit={handleSubmit} className="form-grid">
          <input placeholder="Scenario name" value={form.name}
            onChange={e => setForm({...form, name: e.target.value})} required />
          <input placeholder="Description" value={form.description}
            onChange={e => setForm({...form, description: e.target.value})} />
          <select value={form.cloud_provider}
            onChange={e => setForm({...form, cloud_provider: e.target.value})}>
            {providers.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <button type="submit" className="btn-primary">➕ Create Scenario</button>
        </form>
        {error && <p className="error">{error}</p>}
      </div>

      {loading ? <p>Loading...</p> : (
        <div className="cards-grid">
          {scenarios.length === 0 ? (
            <div className="empty-state">📭 No scenarios yet. Create your first scenario above.</div>
          ) : scenarios.map(s => (
            <div key={s.id} className="scenario-card">
              <div className="scenario-header">
                <h4>{s.name}</h4>
                <span className={`provider-badge provider-${s.cloud_provider?.toLowerCase()}`}>
                  {s.cloud_provider}
                </span>
              </div>
              <p className="scenario-desc">{s.description || 'No description'}</p>
              <div className="scenario-footer">
                <span className="cost">${Number(s.total_cost || 0).toLocaleString()}/mo</span>
                <button className="btn-danger" onClick={() => handleDelete(s.id)}>🗑️ Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Scenarios;
