const API_BASE = 'http://localhost:8001/api';

export async function analyzeForm(formData) {
  const res = await fetch(`${API_BASE}/analyze/form`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export async function analyzeFormQuick(formData) {
  const res = await fetch(`${API_BASE}/analyze/form/quick`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export async function getSchemeDetail(slug) {
  const res = await fetch(`${API_BASE}/schemes/${slug}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function chatWithAI(question, userText = null) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, user_text: userText }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function compareSchemes(slugs, userText = null) {
  const res = await fetch(`${API_BASE}/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slugs, user_text: userText }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getStats() {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
