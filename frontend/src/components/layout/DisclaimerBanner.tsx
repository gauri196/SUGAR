// SUGAR — Compact, Legible Scientific Disclaimer Banner
import React from 'react';
import { ShieldAlert, Info } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <aside
      aria-label="Scientific and Regulatory Disclaimer"
      style={{
        background: 'linear-gradient(90deg, #101052 0%, #153568 100%)',
        borderBottom: '1px solid rgba(169, 212, 231, 0.25)',
      }}
      className="disclaimer-strip"
    >
      <div className="container flex items-center justify-between gap-4 py-1.5">
        <div className="flex items-center gap-3">
          <span
            style={{
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(248, 113, 113, 0.4)',
              color: '#FCA5A5',
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '0.75rem',
              fontWeight: 600,
              letterSpacing: '0.04em',
            }}
            className="flex items-center gap-1.5 flex-shrink-0 font-mono uppercase"
          >
            <ShieldAlert size={13} />
            Research Prototype Only
          </span>

          <p style={{ fontSize: '0.84rem', margin: 0 }} className="text-secondary leading-normal">
            <strong className="text-white">Non-Diagnostic Tool:</strong> SUGAR is an investigational decision-support prototype. It does not provide medical diagnoses or replace clinical staging. Liver stiffness (kPa) reflects physical elastography shear wave speed and is strictly distinguished from histological biopsy Metavir staging (F0–F4).
          </p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <a
            href="#methods"
            style={{ fontSize: '0.82rem', color: '#A9D4E7' }}
            className="flex items-center gap-1 hover:underline"
          >
            <Info size={13} />
            <span>Methodology & Caveats</span>
          </a>
        </div>
      </div>
    </aside>
  );
};
