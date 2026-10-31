// SUGAR — Application Shell Navbar
import React, { useEffect, useState } from 'react';
import {
  Activity,
  Layers,
  BarChart3,
  Swords,
  BookOpen,
  Eye,
  Server,
} from 'lucide-react';
import { checkBackendHealth } from '../../services/api';

export type SectionId = 'overview' | 'assessment' | 'research' | 'arena' | 'methods' | 'bodylab' | 'risklab';

interface NavbarProps {
  activeSection: SectionId;
  onSelectSection: (section: SectionId) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeSection, onSelectSection }) => {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;
    const verifyHealth = async () => {
      const res = await checkBackendHealth();
      if (isMounted) {
        setBackendOnline(res.online);
      }
    };
    verifyHealth();
    const interval = setInterval(verifyHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const navItems: { id: SectionId; label: string; icon: React.ReactNode; isPrimary?: boolean }[] = [
    { id: 'overview', label: 'Overview', icon: <Eye size={16} /> },
    { id: 'assessment', label: 'Patient Assessment', icon: <Activity size={16} />, isPrimary: true },
    { id: 'research', label: 'Research Lab', icon: <BarChart3 size={16} /> },
    { id: 'arena', label: 'Model Arena', icon: <Swords size={16} /> },
    { id: 'methods', label: 'Methods & Limitations', icon: <BookOpen size={16} /> },
    { id: 'bodylab', label: 'Observatory', icon: <Layers size={16} /> },
  ];

  return (
    <header className="app-header">
      <div className="container flex items-center justify-between gap-6">
        {/* Brand Identity */}
        <div
          onClick={() => onSelectSection('overview')}
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '12px', userSelect: 'none' }}
        >
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #19166D 0%, #153568 100%)',
              border: '1px solid #A9D4E7',
              boxShadow: '0 0 14px rgba(169, 212, 231, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#A9D4E7',
            }}
          >
            <Activity size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.01em' }}>
                SUGAR
              </span>
              <span
                style={{
                  background: 'rgba(21, 53, 104, 0.6)',
                  border: '1px solid rgba(128, 179, 208, 0.35)',
                  color: '#80B3D0',
                  fontSize: '0.72rem',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontFamily: 'JetBrains Mono',
                  fontWeight: 600,
                }}
              >
                RESEARCH
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: '#80B3D0', margin: 0, lineHeight: 1.1 }}>
              Liver Fibrosis Research Platform
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {navItems.map((item) => {
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectSection(item.id)}
                className={`btn-tab ${isActive ? 'active' : ''}`}
              >
                <span style={{ color: isActive ? '#A9D4E7' : '#80B3D0' }}>{item.icon}</span>
                <span>{item.label}</span>
                {item.isPrimary && (
                  <span
                    style={{
                      fontSize: '0.65rem',
                      background: isActive ? 'rgba(169, 212, 231, 0.2)' : 'rgba(21, 53, 104, 0.6)',
                      color: isActive ? '#A9D4E7' : '#80B3D0',
                      border: '1px solid rgba(128, 179, 208, 0.3)',
                      padding: '1px 5px',
                      borderRadius: '4px',
                      fontFamily: 'JetBrains Mono',
                      fontWeight: 600,
                    }}
                  >
                    WORKFLOW
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Backend Status Telemetry */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              background: 'rgba(16, 16, 82, 0.65)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '6px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '0.8rem',
            }}
            title={
              backendOnline
                ? 'FastAPI server operational on http://localhost:8000'
                : 'FastAPI offline: using client-side validated research data'
            }
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: backendOnline ? '#34D399' : '#FBBF24',
                boxShadow: backendOnline ? '0 0 8px #34D399' : '0 0 8px #FBBF24',
              }}
            />
            <span style={{ fontFamily: 'JetBrains Mono', color: '#cbd5e1' }}>
              {backendOnline === null ? 'API: Checking' : backendOnline ? 'FastAPI: Live' : 'API: Standalone'}
            </span>
            <Server size={14} style={{ color: '#80B3D0' }} />
          </div>
        </div>
      </div>
    </header>
  );
};
