const API_BASE = "https://upgraded-parakeet-gp6p5pgjq7pfx99-5000.app.github.dev/api";

export async function getStudyActivities() {
  const res = await fetch(`${API_BASE}/study_activities`);
  if (!res.ok) throw new Error("Failed to fetch study activities");
  return res.json();
}

export async function getWords() {
  const res = await fetch(`${API_BASE}/words`);
  if (!res.ok) throw new Error("Failed to fetch words");
  return res.json();
}

export async function getGroups() {
  const res = await fetch(`${API_BASE}/groups`);
  if (!res.ok) throw new Error("Failed to fetch groups");
  return res.json();
}

export async function getSessions() {
  const res = await fetch(`${API_BASE}/study_sessions`);
  if (!res.ok) throw new Error("Failed to fetch sessions");
  return res.json();
}