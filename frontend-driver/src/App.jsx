import React, { useState } from 'react';
import { DriverAuthProvider, useDriverAuth } from './context/AuthContext';
import Login from './pages/Login';
import Layout from './pages/Layout';
import AssignedRoute from './pages/AssignedRoute';
import LiveMap from './pages/LiveMap';

function DriverMain() {
  const { isAuthenticated } = useDriverAuth();
  const [activeTab, setActiveTab] = useState('itinerary');

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'itinerary' && <AssignedRoute />}
      {activeTab === 'map' && <LiveMap />}
    </Layout>
  );
}

export default function App() {
  return (
    <DriverAuthProvider>
      <DriverMain />
    </DriverAuthProvider>
  );
}
