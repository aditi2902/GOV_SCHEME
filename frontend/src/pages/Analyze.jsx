import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  HiOutlineUser,
  HiOutlineAcademicCap,
  HiOutlineCurrencyRupee,
  HiOutlineLocationMarker,
  HiOutlineLightningBolt,
  HiOutlineSearch,
  HiOutlineChevronRight,
  HiOutlineChevronLeft,
  HiOutlineCheckCircle,
} from 'react-icons/hi';
import { analyzeForm, analyzeFormQuick } from '../api';
import './Analyze.css';

// ── Static Data ────────────────────────────────────────

const STATES = [
  'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh',
  'Goa','Gujarat','Haryana','Himachal Pradesh','Jharkhand','Karnataka',
  'Kerala','Madhya Pradesh','Maharashtra','Manipur','Meghalaya','Mizoram',
  'Nagaland','Odisha','Punjab','Rajasthan','Sikkim','Tamil Nadu','Telangana',
  'Tripura','Uttar Pradesh','Uttarakhand','West Bengal',
  // UTs
  'Andaman and Nicobar Islands','Chandigarh','Dadra and Nagar Haveli and Daman and Diu',
  'Delhi','Jammu and Kashmir','Ladakh','Lakshadweep','Puducherry',
  'Other',
];

const CATEGORIES = ['General', 'OBC', 'SC', 'ST', 'EWS', 'Other'];

const GENDERS = ['Male', 'Female', 'Transgender', 'Other'];
const COMMUNITIES = ['Hindu', 'Muslim', 'Christian', 'Sikh', 'Buddhist', 'Jain', 'Parsi', 'Other'];
const RESIDENCE_TYPES = ['Rural', 'Urban'];

const EDUCATION_LEVELS = ['School', 'ITI', 'Diploma', 'UG', 'PG', 'PhD', 'Other'];

const MARITAL_STATUSES = ['Single / Unmarried', 'Married', 'Widow / Widower', 'Divorced'];
const SIBLINGS_OPTIONS = ['Only Child', '1 Sibling', '2+ Siblings'];
const INSTITUTION_TYPES = ['Govt / Aided', 'Private', 'Other'];

// Show course only for these levels
const COURSE_REQUIRED_FOR = ['ITI', 'Diploma', 'UG', 'PG', 'PhD'];

const COURSES = [
  'Engineering / B.Tech / B.E',
  'Medical / MBBS / BDS / BAMS',
  'Science / B.Sc / M.Sc',
  'Commerce / B.Com / M.Com / MBA',
  'Arts / Humanities / BA / MA',
  'Law / LLB / LLM',
  'Computer Science / BCA / MCA',
  'Agriculture / Forestry',
  'Pharmacy / B.Pharm / M.Pharm',
  'Architecture / Design',
  'Nursing / Allied Health',
  'Education / B.Ed / M.Ed',
  'Other',
];

// ── Form Steps ─────────────────────────────────────────

const STEPS = [
  { id: 1, label: 'Personal Info', icon: HiOutlineUser },
  { id: 2, label: 'Location & Income', icon: HiOutlineLocationMarker },
  { id: 3, label: 'Education', icon: HiOutlineAcademicCap },
  { id: 4, label: 'Review & Submit', icon: HiOutlineCheckCircle },
];

// ── Helper Components ──────────────────────────────────

function FormField({ label, required, children, hint }) {
  return (
    <div className="ff-group">
      <label className="ff-label">
        {label}
        {required && <span className="ff-required">*</span>}
      </label>
      {children}
      {hint && <p className="ff-hint">{hint}</p>}
    </div>
  );
}

function SelectWithOther({ id, value, onChange, options, otherValue, onOtherChange, placeholder }) {
  return (
    <div className="select-other-wrap">
      <select
        id={id}
        className="input ff-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">{placeholder || 'Select an option'}</option>
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
      {value === 'Other' && (
        <input
          className="input ff-other-input"
          type="text"
          placeholder="Please specify..."
          value={otherValue}
          onChange={(e) => onOtherChange(e.target.value)}
          autoFocus
        />
      )}
    </div>
  );
}

// ── Main Component ─────────────────────────────────────

const INITIAL_FORM = {
  // Compulsory
  age: '',
  gender: '',
  state: '',
  state_other: '',
  income: '',
  category: '',
  category_other: '',
  education_level: '',
  education_level_other: '',
  // Optional
  course: '',
  course_other: '',
  cgpa: '',
  year_of_study: '',
  disability: false,
  minority: false,
  community: '',
  community_other: '',
  residence_type: '',
  marital_status: '',
  siblings: '',
  institution_type: '',
};

