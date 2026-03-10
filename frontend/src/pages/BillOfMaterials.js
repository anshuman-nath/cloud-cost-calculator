import React, { useEffect, useState } from 'react';
import { getBOMItems, createBOMItem, deleteBOMItem } from '../services/api';

const EMPTY_FORM = { name: '', service_type: '', cloud_provider: 'AWS', quantity: 1, unit_cost: '' };

const CLOUD_SERVICES = {
  AWS:       ['EC2', 'S3', 'RDS', 'Lambda', 'CloudFront', 'EKS', 'ECS', 'DynamoDB', 'ElastiCache', 'Other'],
  Azure:     ['Virtual Machine', 'Blob Storage', 'SQL Database', 'Functions', 'AKS', 'Cosmos DB', 'Redis Cache', 'CDN', 'Other'],
  GCP:       ['Compute Engine', 'Cloud Storage', 'Cloud SQL', 'Cloud Functions', 'GKE', 'Firestore', 'Memorystore', 'Cloud CDN', 'Other'],
  'On-Premise': ['Physical Server', 'NAS Storage', 'Database Server', 'Load Balancer', 'Network Switch', 'Other'],
};

function BillOfMaterials() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchItems = () => {
    setLoading(true);
    getBOMItems()
      .then(res => setItems(res.data || []))
      .catch(() => setError('Failed to load BOM items.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchItems(); }, []);

  const handleProviderChange = (e) => {
    const provider = e.target.value;
    setForm({ ...form, cloud_provider: provider, service_type: '' });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    createBOMItem({ ...form, quantity: Number(form.quantity), unit_cost: Number(form.unit_cost) })
      .then(() => { setForm(EMPTY_FORM); fetchItems(); })
      .catch(() => setError('Failed to create BOM item.'));
  };

  const handleDelete = (id) => {
    deleteBOMItem(id).then(fetchItems).catch(() => setError('Failed to delete item.'));
  };

  // Group items by cloud provider
  const grouped = items.reduce((acc, item) => {
    const key = item.cloud_provider || 'Unknown';
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {});

  const providerColors = {
    AWS: '#e65100', Azure: '#1565c0', GCP: '#2e7d32', 'On-Premise': '#6a1b9a', Unknown: '#888'
  };

  return (
    <div className="page">
      <h2>🧾 Bill of Materials</h2>

      <div className="form-card">
        <h3>Add New Item</h3>
        <form onSubmit={handleSubmit} className="form-grid">
          <input
            placeholder="Item name (e.g. Web Server)"
            value={form.name}
            onChange={e => setForm({...form, name: e.target.value})}
            required
          />
          <select value={form.cloud_provider} onChange={handleProviderChange}>
            {Object.keys(CLOUD_SERVICES).map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <select
            value={form.service_type}
            onChange={e => setForm({...form, service_type: e.target.value})}
            required
          >
            <option value="">-- Select Service --</option>
            {CLOUD_SERVICES[form.cloud_provider].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <input
            type="number" placeholder="Quantity" value={form.quantity} min="1"
            onChange={e => setForm({...form, quantity: e.target.value})} required
          />
          <input
            type="number" placeholder="Unit cost ($/mo)" value={form.unit_cost} min="0" step="0.01"
            onChange={e => setForm({...form, unit_cost: e.target.value})} required
          />
          <button type="submit" className="btn-primary">➕ Add Item</button>
        </form>
        {error && <p className="error">{error}</p>}
      </div>

      {loading ? <p>Loading...</p> : (
        items.length === 0 ? (
          <div className="empty-state">📭 No BOM items yet. Add your first item above.</div>
        ) : (
          Object.entries(grouped).map(([provider, providerItems]) => {
            const total = providerItems.reduce((sum, i) => sum + (i.quantity * i.unit_cost), 0);
            return (
              <div key={provider} className="table-container" style={{marginBottom: 20}}>
                <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12}}>
                  <h3 style={{color: providerColors[provider]}}>
                    {provider === 'AWS' ? '🟠' : provider === 'Azure' ? '🔵' : provider === 'GCP' ? '🟢' : '🟣'} {provider}
                  </h3>
                  <span style={{fontWeight:700, color: providerColors[provider]}}>
                    Total: ${total.toLocaleString(undefined, {minimumFractionDigits:2})}/mo
                  </span>
                </div>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Item Name</th><th>Service</th><th>Qty</th>
                      <th>Unit Cost</th><th>Total Cost</th><th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {providerItems.map(item => (
                      <tr key={item.id}>
                        <td>{item.name}</td>
                        <td><span className="badge">{item.service_type}</span></td>
                        <td>{item.quantity}</td>
                        <td>${Number(item.unit_cost).toFixed(2)}</td>
                        <td><strong>${(item.quantity * item.unit_cost).toFixed(2)}</strong></td>
                        <td>
                          <button className="btn-danger" onClick={() => handleDelete(item.id)}>🗑️</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          })
        )
      )}
    </div>
  );
}

export default BillOfMaterials;
