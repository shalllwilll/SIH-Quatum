import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Layout from './pages/Layout';
import FleetOverview from './pages/FleetOverview';

function MainApp() {
  const { isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'overview' && <FleetOverview />}
      {activeTab === 'routing' && (
        <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
          <h2>Route Assignment</h2>
          <p style={{ color: 'var(--text-muted)' }}>Routing Optimization interface loading...</p>
        </div>
      )}
      {activeTab === 'vehicles' && (
        <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
          <h2>Vehicles & Drivers</h2>
          <p style={{ color: 'var(--text-muted)' }}>Vehicle and Driver management loading...</p>
        </div>
      )}
      {activeTab === 'diagnostics' && (
        <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
          <h2>Live Traffic & Engine Diagnostics</h2>
          <p style={{ color: 'var(--text-muted)' }}>Real-time TomTom live traffic & QGA/QPSO engine telemetry.</p>
        </div>
      )}
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
