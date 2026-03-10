import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getBOMItems, getScenarios, healthCheck } from '../services/api';

function Dashboard() {
  const [status, setStatus] = useState('checking...');
  const [bomCount, setBomCount] = useState(0);
  const [scenarioCount, setScenarioCount] = useState(0);
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    healthCheck()
      .then(() => setStatus('🟢 Online'))
      .catch(() => setStatus('🔴 Offline'));

    getBOMItems()
      .then(res => {
        const items = res.data || [];
        setBomCount(items.length);
      })
      .catch(() => setBomCount(0));

    getScenarios()
      .then(res => {
        const scenarios = res.data || [];
        setScenarioCount(scenarios.length);
        const data = scenarios.slice(0, 6).map(s => ({
          name: s.name || `Scenario ${s.id}`,
          cost: s.total_cost || 0,
        }));
        setChartData(data);
      })
      .catch(() => setScenarioCount(0));
  }, []);

  return (
    <div className="page">
      <h2>Dashboard</h2>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Backend Status</div>
          <div className="stat-value">{status}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">BOM Items</div>
          <div className="stat-value">{bomCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Scenarios</div>
          <div className="stat-value">{scenarioCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">API Base</div>
          <div className="stat-value" style={{fontSize:'0.9rem'}}>localhost:8000</div>
        </div>
      </div>

      {chartData.length > 0 && (
        <div className="chart-container">
          <h3>Scenario Cost Comparison</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
              <Legend />
              <Bar dataKey="cost" fill="#4f8ef7" name="Total Cost ($)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {chartData.length === 0 && (
        <div className="empty-state">
          <p>📭 No scenario data yet. Create scenarios to see cost comparisons here.</p>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
