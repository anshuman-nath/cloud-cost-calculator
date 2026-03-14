import React, { useState, useEffect } from 'react';
import { listBOMs, ApiError } from '../services/api';

export default function Dashboard() {
  const [boms,    setBoms]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  const [health,  setHealth]  = useState(null);

  useEffect(() => {
    // Health check
    fetch('http://localhost:8000/health')
      .then(r => r.json())
      .then(data => setHealth(data))
      .catch(() => setHealth({ status: 'unreachable' }));

    // Load BOMs
    listBOMs()
      .then(data => setBoms(data || []))
      .catch(e => setError(e instanceof ApiError ? e.detail : e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.8rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
        ☁️ Cloud Cost Calculator
      </h1>
      <p style={{ color: '#6b7280', marginBottom: '2rem' }}>
        Multi-cloud cost estimation with per-provider discount modelling
      </p>

      {/* Backend status */}
      <div style={{
        padding: '1rem 1.5rem',
        borderRadius: '12px',
        marginBottom: '1.5rem',
        background: health?.status === 'healthy' ? '#f0fdf4' : '#fef2f2',
        border: `1px solid ${health?.status === 'healthy' ? '#86efac' : '#fca5a5'}`,
      }}>
        <span style={{ fontWeight: '600', fontSize: '0.9rem' }}>
          {health?.status === 'healthy'
            ? `✅ Backend connected — ${health.app} v${health.version}`
            : health?.status === 'unreachable'
            ? '❌ Backend unreachable — is it running on port 8000?'
            : '⏳ Checking backend…'}
        </span>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        {[
          { label: 'Total BOMs',     value: loading ? '…' : boms.length,                              icon: '📋' },
          { label: 'Cloud Providers', value: loading ? '…' : new Set(boms.map(b => b.cloud_provider)).size, icon: '☁️' },
          { label: 'Total Services', value: loading ? '…' : boms.reduce((sum, b) => sum + (b.service_count || 0), 0), icon: '⚙️' },
        ].map((stat) => (
          <div key={stat.label} style={{
            background: 'white', borderRadius: '12px',
            border: '1px solid #e5e7eb', padding: '1.5rem', textAlign: 'center',
          }}>
            <div style={{ fontSize: '2rem' }}>{stat.icon}</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#1f2937' }}>{stat.value}</div>
            <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Recent BOMs */}
      <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '1rem' }}>Recent BOMs</h2>
      {error && (
        <div style={{ padding: '1rem', background: '#fef2f2', borderRadius: '8px',
          border: '1px solid #fca5a5', color: '#dc2626', marginBottom: '1rem' }}>
          ⚠️ {error}
        </div>
      )}
      {loading ? (
        <p style={{ color: '#9ca3af' }}>Loading…</p>
      ) : boms.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem',
          background: '#f9fafb', borderRadius: '12px', border: '2px dashed #e5e7eb' }}>
          <div style={{ fontSize: '3rem' }}>📋</div>
          <p style={{ color: '#6b7280', marginTop: '0.5rem' }}>
            No BOMs yet. Go to <strong>Bill of Materials</strong> to create your first one.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {boms.slice(0, 5).map(bom => (
            <div key={bom.id} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '1rem 1.25rem', background: 'white',
              borderRadius: '10px', border: '1px solid #e5e7eb',
            }}>
              <div>
                <div style={{ fontWeight: '600', color: '#1f2937' }}>{bom.name}</div>
                <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '2px' }}>
                  {bom.cloud_provider.toUpperCase()} · {bom.service_count} service{bom.service_count !== 1 ? 's' : ''}
                  {bom.azure_hybrid_benefit ? ' · 🏷️ AHB' : ''}
                </div>
              </div>
              <span style={{
                fontSize: '0.75rem', fontWeight: '600', padding: '4px 10px',
                borderRadius: '20px', background: '#dbeafe', color: '#1d4ed8',
              }}>
                {bom.cloud_provider.toUpperCase()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
