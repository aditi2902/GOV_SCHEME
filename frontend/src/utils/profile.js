/*
 * Converts the raw Analyze form state (all string values, straight from
 * inputs/selects) into the typed payload the backend expects (numeric age/
 * income/cgpa, lowercase gender, resolved "Other" write-ins). Shared by
 * Analyze.jsx (form submission) and Chat.jsx (personalizing chat context
 * from a saved profile) so both stay in sync with the backend contract.
 */
export function buildAnalysisPayload(form) {
  return {
    age: parseInt(form.age),
    gender: (form.gender || '').toLowerCase(),
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
  };
}
