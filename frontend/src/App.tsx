// SUGAR — Polished Application Entry Point
import React, { useState } from 'react';
import { DisclaimerBanner } from './components/layout/DisclaimerBanner';
import { Navbar, SectionId } from './components/layout/Navbar';
import { Overview } from './components/overview/Overview';
import { BodyLab } from './components/3d/BodyLab';
import { RiskLab } from './components/inference/RiskLab';
import { ResearchLab } from './components/research/ResearchLab';
import { ModelArena } from './components/arena/ModelArena';
import { MethodsLimitations } from './components/methods/MethodsLimitations';

export function App() {
  const [activeSection, setActiveSection] = useState<SectionId>('overview');

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 1. Persistent Compact Disclaimer */}
      <DisclaimerBanner />

      {/* 2. Top Application Navigation Shell */}
      <Navbar activeSection={activeSection} onSelectSection={setActiveSection} />

      {/* 3. Main Workspace Container */}
      <main className="container flex-1 py-6" style={{ width: '100%' }}>
        {activeSection === 'overview' && <Overview onNavigate={setActiveSection} />}
        {activeSection === 'bodylab' && <BodyLab />}
        {activeSection === 'risklab' && <RiskLab />}
        {activeSection === 'research' && <ResearchLab />}
        {activeSection === 'arena' && <ModelArena />}
        {activeSection === 'methods' && <MethodsLimitations />}
      </main>

      {/* 4. Polished App Footer */}
      <footer
        style={{
          background: 'rgba(7, 10, 20, 0.98)',
          borderTop: '1px solid var(--navy-clinical)',
          padding: '16px 0',
          marginTop: 'auto',
          fontSize: '0.82rem',
          color: 'var(--steel-blue)',
        }}
      >
        <div className="container flex items-center justify-between gap-4 flex-wrap">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: 700, color: '#ffffff', fontFamily: 'JetBrains Mono' }}>SUGAR</span>
            <span>—</span>
            <span>Liver Fibrosis Research Platform</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.8rem' }}>
            <span>NHANES 2017–2020 (N=7,211)</span>
            <span>•</span>
            <span>Egyptian HCV Cohort (N=1,385)</span>
            <span>•</span>
            <button
              onClick={() => setActiveSection('methods')}
              style={{ background: 'transparent', border: 'none', color: 'var(--ice-blue)', cursor: 'pointer', textDecoration: 'underline' }}
            >
              Non-Diagnostic Disclaimer
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
