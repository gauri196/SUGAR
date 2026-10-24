// SUGAR — Polished Model Arena (Head-to-Head Cross-Validation Metrics & Honest Benchmarks)
import React, { useState } from 'react';
import {
  Swords,
  Award,
  BarChart,
} from 'lucide-react';
import {
  EXPERIMENT3_FOUR_MODEL_SUMMARY,
  FEATURE_IMPORTANCES,
} from '../../data/researchData';

export const ModelArena: React.FC = () => {
  const [selectedTarget, setSelectedTarget] = useState<'Target A' | 'Target B' | '4-Stage'>('Target A');

  const filteredExperiment3 = EXPERIMENT3_FOUR_MODEL_SUMMARY.filter((row) =>
    row.target.includes(selectedTarget)
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 pb-3 border-b border-[#153568]">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="h1 flex items-center gap-2">
              <Swords className="text-ice" size={26} />
              Model Arena: Experimental Benchmarks
            </h1>
            <span className="badge badge-ice">10-Fold Stratified Cross-Validation</span>
          </div>
          <p className="text-muted mt-1" style={{ fontSize: '0.92rem' }}>
            Uninflated evaluation comparing Routine Clinical Baseline vs. Expanded Machine Learning on the Egyptian HCV Cohort.
          </p>
        </div>

        {/* Target Filter Selector */}
        <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-surface)', padding: '4px', borderRadius: '8px', border: '1px solid var(--navy-clinical)' }}>
          <button
            onClick={() => setSelectedTarget('Target A')}
            className={`btn-tab ${selectedTarget === 'Target A' ? 'active' : ''}`}
          >
            Target A (Stage 1 vs 2-4)
          </button>
          <button
            onClick={() => setSelectedTarget('Target B')}
            className={`btn-tab ${selectedTarget === 'Target B' ? 'active' : ''}`}
          >
            Target B (Stages 1-2 vs 3-4)
          </button>
          <button
            onClick={() => setSelectedTarget('4-Stage')}
            className={`btn-tab ${selectedTarget === '4-Stage' ? 'active' : ''}`}
          >
            4-Stage Multiclass (F1–F4)
          </button>
        </div>
      </div>

      {/* Target A & B Benchmark Tables */}
      {selectedTarget !== '4-Stage' ? (
        <div className="sugar-card space-y-4">
          <div className="card-header flex items-center justify-between">
            <div>
              <h2 className="h2" style={{ fontSize: '1.2rem' }}>
                Cross-Validation Performance: {selectedTarget}
              </h2>
              <span style={{ fontSize: '0.84rem', color: '#80B3D0' }}>
                {selectedTarget === 'Target A'
                  ? 'Early Fibrosis (F1) vs. Intermediate/Advanced Fibrosis (F2–F4)'
                  : 'Mild/Moderate Fibrosis (F1–F2) vs. Advanced Fibrosis / Cirrhosis (F3–F4)'}
              </span>
            </div>
            <span className="badge badge-navy">outputs/experiment3_four_model_summary.csv</span>
          </div>

          <div className="sugar-table-container">
            <table className="sugar-table">
              <thead>
                <tr>
                  <th>Model Pipeline</th>
                  <th>Algorithm</th>
                  <th>Features Included</th>
                  <th>Accuracy</th>
                  <th>Precision</th>
                  <th>Sensitivity</th>
                  <th>Specificity</th>
                  <th>F1 Score</th>
                  <th>ROC-AUC</th>
                </tr>
              </thead>
              <tbody>
                {filteredExperiment3.map((row, idx) => (
                  <tr
                    key={idx}
                    className={row.model === 'Expanded' && row.algorithm === 'Random Forest' ? 'highlight' : ''}
                  >
                    <td style={{ fontWeight: 600, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {row.model === 'Expanded' && row.algorithm === 'Random Forest' && (
                        <Award size={14} style={{ color: '#A9D4E7' }} />
                      )}
                      <span>{row.model}</span>
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono', color: '#cbd5e1' }}>{row.algorithm}</td>
                    <td style={{ color: '#80B3D0', fontSize: '0.84rem' }}>{row.features}</td>
                    <td style={{ fontFamily: 'JetBrains Mono', fontWeight: 700, color: '#ffffff' }}>
                      {(row.accuracy * 100).toFixed(1)}%
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>{(row.precision * 100).toFixed(1)}%</td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>{(row.sensitivity * 100).toFixed(1)}%</td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>{(row.specificity * 100).toFixed(1)}%</td>
                    <td style={{ fontFamily: 'JetBrains Mono', color: '#ffffff' }}>{(row.f1 * 100).toFixed(1)}%</td>
                    <td style={{ fontFamily: 'JetBrains Mono', color: '#A9D4E7', fontWeight: 700 }}>
                      {row.roc_auc.toFixed(3)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ background: 'rgba(21, 53, 104, 0.35)', border: '1px solid var(--navy-clinical)', borderRadius: '8px', padding: '16px' }}>
            <strong style={{ color: '#A9D4E7', fontSize: '0.9rem', display: 'block', marginBottom: '4px' }}>
              Scientific Integrity Callout:
            </strong>
            <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: '1.55', margin: 0 }}>
              In Target A, the Expanded Random Forest yields <strong>64.5%</strong> accuracy and <strong>78.5%</strong> sensitivity. However, note that specificity drops to <strong>20.6%</strong> and ROC-AUC is <strong>0.475</strong> (near chance). This reflects class imbalance in the Egyptian cohort rather than true clinical discrimination. SUGAR surfaces this transparently rather than concealing low specificity behind raw accuracy.
            </p>
          </div>
        </div>
      ) : (
        /* 4-Stage Multiclass */
        <div className="sugar-card space-y-4">
          <div className="card-header flex items-center justify-between">
            <div>
              <h2 className="h2" style={{ fontSize: '1.2rem' }}>
                4-Stage Multiclass Classification (Metavir F1 vs. F2 vs. F3 vs. F4)
              </h2>
              <span style={{ fontSize: '0.84rem', color: '#80B3D0' }}>
                Direct experiment classifying each individual fibrosis stage from routine laboratory counts.
              </span>
            </div>
            <span className="badge badge-navy">outputs/experiment5_four_stage_summary.csv</span>
          </div>

          <div className="grid grid-3 gap-4">
            <div className="metric-box">
              <span className="metric-label">Random Forest (Expanded)</span>
              <div className="metric-value">24.4%</div>
              <span className="metric-subtext">Balanced Acc: 24.3% | AUC: 0.493</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Random Forest (Baseline)</span>
              <div className="metric-value">26.7%</div>
              <span className="metric-subtext">Balanced Acc: 26.6% | AUC: 0.513</span>
            </div>
            <div className="metric-box" style={{ borderColor: 'rgba(251, 191, 36, 0.4)' }}>
              <span className="metric-label" style={{ color: '#FBBF24' }}>Dummy Baseline (Random Guess)</span>
              <div className="metric-value" style={{ color: '#FBBF24' }}>26.2%</div>
              <span className="metric-subtext" style={{ color: '#CBD5E1' }}>Chance Floor (4 Balanced Stages)</span>
            </div>
          </div>

          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(248, 113, 113, 0.35)', borderRadius: '8px', padding: '16px' }}>
            <strong style={{ color: '#ffffff', fontSize: '0.9rem', display: 'block', marginBottom: '4px' }}>
              Scientific Proof of Non-Invasive Staging Boundaries:
            </strong>
            <p style={{ fontSize: '0.88rem', color: '#fca5a5', lineHeight: '1.55', margin: 0 }}>
              When attempting to classify four distinct Metavir stages directly from routine blood counts, machine learning models perform at <strong>~24–27%</strong>, exactly matching the random-guess dummy baseline (~25%). This demonstrates why multi-modal clinical diagnostic pathways (combining serology with vibration-controlled transient elastography or biopsy) are mandatory in modern hepatology.
            </p>
          </div>
        </div>
      )}

      {/* Feature Importance Panel */}
      <div className="sugar-card space-y-4">
        <div className="card-header flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart size={18} style={{ color: '#A9D4E7' }} />
            <h2 className="h2" style={{ fontSize: '1.15rem' }}>
              Random Forest Gini Feature Importances
            </h2>
          </div>
          <span className="badge badge-navy">models/metrics.json</span>
        </div>

        <div className="space-y-3">
          {FEATURE_IMPORTANCES.map((item, idx) => (
            <div key={idx} className="space-y-1">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.9rem' }}>
                <span style={{ fontWeight: 600, color: '#ffffff', fontFamily: 'JetBrains Mono', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: '#80B3D0', fontSize: '0.82rem' }}>#{idx + 1}</span>
                  <span>{item.feature}</span>
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <span style={{ fontSize: '0.84rem', color: '#80B3D0' }}>{item.description}</span>
                  <span style={{ fontFamily: 'JetBrains Mono', color: '#A9D4E7', fontWeight: 700 }}>
                    {(item.importance * 100).toFixed(2)}%
                  </span>
                </div>
              </div>

              <div style={{ width: '100%', height: '8px', borderRadius: '4px', background: 'var(--navy-deep)', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${item.importance * 100 * 5.5}%`,
                    height: '100%',
                    background: idx < 3
                      ? 'linear-gradient(90deg, #19166D 0%, #A9D4E7 100%)'
                      : 'linear-gradient(90deg, #153568 0%, #80B3D0 100%)',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
