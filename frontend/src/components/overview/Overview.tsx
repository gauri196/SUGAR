// SUGAR — Liver Fibrosis Research Platform: Cinematic Homepage
import React, { useEffect, useRef } from 'react';
import {
  Activity,
  BarChart3,
  Swords,
  BookOpen,
  ArrowRight,
  FlaskConical,
  TrendingUp,
  AlertTriangle,
  Layers,
} from 'lucide-react';
import { SectionId } from '../layout/Navbar';

interface OverviewProps {
  onNavigate: (section: SectionId) => void;
}

// Animated SVG Liver Visualization — stylized hepatic anatomy with fibrosis gradient
const LiverVisualization: React.FC = () => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    // Subtle pulse animation on fibrosis zones
    const zones = svg.querySelectorAll('.fibrosis-zone');
    let t = 0;
    const tick = () => {
      t += 0.02;
      zones.forEach((z, i) => {
        const el = z as SVGElement;
        const base = 0.18 + i * 0.06;
        el.style.opacity = String(base + Math.sin(t + i * 1.1) * 0.06);
      });
      requestAnimationFrame(tick);
    };
    const id = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(id);
  }, []);

  return (
    <svg
      ref={svgRef}
      viewBox="0 0 420 300"
      xmlns="http://www.w3.org/2000/svg"
      style={{ width: '100%', height: '100%', maxHeight: '300px' }}
      aria-label="Stylized liver anatomy with fibrosis staging overlay"
    >
      <defs>
        {/* Hepatic tissue gradient — warm brownish-red natural liver color */}
        <radialGradient id="liverGrad" cx="42%" cy="45%" r="55%">
          <stop offset="0%" stopColor="#9b3a2e" stopOpacity="0.95" />
          <stop offset="45%" stopColor="#7a2c22" stopOpacity="0.95" />
          <stop offset="100%" stopColor="#5a1e18" stopOpacity="0.85" />
        </radialGradient>

        {/* Fibrosis progression gradient — cold blue advancing from right */}
        <linearGradient id="fibrosisGrad" x1="100%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#19166d" stopOpacity="0.0" />
          <stop offset="60%" stopColor="#153568" stopOpacity="0.45" />
          <stop offset="100%" stopColor="#101052" stopOpacity="0.75" />
        </linearGradient>

        {/* Surface gloss */}
        <radialGradient id="glossGrad" cx="35%" cy="28%" r="40%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.12" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0.0" />
        </radialGradient>

        {/* Glow filter */}
        <filter id="softGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="6" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        {/* Vessel glow */}
        <filter id="vesselGlow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        {/* Clip path to the liver shape */}
        <clipPath id="liverClip">
          <path d="
            M 60 145
            C 58 100, 72 65, 105 55
            C 130 48, 155 52, 185 58
            C 210 40, 250 35, 290 45
            C 335 55, 360 80, 362 115
            C 365 150, 345 175, 315 188
            C 285 200, 245 205, 210 200
            C 195 215, 175 225, 155 225
            C 120 225, 92 215, 75 195
            C 62 178, 62 162, 60 145 Z
          " />
        </clipPath>
      </defs>

      {/* Background organ glow */}
      <ellipse cx="211" cy="135" rx="170" ry="100" fill="#7a2c22" opacity="0.08" filter="url(#softGlow)" />

      {/* Main liver body */}
      <path
        d="
          M 60 145
          C 58 100, 72 65, 105 55
          C 130 48, 155 52, 185 58
          C 210 40, 250 35, 290 45
          C 335 55, 360 80, 362 115
          C 365 150, 345 175, 315 188
          C 285 200, 245 205, 210 200
          C 195 215, 175 225, 155 225
          C 120 225, 92 215, 75 195
          C 62 178, 62 162, 60 145 Z
        "
        fill="url(#liverGrad)"
        stroke="#c1564a"
        strokeWidth="1.5"
        strokeOpacity="0.6"
      />

      {/* Fibrosis progression overlay (Glisson capsule fibrosis pattern) */}
      <path
        className="fibrosis-zone"
        d="
          M 60 145 C 58 100, 72 65, 105 55 C 130 48, 155 52, 185 58
          C 210 40, 250 35, 290 45 C 335 55, 360 80, 362 115
          C 365 150, 345 175, 315 188 C 285 200, 245 205, 210 200
          C 195 215, 175 225, 155 225 C 120 225, 92 215, 75 195
          C 62 178, 62 162, 60 145 Z
        "
        fill="url(#fibrosisGrad)"
        clipPath="url(#liverClip)"
        style={{ transition: 'opacity 0.4s ease' }}
      />

      {/* Gloss highlight */}
      <path
        d="
          M 60 145 C 58 100, 72 65, 105 55 C 130 48, 155 52, 185 58
          C 210 40, 250 35, 290 45 C 335 55, 360 80, 362 115
          C 365 150, 345 175, 315 188 C 285 200, 245 205, 210 200
          C 195 215, 175 225, 155 225 C 120 225, 92 215, 75 195
          C 62 178, 62 162, 60 145 Z
        "
        fill="url(#glossGrad)"
        clipPath="url(#liverClip)"
      />

      {/* Internal lobule structure lines (hepatic architecture) */}
      <g clipPath="url(#liverClip)" opacity="0.18" stroke="#c1564a" strokeWidth="0.8" fill="none">
        <line x1="130" y1="60" x2="115" y2="210" />
        <line x1="185" y1="55" x2="165" y2="215" />
        <line x1="240" y1="45" x2="220" y2="198" />
        <line x1="295" y1="50" x2="275" y2="195" />
        <line x1="80" y1="85" x2="340" y2="110" />
        <line x1="75" y1="135" x2="355" y2="145" />
        <line x1="80" y1="175" x2="310" y2="185" />
      </g>

      {/* Portal vein (main trunk) */}
      <path
        d="M 175 225 C 180 240, 190 255, 210 262"
        fill="none"
        stroke="#80b3d0"
        strokeWidth="4"
        strokeLinecap="round"
        filter="url(#vesselGlow)"
        opacity="0.7"
      />

      {/* Hepatic veins branching */}
      <g fill="none" stroke="#a9d4e7" strokeLinecap="round" filter="url(#vesselGlow)" opacity="0.55">
        <path d="M 290 75 C 300 95, 310 110, 318 130" strokeWidth="2.5" />
        <path d="M 318 130 C 325 148, 322 165, 312 180" strokeWidth="2" />
        <path d="M 200 75 C 210 95, 215 115, 212 135" strokeWidth="2" />
        <path d="M 140 75 C 145 95, 148 115, 145 138" strokeWidth="1.8" />
        <path d="M 95 100 C 100 120, 102 140, 98 158" strokeWidth="1.5" />
      </g>

      {/* Fibrosis zone markers */}
      {/* F1 zone label */}
      <circle cx="108" cy="128" r="14" fill="#19166d" fillOpacity="0.7" stroke="#80b3d0" strokeWidth="1" className="fibrosis-zone" />
      <text x="108" y="133" textAnchor="middle" fill="#a9d4e7" fontSize="10" fontWeight="700" fontFamily="JetBrains Mono, monospace">F1</text>

      {/* F2 zone label */}
      <circle cx="185" cy="105" r="14" fill="#153568" fillOpacity="0.75" stroke="#80b3d0" strokeWidth="1" className="fibrosis-zone" />
      <text x="185" y="110" textAnchor="middle" fill="#a9d4e7" fontSize="10" fontWeight="700" fontFamily="JetBrains Mono, monospace">F2</text>

      {/* F3 zone label */}
      <circle cx="262" cy="108" r="14" fill="#153568" fillOpacity="0.85" stroke="#a9d4e7" strokeWidth="1.2" className="fibrosis-zone" />
      <text x="262" y="113" textAnchor="middle" fill="#ffffff" fontSize="10" fontWeight="700" fontFamily="JetBrains Mono, monospace">F3</text>

      {/* F4 zone label */}
      <circle cx="328" cy="140" r="14" fill="#101052" fillOpacity="0.9" stroke="#a9d4e7" strokeWidth="1.5" className="fibrosis-zone" />
      <text x="328" y="145" textAnchor="middle" fill="#ffffff" fontSize="10" fontWeight="700" fontFamily="JetBrains Mono, monospace">F4</text>

      {/* Liver outline rim highlight */}
      <path
        d="
          M 60 145
          C 58 100, 72 65, 105 55
          C 130 48, 155 52, 185 58
          C 210 40, 250 35, 290 45
          C 335 55, 360 80, 362 115
          C 365 150, 345 175, 315 188
          C 285 200, 245 205, 210 200
          C 195 215, 175 225, 155 225
          C 120 225, 92 215, 75 195
          C 62 178, 62 162, 60 145 Z
        "
        fill="none"
        stroke="#a9d4e7"
        strokeWidth="1"
        strokeOpacity="0.35"
      />

      {/* Gallbladder */}
      <ellipse cx="172" cy="218" rx="18" ry="12" fill="#5a7e42" fillOpacity="0.75" stroke="#80b3d0" strokeWidth="0.8" strokeOpacity="0.5" />
      <text x="172" y="222" textAnchor="middle" fill="#a9d4e7" fontSize="7.5" fontFamily="Inter, sans-serif" opacity="0.8">GB</text>

      {/* VCTE measurement indicator */}
      <g transform="translate(60, 255)">
        <rect x="0" y="0" width="130" height="28" rx="5" fill="#0a0e1c" fillOpacity="0.85" stroke="#153568" strokeWidth="1" />
        <circle cx="12" cy="14" r="4" fill="#a9d4e7" opacity="0.9" />
        <text x="22" y="18" fill="#cbd5e1" fontSize="9" fontFamily="JetBrains Mono, monospace">VCTE: kPa (stiffness)</text>
      </g>

      {/* FIB-4 annotation */}
      <g transform="translate(218, 255)">
        <rect x="0" y="0" width="130" height="28" rx="5" fill="#0a0e1c" fillOpacity="0.85" stroke="#19166d" strokeWidth="1" />
        <circle cx="12" cy="14" r="4" fill="#80b3d0" opacity="0.9" />
        <text x="22" y="18" fill="#cbd5e1" fontSize="9" fontFamily="JetBrains Mono, monospace">FIB-4 = AST×Age/PLT×√ALT</text>
      </g>
    </svg>
  );
};

