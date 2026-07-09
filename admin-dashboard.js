const API_BASE = "/api/admin"; // adjust if your Flask app is served on a different origin

function getToken() {
  return localStorage.getItem("foodie_token");
}
function authHeaders() {
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${getToken()}`,
  };
}
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

// ---------- Tabs ----------

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.add("hidden"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.remove("hidden");

    if (btn.dataset.tab === "restaurants") loadRestaurants();
    if (btn.dataset.tab === "users") loadUsers();
    if (btn.dataset.tab === "orders") loadOrders();
  });
});

// ---------- Overview ----------

async function loadOverview() {
  const res = await fetch(`${API_BASE}/dashboard/summary`, { headers: authHeaders() });
  if (!res.ok) return;
  const s = await res.json();
  const grid = document.getElementById("statGrid");
  const cards = [
    ["Pending restaurants", s.pending_restaurants],
    ["Approved restaurants", s.approved_restaurants],
    ["Total restaurants", s.total_restaurants],
    ["Customers", s.total_users],
    ["Restaurant owners", s.total_owners],
    ["Total orders", s.total_orders],
  ];
  grid.innerHTML = cards
    .map(([label, value]) => `
      <div class="stat-card">
        <div class="stat-value">${value}</div>
        <div class="stat-label">${label}</div>
      </div>`)
    .join("");
}

// ---------- Restaurants ----------

async function loadRestaurants() {
  const status = document.getElementById("restaurantStatusFilter").value;
  const url = status ? `${API_BASE}/restaurants?status=${status}` : `${API_BASE}/restaurants`;
  const res = await fetch(url, { headers: authHeaders() });
  const list = document.getElementById("restaurantList");
  if (!res.ok) {
    list.innerHTML = `<p class="muted">Could not load restaurants.</p>`;
    return;
  }
  const restaurants = await res.json();
  if (!restaurants.length) {
    list.innerHTML = `<p class="muted">No restaurants found.</p>`;
    return;
  }
  list.innerHTML = restaurants
    .map(
      (r) => `
    <div class="list-item">
      <div>
        <div class="item-name">${escapeHtml(r.name)} <span class="badge ${r.status}">${r.status}</span></div>
        <div class="item-meta">${escapeHtml(r.city)} • ${escapeHtml(r.cuisine_type || "—")}</div>
      </div>
      <div class="actions">
        ${r.status !== "approved" ? `<button class="approve" onclick="approveRestaurant(${r.id})">Approve</button>` : ""}
        ${r.status !== "rejected" ? `<button class="reject" onclick="openRejectModal(${r.id})">Reject</button>` : ""}
        ${r.status === "approved" ? `<button class="suspend" onclick="suspendRestaurant(${r.id})">Suspend</button>` : ""}
      </div>
    </div>`
    )
    .join("");
}

document.getElementById("restaurantStatusFilter").addEventListener("change", loadRestaurants);

async function approveRestaurant(id) {
  await fetch(`${API_BASE}/restaurants/${id}/approve`, { method: "POST", headers: authHeaders() });
  loadRestaurants();
  loadOverview();
}

async function suspendRestaurant(id) {
  if (!confirm("Suspend this restaurant?")) return;
  await fetch(`${API_BASE}/restaurants/${id}/suspend`, { method: "POST", headers: authHeaders() });
  loadRestaurants();
  loadOverview();
}

let rejectTargetId = null;
function openRejectModal(id) {
  rejectTargetId = id;
  document.getElementById("rejectReason").value = "";
  document.getElementById("rejectModal").classList.remove("hidden");
}
document.getElementById("cancelRejectBtn").addEventListener("click", () => {
  document.getElementById("rejectModal").classList.add("hidden");
});
document.getElementById("confirmRejectBtn").addEventListener("click", async () => {
  const reason = document.getElementById("rejectReason").value;
  await fetch(`${API_BASE}/restaurants/${rejectTargetId}/reject`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ reason }),
  });
  document.getElementById("rejectModal").classList.add("hidden");
  loadRestaurants();
  loadOverview();
});

// ---------- Users ----------

async function loadUsers() {
  const role = document.getElementById("userRoleFilter").value;
  const url = role ? `${API_BASE}/users?role=${role}` : `${API_BASE}/users`;
  const res = await fetch(url, { headers: authHeaders() });
  const list = document.getElementById("userList");
  if (!res.ok) {
    list.innerHTML = `<p class="muted">Could not load users.</p>`;
    return;
  }
  const users = await res.json();
  list.innerHTML = users
    .map(
      (u) => `
    <div class="list-item">
      <div>
        <div class="item-name">${escapeHtml(u.name)} ${!u.is_active ? '<span class="badge deactivated">inactive</span>' : ""}</div>
        <div class="item-meta">${escapeHtml(u.email)} • ${u.role}</div>
      </div>
      <div class="actions">
        ${u.is_active
          ? `<button class="deactivate" onclick="toggleUser(${u.id}, false)">Deactivate</button>`
          : `<button class="approve" onclick="toggleUser(${u.id}, true)">Reactivate</button>`}
      </div>
    </div>`
    )
    .join("");
}

document.getElementById("userRoleFilter").addEventListener("change", loadUsers);

async function toggleUser(id, activate) {
  const endpoint = activate ? "reactivate" : "deactivate";
  await fetch(`${API_BASE}/users/${id}/${endpoint}`, { method: "POST", headers: authHeaders() });
  loadUsers();
}

// ---------- Orders ----------

async function loadOrders() {
  const res = await fetch(`${API_BASE}/orders`, { headers: authHeaders() });
  const list = document.getElementById("orderList");
  if (!res.ok) {
    list.innerHTML = `<p class="muted">Could not load orders.</p>`;
    return;
  }
  const orders = await res.json();
  if (!orders.length) {
    list.innerHTML = `<p class="muted">No orders yet.</p>`;
    return;
  }
  list.innerHTML = orders
    .map(
      (o) => `
    <div class="list-item">
      <div>
        <div class="item-name">Order #${o.id}</div>
        <div class="item-meta">₹${o.total_amount} • ${o.status}</div>
      </div>
    </div>`
    )
    .join("");
}

document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("foodie_token");
  window.location.href = "/login.html";
});

if (!getToken()) {
  window.location.href = "/login.html";
} else {
  loadOverview();
}
