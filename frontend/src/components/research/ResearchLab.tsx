// SUGAR — Polished Research Lab (NHANES 2017–2020 Elastography Cohort Analysis)
import React, { useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Database,
  Info,
} from 'lucide-react';
import {
  NHANES_OVERALL_ASSOCIATION,
  NHANES_AGE_GROUP_SUMMARY,
  NHANES_ADJUSTED_MODELS,
  NHANES_FAIR_MODEL_COMPARISON,
} from '../../data/researchData';

export const ResearchLab: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'association' | 'age' | 'regression' | 'test_eval'>('association');

  return (
    <div className="space-y-6">
      {/* Lab Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 pb-3 border-b border-[#153568]">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="h1 flex items-center gap-2">
              <BarChart3 className="text-ice" size={26} />
              Research Lab: NHANES Elastography
            </h1>
            <span className="badge badge-ice">7,211 Adult Participants</span>
          </div>
          <p className="text-muted mt-1" style={{ fontSize: '0.92rem' }}>
            Epidemiological analysis investigating blood-based FIB-4 against vibration-controlled transient elastography (VCTE) liver stiffness (kPa).
          </p>
        </div>

        {/* Sub-Tabs */}
        <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-surface)', padding: '4px', borderRadius: '8px', border: '1px solid var(--navy-clinical)' }}>
          <button
            onClick={() => setActiveTab('association')}
            className={`btn-tab ${activeTab === 'association' ? 'active' : ''}`}
          >
            Overall Association
          </button>
          <button
            onClick={() => setActiveTab('age')}
            className={`btn-tab ${activeTab === 'age' ? 'active' : ''}`}
          >
            Age Stratification
          </button>
          <button
            onClick={() => setActiveTab('regression')}
            className={`btn-tab ${activeTab === 'regression' ? 'active' : ''}`}
          >
            Adjusted Regressions
          </button>
          <button
            onClick={() => setActiveTab('test_eval')}
            className={`btn-tab ${activeTab === 'test_eval' ? 'active' : ''}`}
          >
            Holdout Test Benchmarks
          </button>
        </div>
      </div>

      {/* Primary Metrics Strip */}
      <div className="grid grid-4 gap-4">
        <div className="metric-box">
          <span className="metric-label">Cohort Sample Size</span>
          <div className="metric-value">{NHANES_OVERALL_ASSOCIATION.participants.toLocaleString()}</div>
          <span className="metric-subtext">Complete VCTE Exams (2017–2020)</span>
        </div>

        <div className="metric-box">
          <span className="metric-label">Spearman Rank Correlation (ρ)</span>
          <div className="metric-value" style={{ color: '#A9D4E7' }}>+0.1218</div>
          <span className="metric-subtext" style={{ color: '#34D399' }}>p = 3.17 × 10⁻²⁵</span>
        </div>

        <div className="metric-box">
          <span className="metric-label">Pearson Linear Correlation (r)</span>
          <div className="metric-value" style={{ color: '#A9D4E7' }}>+0.1648</div>
          <span className="metric-subtext" style={{ color: '#34D399' }}>p = 4.41 × 10⁻⁴⁵</span>
        </div>

        <div className="metric-box">
          <span className="metric-label">Multivariable Model 3 (R²)</span>
          <div className="metric-value">13.00%</div>
          <span className="metric-subtext">FIB-4 + Age + Sex + CAP Steatosis</span>
        </div>
      </div>

      {/* Tab 1: Overall Association */}
      {activeTab === 'association' && (
        <div className="grid grid-12 gap-6">
          <div className="col-span-7 sugar-card space-y-4">
            <h2 className="h2 flex items-center gap-2" style={{ fontSize: '1.2rem' }}>
              <TrendingUp size={20} style={{ color: '#A9D4E7' }} />
              <span>Statistical Correlation: FIB-4 vs. Physical Liver Stiffness</span>
            </h2>

            <p style={{ fontSize: '0.92rem', color: '#cbd5e1', lineHeight: '1.6' }}>
              In the 2017–March 2020 pre-pandemic NHANES cycle, transient elastography was administered using FibroScan® technology to record continuous liver stiffness (shear wave speed, measured in kilopascals, kPa).
            </p>

            <div className="grid grid-2 gap-4 pt-2">
              <div style={{ background: 'rgba(16, 16, 82, 0.5)', border: '1px solid var(--navy-clinical)', borderRadius: '8px', padding: '16px' }}>
                <span style={{ fontSize: '0.78rem', color: '#80B3D0', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '4px' }}>
                  Non-Parametric Spearman Rank
                </span>
                <div style={{ fontSize: '1.6rem', fontWeight: 700, fontFamily: 'JetBrains Mono', color: '#ffffff' }}>
                  ρ = 0.1218
                </div>
                <span style={{ fontSize: '0.82rem', color: '#34D399', fontFamily: 'JetBrains Mono', marginTop: '4px', display: 'block' }}>
                  Statistically Significant (p &lt; 10⁻²⁴)
                </span>
              </div>

              <div style={{ background: 'rgba(16, 16, 82, 0.5)', border: '1px solid var(--navy-clinical)', borderRadius: '8px', padding: '16px' }}>
                <span style={{ fontSize: '0.78rem', color: '#80B3D0', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '4px' }}>
                  Parametric Pearson Coefficient
                </span>
                <div style={{ fontSize: '1.6rem', fontWeight: 700, fontFamily: 'JetBrains Mono', color: '#ffffff' }}>
                  r = 0.1648
                </div>
                <span style={{ fontSize: '0.82rem', color: '#34D399', fontFamily: 'JetBrains Mono', marginTop: '4px', display: 'block' }}>
                  Statistically Significant (p &lt; 10⁻⁴⁴)
                </span>
              </div>
            </div>

            <div style={{ background: 'rgba(25, 22, 109, 0.25)', border: '1px solid var(--navy-clinical)', borderRadius: '8px', padding: '16px', marginTop: '16px' }}>
              <h4 style={{ fontSize: '0.9rem', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Info size={14} />
                Epidemiological Interpretation
              </h4>
              <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: '1.55', margin: 0 }}>
                While the correlation between standard blood-based FIB-4 and physical ultrasound stiffness is statistically confirmed (p &lt; 10⁻²⁴), the effect size is modest (ρ ≈ 0.12). Blood-based indices explain only a fraction of continuous liver stiffness variance in an unselected general population.
              </p>
            </div>
          </div>

          <div className="col-span-5 sugar-card-elevated space-y-4">
            <h2 className="h2 flex items-center gap-2" style={{ fontSize: '1.2rem' }}>
              <Database size={20} style={{ color: '#A9D4E7' }} />
              <span>Cohort Data Provenance</span>
            </h2>

            <div className="space-y-3">
              <div style={{ background: 'rgba(7, 10, 20, 0.7)', border: '1px solid var(--navy-clinical)', borderRadius: '8px', padding: '12px' }}>
                <strong style={{ color: '#ffffff', fontSize: '0.9rem', display: 'block' }}>CDC / NCHS NHANES Study Cycle</strong>
                <span style={{ fontSize: '0.82rem', color: '#80B3D0' }}>Pre-pandemic cycle (2017 to March 2020)</span>
              </div>

              <div style={{ background: 'rgba(7, 10, 20, 0.7)', border: '1px solid var(--navy-clinical)', borderRadius: '8px', padding: '12px' }}>
                <strong style={{ color: '#ffffff', fontSize: '0.9rem', display: 'block' }}>Merged XPT Examination Files</strong>
                <code style={{ fontSize: '0.8rem', color: '#A9D4E7' }}>P_DEMO.xpt, P_BIOPRO.xpt, P_CBC.xpt, P_LUX.xpt</code>
              </div>

              <div style={{ background: 'rgba(7, 10, 20, 0.7)', border: '1px solid var(--navy-clinical)', borderRadius: '8px', padding: '12px' }}>
                <strong style={{ color: '#ffffff', fontSize: '0.9rem', display: 'block' }}>Quality Inclusions</strong>
                <span style={{ fontSize: '0.82rem', color: '#80B3D0' }}>Adults ≥18 with valid elastography flags and recorded FIB-4 inputs.</span>
              </div>

              <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(248, 113, 113, 0.35)', borderRadius: '8px', padding: '14px', color: '#fca5a5', fontSize: '0.84rem' }}>
                <strong style={{ display: 'block', marginBottom: '2px', color: '#ffffff' }}>Crucial Scientific Distinction:</strong>
                Liver stiffness in kPa measures acoustic shear wave propagation. It is a continuous physical tissue biomarker and is strictly distinguished from histological biopsy Metavir staging.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Age Stratification */}
      {activeTab === 'age' && (
        <div className="sugar-card space-y-4">
          <div className="card-header flex items-center justify-between">
            <div>
              <h2 className="h2" style={{ fontSize: '1.2rem' }}>
                Age Bracket Stratification ({NHANES_AGE_GROUP_SUMMARY.length} Age Cohorts)
              </h2>
              <span style={{ fontSize: '0.84rem', color: '#80B3D0' }}>
                Exploring why FIB-4 climbs exponentially with age while general population stiffness remains relatively stable.
              </span>
            </div>
            <span className="badge badge-navy">outputs/nhanes_8e_age_group_summary.csv</span>
          </div>

          <div className="sugar-table-container">
            <table className="sugar-table">
              <thead>
                <tr>
                  <th>Age Bracket</th>
                  <th>Participants (N)</th>
                  <th>Median FIB-4</th>
                  <th>Median Stiffness (kPa)</th>
                  <th>Mean FIB-4</th>
                  <th>Mean Stiffness (kPa)</th>
                </tr>
              </thead>
              <tbody>
                {NHANES_AGE_GROUP_SUMMARY.map((row, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600, color: '#ffffff', fontFamily: 'JetBrains Mono' }}>
                      {row.age_group} yrs
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>{row.participants.toLocaleString()}</td>
                    <td style={{ fontFamily: 'JetBrains Mono', color: '#A9D4E7', fontWeight: 600 }}>
                      {row.median_fib4.toFixed(2)}
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono', color: '#ffffff', fontWeight: 600 }}>
                      {row.median_stiffness_kpa.toFixed(1)} kPa
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>{row.mean_fib4.toFixed(2)}</td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>{row.mean_stiffness_kpa.toFixed(2)} kPa</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ background: 'rgba(21, 53, 104, 0.35)', border: '1px solid var(--navy-clinical)', borderRadius: '8px', padding: '16px' }}>
            <strong style={{ color: '#A9D4E7', fontSize: '0.9rem', display: 'block', marginBottom: '4px' }}>
              Key Epidemiological Finding:
            </strong>
            <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: '1.55', margin: 0 }}>
              Median FIB-4 scales &gt;4-fold from age 18–29 (0.42) to age 70–80 (1.73). This is largely an artifact of chronological age being positioned directly in the FIB-4 numerator. In contrast, median physical liver stiffness in the same unselected cohort increases by only 0.5 kPa (4.7 to 5.2 kPa). This demonstrates why age-adjusted cutoffs (e.g. 2.0 in adults &gt;65) are recommended in recent hepatology guidelines.
            </p>
          </div>
        </div>
      )}

      {/* Tab 3: Adjusted Regressions */}
      {activeTab === 'regression' && (
        <div className="sugar-card space-y-4">
          <div className="card-header flex items-center justify-between">
            <div>
              <h2 className="h2" style={{ fontSize: '1.2rem' }}>
                Multivariable Adjusted OLS Regression Models
              </h2>
              <span style={{ fontSize: '0.84rem', color: '#80B3D0' }}>
                Log-transformed liver stiffness regressed against log(FIB-4), age, sex, and Controlled Attenuation Parameter (CAP).
              </span>
            </div>
            <span className="badge badge-navy">outputs/nhanes_8f_adjusted_models.csv</span>
          </div>

          <div className="grid grid-3 gap-4">
            {NHANES_ADJUSTED_MODELS.map((model, idx) => (
              <div
                key={idx}
                style={{
                  background: 'rgba(16, 16, 82, 0.55)',
                  border: `1px solid ${idx === 2 ? 'var(--border-active)' : 'var(--border-subtle)'}`,
                  borderRadius: '10px',
                  padding: '20px',
                }}
                className="space-y-3"
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <h3 style={{ fontSize: '0.95rem', color: '#ffffff', margin: 0 }}>{model.model}</h3>
                  <span className="badge badge-navy">N={model.participants.toLocaleString()}</span>
                </div>

                <div className="space-y-2" style={{ fontSize: '0.88rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#80B3D0' }}>log(FIB-4) Coeff (β):</span>
                    <span style={{ fontFamily: 'JetBrains Mono', color: '#ffffff', fontWeight: 600 }}>
                      +{model.log_fib4_coefficient.toFixed(4)}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#80B3D0' }}>Robust 95% CI:</span>
                    <span style={{ fontFamily: 'JetBrains Mono', color: '#CBD5E1', fontSize: '0.82rem' }}>
                      [{model.robust_ci_lower.toFixed(4)}, {model.robust_ci_upper.toFixed(4)}]
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#80B3D0' }}>p-value:</span>
                    <span style={{ fontFamily: 'JetBrains Mono', color: '#34D399' }}>
                      {model.p_value < 1e-10 ? '< 10⁻¹⁰' : model.p_value.toExponential(3)}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '8px', borderTop: '1px solid var(--navy-clinical)' }}>
                    <strong style={{ color: '#ffffff' }}>Variance Explained (R²):</strong>
                    <strong style={{ fontFamily: 'JetBrains Mono', color: '#A9D4E7' }}>
                      {(model.r_squared * 100).toFixed(2)}%
                    </strong>
                  </div>
                </div>

                <div style={{ width: '100%', height: '8px', borderRadius: '4px', background: 'var(--navy-deep)', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${model.r_squared * 100 * 4}%`,
                      height: '100%',
                      background: idx === 2 ? '#A9D4E7' : '#80B3D0',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div style={{ background: 'rgba(21, 53, 104, 0.35)', border: '1px solid var(--navy-clinical)', borderRadius: '8px', padding: '16px' }}>
            <strong style={{ color: '#A9D4E7', fontSize: '0.9rem', display: 'block', marginBottom: '4px' }}>
              Regression Finding:
            </strong>
            <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: '1.55', margin: 0 }}>
              Controlling for age and sex, the independent explanatory power of FIB-4 for stiffness is <strong>4.25%</strong>. However, incorporating <strong>CAP</strong> (steatosis fat attenuation in dB/m) increases $R^2$ to <strong>13.00%</strong>, proving that ultrasound fat fraction significantly co-modulates physical shear wave velocity independent of fibrosis.
            </p>
          </div>
        </div>
      )}

      {/* Tab 4: Holdout Test Benchmarks */}
      {activeTab === 'test_eval' && (
        <div className="sugar-card space-y-4">
          <div className="card-header flex items-center justify-between">
            <div>
              <h2 className="h2" style={{ fontSize: '1.2rem' }}>
                Holdout Predictive Performance on Unseen Test Participants
              </h2>
              <span style={{ fontSize: '0.84rem', color: '#80B3D0' }}>
                Standardized split (5,768 training / 1,442 holdout test participants) comparing mean absolute error (MAE) and root mean square error (RMSE).
              </span>
            </div>
            <span className="badge badge-navy">outputs/nhanes_8h_fair_model_comparison.csv</span>
          </div>

          <div className="sugar-table-container">
            <table className="sugar-table">
              <thead>
                <tr>
                  <th>Predictive Model</th>
                  <th>Train / Test Participants</th>
                  <th>Test MAE (kPa)</th>
                  <th>Test RMSE (kPa)</th>
                  <th>Test R² (log scale)</th>
                  <th>MAE Improvement vs. M1</th>
                </tr>
              </thead>
              <tbody>
                {NHANES_FAIR_MODEL_COMPARISON.map((row, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600, color: '#ffffff' }}>{row.model}</td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>
                      {row.training_participants} / {row.test_participants}
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono', color: '#A9D4E7', fontWeight: 600 }}>
                      {row.test_mae_kpa.toFixed(4)} kPa
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>{row.test_rmse_kpa.toFixed(4)} kPa</td>
                    <td style={{ fontFamily: 'JetBrains Mono', color: '#34D399' }}>
                      {row.test_r2_log_scale.toFixed(4)}
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>
                      {row.mae_improvement_pct > 0 ? (
                        <span style={{ color: '#34D399', fontWeight: 600 }}>+{row.mae_improvement_pct.toFixed(2)}%</span>
                      ) : (
                        <span style={{ color: '#80B3D0' }}>Baseline</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ background: 'rgba(21, 53, 104, 0.35)', border: '1px solid var(--navy-clinical)', borderRadius: '8px', padding: '16px' }}>
            <strong style={{ color: '#A9D4E7', fontSize: '0.9rem', display: 'block', marginBottom: '4px' }}>
              Holdout Evaluation Summary:
            </strong>
            <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: '1.55', margin: 0 }}>
              Adding FIB-4 to age and sex yields only a marginal <strong>0.03%</strong> MAE improvement on unseen test participants. In contrast, adding steatosis (CAP) reduces MAE by <strong>4.64%</strong>. This objective validation demonstrates why multi-parameter assessment is necessary.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
