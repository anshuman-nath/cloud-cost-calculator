import React from 'react';

function Navbar({ activePage, setActivePage }) {
  const tabs = [
    { id: 'dashboard', label: '📊 Dashboard' },
    { id: 'bom', label: '🧾 Bill of Materials' },
    { id: 'scenarios', label: '🔀 Scenarios' },
    { id: 'pricing', label: '💰 Pricing' },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-brand">☁️ Cloud Cost Calculator</div>
      <div className="navbar-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`nav-btn ${activePage === tab.id ? 'active' : ''}`}
            onClick={() => setActivePage(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </nav>
  );
}

export default Navbar;
