const API_BASE = "/api/owner"; // adjust if your Flask app is served on a different origin

function getToken() {
  return localStorage.getItem("foodie_token");
}

function authHeaders() {
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${getToken()}`,
  };
}

let myRestaurant = null; // cached current restaurant object

async function init() {
  if (!getToken()) {
    window.location.href = "/login.html";
    return;
  }
  await loadMyRestaurant();
}

async function loadMyRestaurant() {
  const res = await fetch(`${API_BASE}/restaurants`, { headers: authHeaders() });
  const list = await res.json();

  if (!res.ok || !list.length) {
    document.getElementById("registerSection").classList.remove("hidden");
    document.getElementById("dashboardSection").classList.add("hidden");
    return;
  }

  myRestaurant = list[0]; // simple model: one restaurant per owner
  renderDashboard();
}

function renderDashboard() {
  document.getElementById("registerSection").classList.add("hidden");
  document.getElementById("dashboardSection").classList.remove("hidden");

  document.getElementById("restName").textContent = myRestaurant.name;

  const badge = document.getElementById("statusBadge");
  badge.textContent = myRestaurant.status;
  badge.className = `badge ${myRestaurant.status}`;

  document.getElementById("openToggle").checked = myRestaurant.is_open;

  const rejectionNotice = document.getElementById("rejectionNotice");
  if (myRestaurant.status === "rejected" && myRestaurant.rejection_reason) {
    rejectionNotice.textContent = `Rejected: ${myRestaurant.rejection_reason}`;
    rejectionNotice.classList.remove("hidden");
  } else {
    rejectionNotice.classList.add("hidden");
  }

  renderMenu();
  loadOrders();
}

function renderMenu() {
  const menuList = document.getElementById("menuList");
  menuList.innerHTML = "";
  const items = myRestaurant.menu_items || [];

  if (!items.length) {
    menuList.innerHTML = `<p class="muted">No menu items yet. Add your first dish.</p>`;
    return;
  }

  items.forEach((item) => {
    const div = document.createElement("div");
    div.className = "menu-item";
    div.innerHTML = `
      <div>
        <div class="menu-item-name">${escapeHtml(item.name)} ${item.is_veg ? "🟢" : "🔴"}</div>
        <div class="menu-item-meta">₹${item.price.toFixed(2)} • ${escapeHtml(item.category || "Uncategorized")} • ${item.is_available ? "Available" : "Unavailable"}</div>
      </div>
      <div class="menu-item-actions">
        <button onclick="openItemModal(${item.id})">Edit</button>
        <button onclick="deleteItem(${item.id})">Delete</button>
      </div>
    `;
    menuList.appendChild(div);
  });
}

async function loadOrders() {
  const res = await fetch(`${API_BASE}/restaurants/${myRestaurant.id}/orders`, { headers: authHeaders() });
  const ordersList = document.getElementById("ordersList");
  if (!res.ok) {
    ordersList.innerHTML = `<p class="muted">Could not load orders.</p>`;
    return;
  }
  const orders = await res.json();
  if (!orders.length) {
    ordersList.innerHTML = `<p class="muted">No orders yet.</p>`;
    return;
  }
  ordersList.innerHTML = "";
  orders.slice(0, 20).forEach((order) => {
    const div = document.createElement("div");
    div.className = "order-item";
    div.innerHTML = `
      <div>
        <div class="menu-item-name">Order #${order.id}</div>
        <div class="menu-item-meta">₹${order.total_amount}</div>
      </div>
      <select class="order-status-select" onchange="updateOrderStatus(${order.id}, this.value)">
        ${["accepted", "preparing", "out_for_delivery", "delivered", "cancelled"]
          .map((s) => `<option value="${s}" ${order.status === s ? "selected" : ""}>${s.replace(/_/g, " ")}</option>`)
          .join("")}
      </select>
    `;
    ordersList.appendChild(div);
  });
}

async function updateOrderStatus(orderId, status) {
  await fetch(`${API_BASE}/orders/${orderId}/status`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify({ status }),
  });
}

// ---------- Restaurant registration ----------

document.getElementById("restaurantForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    name: document.getElementById("r_name").value,
    cuisine_type: document.getElementById("r_cuisine").value,
    description: document.getElementById("r_description").value,
    address: document.getElementById("r_address").value,
    city: document.getElementById("r_city").value,
    phone: document.getElementById("r_phone").value,
    image_url: document.getElementById("r_image").value,
  };

  const res = await fetch(`${API_BASE}/restaurants`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  const msg = document.getElementById("registerMsg");

  if (res.ok) {
    msg.textContent = "Submitted! Awaiting admin approval.";
    msg.className = "msg success";
    myRestaurant = data.restaurant;
    setTimeout(renderDashboard, 800);
  } else {
    msg.textContent = data.error || "Something went wrong.";
    msg.className = "msg error";
  }
});

// ---------- Open/close toggle ----------

document.getElementById("openToggle").addEventListener("change", async (e) => {
  await fetch(`${API_BASE}/restaurants/${myRestaurant.id}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify({ is_open: e.target.checked }),
  });
});

// ---------- Menu item modal ----------

function openItemModal(itemId = null) {
  const modal = document.getElementById("itemModal");
  modal.classList.remove("hidden");
  document.getElementById("itemForm").reset();
  document.getElementById("item_id").value = "";
  document.getElementById("itemModalTitle").textContent = "Add menu item";

  if (itemId) {
    const item = myRestaurant.menu_items.find((i) => i.id === itemId);
    if (item) {
      document.getElementById("itemModalTitle").textContent = "Edit menu item";
      document.getElementById("item_id").value = item.id;
      document.getElementById("item_name").value = item.name;
      document.getElementById("item_price").value = item.price;
      document.getElementById("item_category").value = item.category || "";
      document.getElementById("item_description").value = item.description || "";
      document.getElementById("item_image").value = item.image_url || "";
      document.getElementById("item_veg").checked = item.is_veg;
    }
  }
}

document.getElementById("addItemBtn").addEventListener("click", () => openItemModal());
document.getElementById("cancelItemBtn").addEventListener("click", () => {
  document.getElementById("itemModal").classList.add("hidden");
});

document.getElementById("itemForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("item_id").value;
  const payload = {
    name: document.getElementById("item_name").value,
    price: parseFloat(document.getElementById("item_price").value),
    category: document.getElementById("item_category").value,
    description: document.getElementById("item_description").value,
    image_url: document.getElementById("item_image").value,
    is_veg: document.getElementById("item_veg").checked,
  };

  const url = id ? `${API_BASE}/menu/${id}` : `${API_BASE}/restaurants/${myRestaurant.id}/menu`;
  const method = id ? "PUT" : "POST";

  await fetch(url, { method, headers: authHeaders(), body: JSON.stringify(payload) });
  document.getElementById("itemModal").classList.add("hidden");
  await loadMyRestaurant();
});

async function deleteItem(itemId) {
  if (!confirm("Delete this menu item?")) return;
  await fetch(`${API_BASE}/menu/${itemId}`, { method: "DELETE", headers: authHeaders() });
  await loadMyRestaurant();
}

document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("foodie_token");
  window.location.href = "/login.html";
});

init();
