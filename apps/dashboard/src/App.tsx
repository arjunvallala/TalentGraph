import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { CandidateExplorerPage } from './pages/CandidateExplorerPage';
import { CandidateDetailsPage } from './pages/CandidateDetailsPage';
import { JobIntelligencePage } from './pages/JobIntelligencePage';
import { RankingsPage } from './pages/RankingsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ExplainabilityPage } from './pages/ExplainabilityPage';
import { SettingsPage } from './pages/SettingsPage';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/candidates" element={<CandidateExplorerPage />} />
            <Route path="/candidates/:id" element={<CandidateDetailsPage />} />
            <Route path="/job-intelligence" element={<JobIntelligencePage />} />
            <Route path="/rankings" element={<RankingsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/explainability" element={<ExplainabilityPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
