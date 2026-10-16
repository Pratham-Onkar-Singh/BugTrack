async function request(path, options) {
  let res;
  try {
    res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  } catch {
    throw new Error("Could not reach the API");
  }
  if (res.status === 422) throw new Error("Title and component are required (up to 120 characters)");
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.status === 204 ? null : res.json();
}

export const api = {
  list: (status) => request(`/api/bugs${status ? `?status=${status}` : ""}`),
  stats: () => request("/api/bugs/stats"),
  create: (bug) => request("/api/bugs", { method: "POST", body: JSON.stringify(bug) }),
  update: (id, bug) => request(`/api/bugs/${id}`, { method: "PUT", body: JSON.stringify(bug) }),
  remove: (id) => request(`/api/bugs/${id}`, { method: "DELETE" }),
};