// Inline fibrosis stage progression bar
const FibrosisProgressBar: React.FC = () => {
  const stages = [
    { label: 'F0', desc: 'No Fibrosis', color: '#34d399', pct: 0 },
    { label: 'F1', desc: 'Mild', color: '#80b3d0', pct: 25 },
    { label: 'F2', desc: 'Moderate', color: '#fbbf24', pct: 50 },
    { label: 'F3', desc: 'Severe', color: '#f97316', pct: 75 },
    { label: 'F4', desc: 'Cirrhosis', color: '#f87171', pct: 100 },
  ];
  return (
    <div style={{ padding: '16px 20px', background: 'rgba(10,14,28,0.7)', border: '1px solid var(--navy-clinical)', borderRadius: '10px' }}>
      <div style={{ fontSize: '0.78rem', color: 'var(--steel-blue)', textTransform: 'uppercase', letterSpacing: '0.07em', fontWeight: 600, marginBottom: '10px', fontFamily: 'JetBrains Mono, monospace' }}>
        Metavir Fibrosis Staging (Biopsy Reference)
      </div>
      <div style={{ display: 'flex', gap: 0, borderRadius: '6px', overflow: 'hidden', height: '10px', marginBottom: '8px' }}>
        {stages.map((s, i) => (
          <div key={i} style={{ flex: 1, background: s.color, opacity: 0.75 + i * 0.04 }} />
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        {stages.map((s, i) => (
          <div key={i} style={{ textAlign: 'center', flex: 1 }}>
            <div style={{ fontSize: '0.82rem', fontWeight: 700, color: s.color, fontFamily: 'JetBrains Mono, monospace' }}>{s.label}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.2 }}>{s.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const Overview: React.FC<OverviewProps> = ({ onNavigate }) => {
  return (
    <div className="space-y-8">

      {/* ═══════════════════════════════════════════════════════ */}
      {/* HERO — Cinematic two-column liver fibrosis composition  */}
      {/* ═══════════════════════════════════════════════════════ */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 420px',
          gap: '40px',
          alignItems: 'center',
          background: 'radial-gradient(ellipse at 15% 40%, rgba(25, 22, 109, 0.38) 0%, rgba(10, 14, 28, 0.96) 65%)',
          border: '1px solid var(--border-active)',
          borderRadius: '16px',
          padding: '44px 40px',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.6)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Decorative background glow */}
        <div style={{
          position: 'absolute', right: '380px', top: '50%', transform: 'translateY(-50%)',
          width: '300px', height: '300px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(154, 58, 46, 0.07) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        {/* LEFT: Text narrative */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              style={{
                background: 'rgba(21, 53, 104, 0.7)',
                border: '1px solid var(--border-active)',
                color: 'var(--ice-blue)',
                fontSize: '0.78rem',
                padding: '4px 12px',
                borderRadius: '20px',
                fontFamily: 'JetBrains Mono, monospace',
                fontWeight: 600,
                letterSpacing: '0.05em',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <FlaskConical size={13} />
              Research Prototype · Non-Clinical
            </span>
          </div>

          <div>
            <h1
              style={{
                fontSize: '2.6rem',
                fontWeight: 800,
                color: '#ffffff',
                lineHeight: 1.15,
                letterSpacing: '-0.025em',
                margin: 0,
              }}
            >
              Liver Fibrosis
              <br />
              <span style={{ color: 'var(--ice-blue)' }}>Research Platform</span>
            </h1>
            <p
              style={{
                marginTop: '16px',
                fontSize: '1.05rem',
                color: '#cbd5e1',
                lineHeight: 1.65,
                maxWidth: '520px',
              }}
            >
              SUGAR investigates hepatic fibrosis assessment through FIB-4 biomarker analysis,
              machine-learning staging models, and epidemiological liver stiffness data — validated
              against <strong style={{ color: '#ffffff' }}>7,211 NHANES elastography exams</strong> and
              an <strong style={{ color: '#ffffff' }}>Egyptian HCV cohort (N=1,385)</strong>.
            </p>
          </div>

          {/* Research evidence callout — actual findings */}
          <div
            style={{
              background: 'rgba(16, 16, 82, 0.5)',
              border: '1px solid rgba(128, 179, 208, 0.25)',
              borderLeft: '3px solid var(--ice-blue)',
              borderRadius: '8px',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
            }}
          >
            <TrendingUp size={18} style={{ color: 'var(--ice-blue)', flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontSize: '0.88rem', color: '#ffffff', fontWeight: 600, marginBottom: '2px' }}>
                Key Epidemiological Finding
              </div>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                FIB-4 shows a statistically significant but <em>weak</em> association with VCTE liver
                stiffness (ρ = 0.122, p = 3.17×10⁻²⁵). Stiffness alone explains only ~3% of FIB-4
                variance — underscoring their complementary, not interchangeable, roles.
              </p>
            </div>
          </div>

          {/* Disclaimer note */}
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '8px',
              background: 'rgba(251, 191, 36, 0.06)',
              border: '1px solid rgba(251, 191, 36, 0.2)',
              borderRadius: '8px',
              padding: '10px 14px',
            }}
          >
            <AlertTriangle size={15} style={{ color: '#fbbf24', flexShrink: 0, marginTop: '2px' }} />
            <p style={{ margin: 0, fontSize: '0.82rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Not a clinical diagnostic tool. Results derive from retrospective population-level data
              and must not substitute liver biopsy or specialist interpretation.
            </p>
          </div>

          {/* Primary CTAs */}
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              onClick={() => onNavigate('risklab')}
              className="btn btn-primary"
              id="cta-risklab"
              style={{ padding: '12px 24px', fontSize: '0.95rem' }}
            >
              <Activity size={18} />
              <span>Fibrosis Assessment</span>
              <ArrowRight size={15} />
            </button>
            <button
              onClick={() => onNavigate('research')}
              className="btn btn-secondary"
              id="cta-research"
              style={{ padding: '12px 24px', fontSize: '0.95rem' }}
            >
              <BarChart3 size={18} />
              <span>Research Evidence</span>
            </button>
          </div>
        </div>

        {/* RIGHT: Liver visualization */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div
            style={{
              background: 'radial-gradient(ellipse at 50% 50%, rgba(90, 30, 24, 0.15) 0%, rgba(7, 10, 20, 0.5) 70%)',
              border: '1px solid rgba(154, 58, 46, 0.25)',
              borderRadius: '12px',
              padding: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <LiverVisualization />
          </div>

          {/* Fibrosis staging reference bar */}
          <FibrosisProgressBar />
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* RESEARCH NARRATIVE — 3 key evidence cards (non-KPI)   */}
      {/* ═══════════════════════════════════════════════════════ */}
      <div>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#ffffff', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FlaskConical size={18} style={{ color: 'var(--ice-blue)' }} />
          Research Evidence at a Glance
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          {/* Evidence card 1 */}
          <div
            style={{
              background: 'rgba(10,14,28,0.82)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: 'var(--steel-blue)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'JetBrains Mono, monospace' }}>
              NHANES Cohort · N=7,211
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff', fontFamily: 'JetBrains Mono, monospace', lineHeight: 1 }}>
              ρ = 0.122
            </div>
            <div style={{ fontSize: '0.82rem', color: '#34d399', fontFamily: 'JetBrains Mono, monospace' }}>
              p = 3.17×10⁻²⁵
            </div>
            <p style={{ margin: 0, fontSize: '0.86rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Spearman rank correlation between FIB-4 and VCTE liver stiffness (kPa). Significant
              but modest — reflecting different measurement constructs.
            </p>
          </div>

          {/* Evidence card 2 */}
          <div
            style={{
              background: 'rgba(10,14,28,0.82)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: 'var(--steel-blue)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'JetBrains Mono, monospace' }}>
              Egyptian HCV · N=1,385
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff', fontFamily: 'JetBrains Mono, monospace', lineHeight: 1 }}>
              AUC 0.69
            </div>
            <div style={{ fontSize: '0.82rem', color: '#fbbf24', fontFamily: 'JetBrains Mono, monospace' }}>
              Expanded RF · Target A
            </div>
            <p style={{ margin: 0, fontSize: '0.86rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Best performing model (Expanded Random Forest) for Stage 1 vs. 2–4 classification.
              Modest performance consistent with clinical complexity.
            </p>
          </div>

          {/* Evidence card 3 */}
          <div
            style={{
              background: 'rgba(10,14,28,0.82)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: 'var(--steel-blue)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'JetBrains Mono, monospace' }}>
              FIB-4 Index · Cross-cohort
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff', fontFamily: 'JetBrains Mono, monospace', lineHeight: 1 }}>
              ~3%
            </div>
            <div style={{ fontSize: '0.82rem', color: '#a9d4e7', fontFamily: 'JetBrains Mono, monospace' }}>
              Explained variance (R²)
            </div>
            <p style={{ margin: 0, fontSize: '0.86rem', color: '#94a3b8', lineHeight: 1.5 }}>
              FIB-4 alone explains only ~3% of liver stiffness variance in adjusted OLS models.
              Age contributes independently, reinforcing age-stratified interpretation.
            </p>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* MODULE NAVIGATION — compact, purpose-first labels     */}
      {/* ═══════════════════════════════════════════════════════ */}
      <div>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#ffffff', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={18} style={{ color: 'var(--ice-blue)' }} />
          Research Modules
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px' }}>
          {/* Risk Stratification Lab — PRIMARY */}
          <div
            onClick={() => onNavigate('risklab')}
            id="nav-risklab"
            style={{
              cursor: 'pointer',
              background: 'linear-gradient(135deg, rgba(25, 22, 109, 0.5) 0%, rgba(10, 14, 28, 0.9) 100%)',
              border: '1px solid var(--border-active)',
              borderRadius: '12px',
              padding: '22px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '16px',
              transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
              gridColumn: 'span 2',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--ice-blue)';
              (e.currentTarget as HTMLDivElement).style.boxShadow = '0 0 20px rgba(169,212,231,0.12)';
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-active)';
              (e.currentTarget as HTMLDivElement).style.boxShadow = 'none';
            }}
          >
            <div style={{ background: 'rgba(21,53,104,0.7)', border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '10px', flexShrink: 0 }}>
              <Activity size={22} style={{ color: 'var(--ice-blue)' }} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#ffffff', fontWeight: 600 }}>Risk Stratification Lab</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--ice-blue)', background: 'rgba(25,22,109,0.6)', border: '1px solid var(--border-active)', padding: '2px 8px', borderRadius: '12px', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600 }}>Primary</span>
              </div>
              <p style={{ margin: 0, fontSize: '0.9rem', color: '#94a3b8', lineHeight: 1.55 }}>
                Enter patient biomarkers, compute real-time FIB-4 index, and compare Baseline Logistic Regression
                vs. Expanded Random Forest predictions from the FastAPI backend — with full transparency on inputs
                and limitations.
              </p>
            </div>
            <ArrowRight size={18} style={{ color: 'var(--steel-blue)', flexShrink: 0, marginTop: '4px' }} />
          </div>

          {/* Research Lab */}
          <div
            onClick={() => onNavigate('research')}
            id="nav-research"
            style={{
              cursor: 'pointer',
              background: 'rgba(10,14,28,0.82)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '20px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '14px',
              transition: 'border-color 0.15s ease',
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(128,179,208,0.45)'; }}
            onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-subtle)'; }}
          >
            <div style={{ background: 'rgba(16,16,82,0.6)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '8px', flexShrink: 0 }}>
              <BarChart3 size={20} style={{ color: 'var(--ice-blue)' }} />
            </div>
            <div>
              <h3 style={{ margin: '0 0 4px', fontSize: '1rem', color: '#ffffff', fontWeight: 600 }}>Research Lab: NHANES</h3>
              <p style={{ margin: 0, fontSize: '0.86rem', color: '#94a3b8', lineHeight: 1.5 }}>
                Epidemiological analysis — Spearman correlations, age-stratified trends, and
                multivariable OLS regressions from 7,211 VCTE exams.
              </p>
            </div>
          </div>

          {/* Model Arena */}
          <div
            onClick={() => onNavigate('arena')}
            id="nav-arena"
            style={{
              cursor: 'pointer',
              background: 'rgba(10,14,28,0.82)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '20px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '14px',
              transition: 'border-color 0.15s ease',
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(128,179,208,0.45)'; }}
            onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-subtle)'; }}
          >
            <div style={{ background: 'rgba(16,16,82,0.6)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '8px', flexShrink: 0 }}>
              <Swords size={20} style={{ color: 'var(--ice-blue)' }} />
            </div>
            <div>
              <h3 style={{ margin: '0 0 4px', fontSize: '1rem', color: '#ffffff', fontWeight: 600 }}>Model Arena</h3>
              <p style={{ margin: 0, fontSize: '0.86rem', color: '#94a3b8', lineHeight: 1.5 }}>
                10-fold cross-validation benchmarks — Baseline vs. Expanded RF on Target A, Target B,
                and 4-stage Metavir classification.
              </p>
            </div>
          </div>

          {/* Methods & Limitations */}
          <div
            onClick={() => onNavigate('methods')}
            id="nav-methods"
            style={{
              cursor: 'pointer',
              background: 'rgba(10,14,28,0.82)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '20px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '14px',
              transition: 'border-color 0.15s ease',
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(128,179,208,0.45)'; }}
            onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-subtle)'; }}
          >
            <div style={{ background: 'rgba(16,16,82,0.6)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '8px', flexShrink: 0 }}>
              <BookOpen size={20} style={{ color: 'var(--ice-blue)' }} />
            </div>
            <div>
              <h3 style={{ margin: '0 0 4px', fontSize: '1rem', color: '#ffffff', fontWeight: 600 }}>Methods & Limitations</h3>
              <p style={{ margin: 0, fontSize: '0.86rem', color: '#94a3b8', lineHeight: 1.5 }}>
                Data provenance, stiffness-vs-biopsy distinction, class imbalance caveats, and
                full non-diagnostic research prototype disclosure.
              </p>
            </div>
          </div>

          {/* Human Systems Observatory — secondary/supporting */}
          <div
            onClick={() => onNavigate('bodylab')}
            id="nav-bodylab"
            style={{
              cursor: 'pointer',
              background: 'rgba(10,14,28,0.82)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '20px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '14px',
              transition: 'border-color 0.15s ease',
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(128,179,208,0.45)'; }}
            onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-subtle)'; }}
          >
            <div style={{ background: 'rgba(16,16,82,0.6)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '8px', flexShrink: 0 }}>
              <Layers size={20} style={{ color: 'var(--steel-blue)' }} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <h3 style={{ margin: 0, fontSize: '1rem', color: '#ffffff', fontWeight: 600 }}>Human Systems Observatory</h3>
                <span style={{ fontSize: '0.72rem', color: 'var(--steel-blue)', background: 'rgba(16,16,82,0.5)', border: '1px solid var(--border-subtle)', padding: '2px 7px', borderRadius: '10px', fontFamily: 'JetBrains Mono, monospace' }}>Supporting</span>
              </div>
              <p style={{ margin: 0, fontSize: '0.86rem', color: '#94a3b8', lineHeight: 1.5 }}>
                Interactive 3D anatomy viewer — click organs to explore clinical biomarkers and
                liver-fibrosis anatomical context.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