export default function Analyze() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState(INITIAL_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const set = (field, value) => setForm((f) => ({ ...f, [field]: value }));

  // ── Validation per step ──────────────────────────────

  const validateStep = () => {
    setError('');
    if (step === 1) {
      if (!form.age || form.age < 1 || form.age > 100)
        return setError('Please enter a valid age between 1 and 100.'), false;
      if (!form.gender)
        return setError('Please select your gender.'), false;
      if (!form.category)
        return setError('Please select your caste category.'), false;
      if (form.category === 'Other' && !form.category_other.trim())
        return setError('Please specify your caste category.'), false;
    }
    if (step === 2) {
      if (!form.state)
        return setError('Please select your state.'), false;
      if (form.state === 'Other' && !form.state_other.trim())
        return setError('Please specify your state / UT.'), false;
      if (form.income === '' || form.income < 0)
        return setError('Please enter your annual family income (enter 0 if none).'), false;
    }
    if (step === 3) {
      if (!form.education_level)
        return setError('Please select your education level.'), false;
      if (form.education_level === 'Other' && !form.education_level_other.trim())
        return setError('Please specify your education level.'), false;
      if (COURSE_REQUIRED_FOR.includes(form.education_level) && !form.course)
        return setError('Please select your course / stream.'), false;
      if (form.course === 'Other' && !form.course_other.trim())
        return setError('Please specify your course.'), false;
    }
    return true;
  };

  const nextStep = () => {
    if (validateStep()) setStep((s) => Math.min(s + 1, STEPS.length));
  };
  const prevStep = () => { setError(''); setStep((s) => Math.max(s - 1, 1)); };

  // ── Build payload ────────────────────────────────────

  const buildPayload = () => ({
    age: parseInt(form.age),
    gender: form.gender.toLowerCase(),
    state: form.state,
    state_other: form.state_other || null,
    income: parseFloat(form.income),
    category: form.category,
    category_other: form.category_other || null,
    education_level: form.education_level,
    education_level_other: form.education_level_other || null,
    course: form.course || null,
    course_other: form.course_other || null,
    cgpa: form.cgpa ? parseFloat(form.cgpa) : null,
    year_of_study: form.year_of_study ? parseInt(form.year_of_study) : null,
    disability: form.disability,
    minority: form.minority,
    community: form.community,
    community_other: form.community_other || null,
    residence_type: form.residence_type || null,
    marital_status: form.marital_status
      ? form.marital_status.toLowerCase().replace(' / ', '/').split('/')[0].trim()
      : null,
    siblings: form.siblings || null,
    institution_type: form.institution_type || null,
  });

  // ── Submit ───────────────────────────────────────────

  const handleSubmit = async (quick = false) => {
    if (!validateStep()) return;
    setError('');
    setLoading(true);
    try {
      const payload = buildPayload();
      const fn = quick ? analyzeFormQuick : analyzeForm;
      const result = await fn(payload);
      sessionStorage.setItem('analysisResult', JSON.stringify(result));
      sessionStorage.setItem('userText', JSON.stringify(payload));
      navigate('/results');
    } catch (err) {
      setError(`Analysis failed: ${err.message}. Make sure the backend is running.`);
    } finally {
      setLoading(false);
    }
  };

  // ── Step Renderers ───────────────────────────────────

  const renderStep1 = () => (
    <div className="form-step">
      <div className="step-intro">
        <h2 className="heading-md">Personal Information</h2>
        <p className="step-desc">Basic personal details used to match age, gender, and category-specific schemes.</p>
      </div>

      <div className="ff-grid-2">
        <FormField label="Age" required>
          <input
            id="age-input"
            className="input"
            type="number"
            min={1}
            max={120}
            placeholder="e.g. 21"
            value={form.age}
            onChange={(e) => set('age', e.target.value)}
          />
        </FormField>

        <FormField label="Gender" required>
          <select
            id="gender-input"
            className="input ff-select"
            value={form.gender}
            onChange={(e) => set('gender', e.target.value)}
          >
            <option value="">Select gender</option>
            {GENDERS.map((g) => <option key={g} value={g}>{g}</option>)}
          </select>
        </FormField>
      </div>

      <FormField label="Caste Category" required hint="This is used to match reservation-based and category-specific scholarship schemes.">
        <SelectWithOther
          id="category-input"
          value={form.category}
          onChange={(v) => set('category', v)}
          options={CATEGORIES}
          otherValue={form.category_other}
          onOtherChange={(v) => set('category_other', v)}
          placeholder="Select caste category"
        />
      </FormField>

      <FormField label="Community" required={false} hint="Used for minority or community specific schemes (e.g. Muslim, Parsi, Hindu).">
        <SelectWithOther
          id="community-input"
          value={form.community}
          onChange={(v) => {
            set('community', v);
            if (['Muslim', 'Christian', 'Sikh', 'Buddhist', 'Jain', 'Parsi'].includes(v)) {
              set('minority', true);
            }
          }}
          options={COMMUNITIES}
          otherValue={form.community_other}
          onOtherChange={(v) => set('community_other', v)}
          placeholder="Select community"
        />
      </FormField>

      <div className="ff-toggles">
        <label className="toggle-row" htmlFor="disability-toggle">
          <div className="toggle-text">
            <span className="toggle-title">Person with Disability (PwD)</span>
            <span className="toggle-desc">Check if you have a recognized disability (≥ 40%)</span>
          </div>
          <div
            id="disability-toggle"
            className={`toggle-switch ${form.disability ? 'active' : ''}`}
            onClick={() => set('disability', !form.disability)}
            role="checkbox"
            aria-checked={form.disability}
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && set('disability', !form.disability)}
          >
            <div className="toggle-knob" />
          </div>
        </label>

        <label className="toggle-row" htmlFor="minority-toggle">
          <div className="toggle-text">
            <span className="toggle-title">Minority Community</span>
            <span className="toggle-desc">Check if you belong to a recognized minority community</span>
          </div>
          <div
            id="minority-toggle"
            className={`toggle-switch ${form.minority ? 'active' : ''}`}
            onClick={() => set('minority', !form.minority)}
            role="checkbox"
            aria-checked={form.minority}
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && set('minority', !form.minority)}
          >
            <div className="toggle-knob" />
          </div>
        </label>
      </div>

      <div className="ff-grid-2">
        <FormField
          label="Marital Status"
          hint="Optional. Matches widow/single girl schemes."
        >
          <select
            id="marital-status-input"
            className="input ff-select"
            value={form.marital_status}
            onChange={(e) => set('marital_status', e.target.value)}
          >
            <option value="">Select (optional)</option>
            {MARITAL_STATUSES.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </FormField>

        <FormField
          label="Siblings"
          hint="Optional. Matches 'Only Child' schemes."
        >
          <select
            id="siblings-input"
            className="input ff-select"
            value={form.siblings}
            onChange={(e) => set('siblings', e.target.value)}
          >
            <option value="">Select (optional)</option>
            {SIBLINGS_OPTIONS.map((o) => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
        </FormField>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="form-step">
      <div className="step-intro">
        <h2 className="heading-md">Location & Income</h2>
        <p className="step-desc">Your state determines eligibility for state-specific schemes. Income filters income-capped scholarships.</p>
      </div>

      <FormField label="State / Union Territory" required>
        <SelectWithOther
          id="state-input"
          value={form.state}
          onChange={(v) => set('state', v)}
          options={STATES}
          otherValue={form.state_other}
          onOtherChange={(v) => set('state_other', v)}
          placeholder="Select your state"
        />
      </FormField>

      <FormField label="Residence Type" hint="Are you from a Rural or Urban area?">
        <select
          id="residence-input"
          className="input ff-select"
          value={form.residence_type}
          onChange={(e) => set('residence_type', e.target.value)}
        >
          <option value="">Select (optional)</option>
          {RESIDENCE_TYPES.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      </FormField>

      <FormField
        label="Annual Family Income (₹)"
        required
        hint="Enter your total family income per year in Indian Rupees. Enter 0 if no income."
      >
        <div className="input-prefix-wrap">
          <span className="input-prefix"><HiOutlineCurrencyRupee /></span>
          <input
            id="income-input"
            className="input input-with-prefix"
            type="number"
            min={0}
            step={1000}
            placeholder="e.g. 400000"
            value={form.income}
            onChange={(e) => set('income', e.target.value)}
          />
        </div>
        {form.income !== '' && (
          <p className="income-display">
            ₹ {Number(form.income).toLocaleString('en-IN')} per year
            {form.income > 0 && ` (≈ ₹${Math.round(form.income / 100000 * 100) / 100} lakh)`}
          </p>
        )}
      </FormField>
    </div>
  );

  const renderStep3 = () => {
    const showCourse = COURSE_REQUIRED_FOR.includes(form.education_level);
    return (
      <div className="form-step">
        <div className="step-intro">
          <h2 className="heading-md">Education Details</h2>
          <p className="step-desc">Your education level and course are the most important factors for scholarship matching.</p>
        </div>

        <FormField label="Current / Highest Education Level" required>
          <SelectWithOther
            id="education-input"
            value={form.education_level}
            onChange={(v) => { 
              set('education_level', v); 
              set('course', ''); 
              set('course_other', '');
            }}
            options={EDUCATION_LEVELS}
            otherValue={form.education_level_other}
            onOtherChange={(v) => set('education_level_other', v)}
            placeholder="Select education level"
          />
        </FormField>

        {showCourse && (
          <FormField label="Course / Stream" required hint="Select the closest match for your field of study.">
            <SelectWithOther
              id="course-input"
              value={form.course}
              onChange={(v) => set('course', v)}
              options={COURSES}
              otherValue={form.course_other}
              onOtherChange={(v) => set('course_other', v)}
              placeholder="Select your course"
            />
          </FormField>
        )}

        <div className="ff-grid-2">
          <FormField
            label="Academic Score"
            hint="Optional. Enter percentage (0–100) or CGPA (0–10). We'll normalize automatically."
          >
            <input
              id="cgpa-input"
              className="input"
              type="number"
              min={0}
              max={100}
              step={0.1}
              placeholder="e.g. 8.5 or 85"
              value={form.cgpa}
              onChange={(e) => set('cgpa', e.target.value)}
            />
          </FormField>

          {(showCourse || form.education_level === 'School') && (
            <FormField 
              label={form.education_level === 'School' ? "Standard / Class" : "Current Year of Study"} 
              hint={form.education_level === 'School' ? "Optional. Which class are you studying in? (1-12)" : "Optional. Which year are you in?"}
            >
              <input
                id="year-input"
                className="input"
                type="number"
                min={1}
                max={form.education_level === 'School' ? 12 : 10}
                placeholder={form.education_level === 'School' ? "e.g. 10" : "e.g. 2"}
                value={form.year_of_study}
                onChange={(e) => set('year_of_study', e.target.value)}
              />
            </FormField>
          )}
        </div>

        {form.education_level && (
          <FormField
            label="Institution Type"
            hint="Are you studying in a Government/Aided or Private institution/school?"
          >
            <select
              id="institution-type-input"
              className="input ff-select"
              value={form.institution_type}
              onChange={(e) => set('institution_type', e.target.value)}
            >
              <option value="">Select (optional)</option>
              {INSTITUTION_TYPES.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </FormField>
        )}
      </div>
    );
  };

  const renderStep4 = () => {
    const effState = form.state === 'Other' ? form.state_other : form.state;
    const effCategory = form.category === 'Other' ? form.category_other : form.category;
    const effCommunity = form.community === 'Other' ? form.community_other : form.community;
    const effEdu = form.education_level === 'Other' ? form.education_level_other : form.education_level;
    const effCourse = form.course === 'Other' ? form.course_other : form.course;
    return (
      <div className="form-step">
        <div className="step-intro">
          <h2 className="heading-md">Review Your Profile</h2>
          <p className="step-desc">Double-check your details before we run the matching engine.</p>
        </div>

        <div className="review-grid">
          <ReviewCard icon="🧑" label="Age" value={form.age} />
          <ReviewCard icon="⚧" label="Gender" value={form.gender} />
          <ReviewCard icon="🏷️" label="Category" value={effCategory} />
          {effCommunity && <ReviewCard icon="🙏" label="Community" value={effCommunity} />}
          <ReviewCard icon="📍" label="State" value={effState} />
          {form.residence_type && <ReviewCard icon="🏡" label="Residence" value={form.residence_type} />}
          <ReviewCard icon="💰" label="Annual Income" value={form.income !== '' ? `₹${Number(form.income).toLocaleString('en-IN')}` : null} />
          <ReviewCard icon="🎓" label="Education" value={effEdu} />
          {effCourse && <ReviewCard icon="📚" label="Course" value={effCourse} />}
          {form.cgpa && <ReviewCard icon="📊" label="Score" value={`${form.cgpa}${form.cgpa > 10 ? '%' : ' CGPA'}`} />}
          {form.year_of_study && <ReviewCard icon="📅" label="Year of Study" value={`Year ${form.year_of_study}`} />}
          {form.institution_type && <ReviewCard icon="🏛️" label="Institution" value={form.institution_type} />}
          {form.disability && <ReviewCard icon="♿" label="PwD" value="Yes" highlight />}
          {form.minority && <ReviewCard icon="🌙" label="Minority" value="Yes" highlight />}
          {form.marital_status && <ReviewCard icon="💍" label="Marital Status" value={form.marital_status} />}
          {form.siblings && <ReviewCard icon="👨‍👩‍👧‍👦" label="Siblings" value={form.siblings} />}
        </div>

        <p className="review-note">
          ✅ Your profile is ready. The engine will now match across <strong>500+ schemes</strong> using deterministic rules — no AI guessing involved at this stage.
        </p>
      </div>
    );
  };

  // ── Review Card ──────────────────────────────────────

  function ReviewCard({ icon, label, value, highlight }) {
    if (!value) return null;
    return (
      <div className={`review-card ${highlight ? 'review-card--highlight' : ''}`}>
        <span className="review-icon">{icon}</span>
        <div>
          <p className="review-label">{label}</p>
          <p className="review-value">{value}</p>
        </div>
      </div>
    );
  }

  // ── Render ───────────────────────────────────────────

  const isLastStep = step === STEPS.length;

  return (
    <div className="analyze-page">
      <div className="container">

        {/* Header */}
        <div className="analyze-header animate-fadeInUp">
          <h1 className="heading-lg">
            Find Your <span className="text-gradient">Eligible Schemes</span>
          </h1>
          <p className="analyze-subtitle">
            Fill in your details accurately. More information = more precise scheme matching.
            All fields marked <span style={{ color: 'var(--secondary)' }}>*</span> are required.
          </p>
        </div>

        {/* Step Progress Bar */}
        <div className="step-progress animate-fadeInUp stagger-1">
          {STEPS.map((s, idx) => {
            const Icon = s.icon;
            const isDone = step > s.id;
            const isActive = step === s.id;
            return (
              <div key={s.id} className="step-item-wrap">
                <div className={`step-item ${isActive ? 'step-item--active' : ''} ${isDone ? 'step-item--done' : ''}`}>
                  <div className="step-icon-wrap">
                    {isDone ? <HiOutlineCheckCircle /> : <Icon />}
                  </div>
                  <span className="step-label">{s.label}</span>
                </div>
                {idx < STEPS.length - 1 && (
                  <div className={`step-connector ${isDone ? 'step-connector--done' : ''}`} />
                )}
              </div>
            );
          })}
        </div>

        {/* Form Card */}
        <div className="form-card glass-card animate-fadeInUp stagger-2">

          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
          {step === 4 && renderStep4()}

          {error && (
            <div className="analyze-error" role="alert">
              ⚠️ {error}
            </div>
          )}

          {/* Navigation */}
          <div className="form-nav">
            {step > 1 && (
              <button
                className="btn btn-secondary"
                onClick={prevStep}
                disabled={loading}
                id="prev-step-btn"
              >
                <HiOutlineChevronLeft /> Back
              </button>
            )}

            {!isLastStep && (
              <button
                className="btn btn-primary"
                onClick={nextStep}
                disabled={loading}
                id="next-step-btn"
                style={{ marginLeft: 'auto' }}
              >
                Continue <HiOutlineChevronRight />
              </button>
            )}

            {isLastStep && (
              <div className="submit-actions">
                <button
                  className="btn btn-primary btn-lg"
                  onClick={() => handleSubmit(false)}
                  disabled={loading}
                  id="submit-full-btn"
                >
                  {loading ? (
                    <><span className="spinner" style={{ width: 20, height: 20 }} /> Analyzing...</>
                  ) : (
                    <><HiOutlineSearch /> Full Analysis + AI Guidance</>
                  )}
                </button>
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem', margin: '10px 0' }}>OR</div>
                <button
                  className="btn btn-secondary btn-lg"
                  onClick={() => handleSubmit(true)}
                  disabled={loading}
                  id="submit-quick-btn"
                  style={{ width: '100%' }}
                >
                  <HiOutlineLightningBolt /> Quick Match (Instant, No AI Guidance)
                </button>
              </div>
            )}
          </div>

          {loading && (
            <div className="analyze-loading-message">
              <div className="loading-dots"><span /><span /><span /></div>
              <p>Matching your profile against {500}+ schemes...</p>
              <p className="loading-sub">Full Analysis takes 10-30 seconds. Quick Match is instant.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
