import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Layout from './pages/Layout';
import FleetOverview from './pages/FleetOverview';

import RouteAssignment from './pages/RouteAssignment';
import VehicleManagement from './pages/VehicleManagement';
import Diagnostics from './pages/Diagnostics';

function MainApp() {
  const { isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'overview' && <FleetOverview />}
      {activeTab === 'routing' && <RouteAssignment />}
      {activeTab === 'vehicles' && <VehicleManagement />}
      {activeTab === 'diagnostics' && <Diagnostics />}
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
