import React, { useState } from 'react';
import Layout from './pages/Layout';
import ActiveDashboard from './pages/ActiveDashboard';
import ComparisonDashboard from './pages/ComparisonDashboard';
import AnalysisDashboard from './pages/AnalysisDashboard';

export default function App() {
  const [activeTab, setActiveTab] = useState('active');

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'active' && <ActiveDashboard />}
      {activeTab === 'comparison' && <ComparisonDashboard setActiveTab={setActiveTab} />}
      {activeTab === 'analysis' && <AnalysisDashboard />}
    </Layout>
  );
}
