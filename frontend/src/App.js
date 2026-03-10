import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import BillOfMaterials from './pages/BillOfMaterials';
import Scenarios from './pages/Scenarios';
import Pricing from './pages/Pricing';
import './styles/App.css';

function App() {
  const [activePage, setActivePage] = useState('dashboard');

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard': return <Dashboard />;
      case 'bom': return <BillOfMaterials />;
      case 'scenarios': return <Scenarios />;
      case 'pricing': return <Pricing />;
      default: return <Dashboard />;
    }
  };

  return (
    <div className="app-container">
      <Navbar activePage={activePage} setActivePage={setActivePage} />
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  );
}

export default App;
