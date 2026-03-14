import React from 'react';

export default function Pricing() {
  return (
    <div style={{ padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.8rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
        💰 Pricing Reference
      </h1>
      <p style={{ color: '#6b7280', marginBottom: '2rem' }}>
        Live pricing is fetched directly from cloud provider APIs when you generate scenarios.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
        {[
          { provider: 'AWS',   icon: '🟠', source: 'AWS Bulk Pricing API',       url: 'https://pricing.us-east-1.amazonaws.com' },
          { provider: 'Azure', icon: '🔵', source: 'Azure Retail Prices API',    url: 'https://prices.azure.com/api/retail/prices' },
          { provider: 'GCP',   icon: '🔴', source: 'GCP Regional Rate Table',    url: 'https://cloud.google.com/compute/vm-instance-pricing' },
        ].map((p) => (
          <div key={p.provider} style={{
            background: 'white', borderRadius: '12px',
            border: '1px solid #e5e7eb', padding: '1.5rem',
          }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>{p.icon}</div>
            <div style={{ fontWeight: '700', fontSize: '1.1rem', marginBottom: '0.25rem' }}>{p.provider}</div>
            <div style={{ fontSize: '0.8rem', color: '#6b7280', marginBottom: '0.75rem' }}>{p.source}</div>
            <a href={p.url} target="_blank" rel="noreferrer"
              style={{ fontSize: '0.75rem', color: '#2563eb', textDecoration: 'underline' }}>
              View pricing docs →
            </a>
          </div>
        ))}
      </div>

      <div style={{ marginTop: '2rem', padding: '1rem 1.5rem',
        background: '#eff6ff', borderRadius: '12px', border: '1px solid #bfdbfe' }}>
        <p style={{ fontSize: '0.85rem', color: '#1d4ed8' }}>
          💡 To see live prices, go to <strong>Bill of Materials</strong> → create a BOM →
          then go to <strong>Scenarios</strong> → click <strong>Generate Scenarios</strong>.
        </p>
      </div>
    </div>
  );
}
