// ============================================================
//  Lorian Dashboard JS — 4 模块
//  看板 / 更新 / 公告 / 账号
// ============================================================

const API = "/api/dashboard";

function getToken() { return localStorage.getItem("lorian_access_token"); }
function getUser() { const r = localStorage.getItem("lorian_user"); return r ? JSON.parse(r) : null; }
function clearSession() { localStorage.removeItem("lorian_access_token"); localStorage.removeItem("lorian_refresh_token"); localStorage.removeItem("lorian_user"); }

async function apiGet(path) {
    const t = getToken();
    if (!t) { window.location.href = "/api/auth/login"; return null; }
    const r = await fetch(path, { headers: { "Authorization": `Bearer ${t}` } });
    if (r.status === 401) { clearSession(); window.location.href = "/api/auth/login"; return null; }
    return r.json();
}
async function apiPost(path, body = {}) {
    const t = getToken();
    if (!t) { window.location.href = "/api/auth/login"; return null; }
    const r = await fetch(path, {
        method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${t}` },
        body: JSON.stringify(body)
    });
    if (r.status === 401) { clearSession(); window.location.href = "/api/auth/login"; return null; }
    return r.json();
}
async function apiDelete(path) {
    const t = getToken();
    if (!t) { window.location.href = "/api/auth/login"; return null; }
    const r = await fetch(path, { method: "DELETE", headers: { "Authorization": `Bearer ${t}` } });
    if (r.status === 401) { clearSession(); window.location.href = "/api/auth/login"; return null; }
    return r.json();
}

// ---- 页面入口 ----
document.addEventListener("DOMContentLoaded", () => {
    const user = getUser();
    if (!user || !getToken()) { window.location.href = "/api/auth/login"; return; }

    document.getElementById("user-display").textContent = `${user.username} (${user.permission})`;

    const isAdmin = user.permission === "管理员" || user.permission === "最高管理员";
    const isSuper = user.permission === "最高管理员";
    document.getElementById("tab-updates").style.display  = isAdmin  ? "" : "none";
    document.getElementById("tab-announce").style.display = isAdmin  ? "" : "none";
    document.getElementById("tab-accounts").style.display = isAdmin  ? "" : "none";

    document.getElementById("btn-logout").onclick = async () => {
        await fetch("/api/auth/logout", { method: "POST", headers: { "Authorization": `Bearer ${getToken()}` } });
        clearSession(); window.location.href = "/api/auth/login";
    };

    // Tab 切换
    document.querySelectorAll(".tab-btn").forEach(b => {
        b.onclick = () => {
            document.querySelectorAll(".tab-btn").forEach(x => x.classList.remove("active"));
            document.querySelectorAll(".tab-panel").forEach(x => x.style.display = "none");
            b.classList.add("active");
            document.getElementById("panel-" + b.dataset.tab).style.display = "";
            if (b.dataset.tab === "stats") loadStats();
            if (b.dataset.tab === "updates") loadUpdates();
            if (b.dataset.tab === "announce") loadAnnouncements();
            if (b.dataset.tab === "accounts") loadAccounts();
        };
    });

    loadStats(); // 默认激活看板
});

// ===== 1. 数据看板 =====
async function loadStats() {
    const d = await apiGet(`${API}/stats`);
    if (!d || d.code !== 0) return;
    const s = d.data;
    document.getElementById("v-devices").textContent   = s.total_devices ?? "--";
    document.getElementById("v-active").textContent    = s.today_active ?? "--";
    document.getElementById("v-downloads").textContent = s.total_downloads ?? "--";
    document.getElementById("v-online").textContent    = s.online_devices ?? "--";
    document.getElementById("v-version").textContent   = s.latest_version ?? "--";
}

// ===== 2. 更新管理 =====
async function loadUpdates() {
    const d = await apiGet(`${API}/updates`);
    if (!d || d.code !== 0) return;
    const pkgs = d.data.packages || [];
    const tbody = document.querySelector("#updates-table tbody");
    if (pkgs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="placeholder">暂无安装包</td></tr>`;
        return;
    }
    tbody.innerHTML = pkgs.map(p => `
        <tr>
            <td>${p.filename||""} ${p.is_latest ? '<span class="badge">最新</span>' : ""}</td>
            <td>${p.version||""}</td>
            <td>${p.size_mb||"?"} MB</td>
            <td>${p.uploaded_at||""}</td>
            <td>${p.uploader||""}</td>
            <td>${p.status||"active"}</td>
        </tr>`).join("");
}

async function uploadPackage() {
    const file = document.getElementById("upload-file").files[0];
    if (!file) return alert("请选择文件");
    const fd = new FormData(); fd.append("file", file);
    const t = getToken();
    const r = await fetch(`${API}/updates/upload`, { method: "POST", headers: { "Authorization": `Bearer ${t}` }, body: fd });
    const b = await r.json();
    alert(b.msg); loadUpdates();
}

async function pushUpdate() {
    const ver = prompt("输入要推送的版本号:");
    if (!ver) return;
    const d = await apiPost(`${API}/updates/push`, { version: ver, target: "all" });
    alert(d.msg);
}

// ===== 3. 公告管理 =====
async function loadAnnouncements() {
    const d = await apiGet(`${API}/announcements`);
    if (!d || d.code !== 0) return;
    const items = d.data.announcements || [];
    const div = document.getElementById("announce-list");
    div.innerHTML = items.length
        ? items.map(a => `
            <div class="card-row">
                <div><strong>#${a.id} ${a.title}</strong> <span class="badge">${a.is_active ? "生效中" : "已停用"}</span></div>
                <div class="muted">${a.content}</div>
                <div class="actions">
                    <button onclick="pushAnn(${a.id})">推送</button>
                    <button onclick="editAnn(${a.id},'${a.title.replace(/'/g,"\\'")}','${a.content.replace(/'/g,"\\'").replace(/\n/g," ")}',${a.is_active})">编辑</button>
                    <button class="danger" onclick="delAnn(${a.id})">删除</button>
                </div>
            </div>`).join("")
        : `<div class="placeholder">暂无公告</div>`;
}

async function createAnn() {
    const title = prompt("公告标题:");
    if (!title) return;
    const content = prompt("公告内容:");
    if (!content) return;
    const d = await apiPost(`${API}/announcements`, { title, content });
    alert(d.msg); loadAnnouncements();
}

async function editAnn(id, oldTitle, oldContent, oldActive) {
    const title = prompt("标题:", oldTitle);
    if (title === null) return;
    const content = prompt("内容:", oldContent);
    if (content === null) return;
    const t = getToken();
    const r = await fetch(`${API}/announcements/${id}`, {
        method: "PUT", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${t}` },
        body: JSON.stringify({ title, content, is_active: oldActive })
    });
    const b = await r.json();
    alert(b.msg); loadAnnouncements();
}

async function delAnn(id) {
    if (!confirm("确认删除？")) return;
    const d = await apiDelete(`${API}/announcements/${id}`);
    alert(d.msg); loadAnnouncements();
}

async function pushAnn(id) {
    const d = await apiPost(`${API}/announcements/push`, { id });
    alert(d.msg);
}

// ===== 4. 账号管理 =====
async function loadAccounts() {
    const d = await apiGet(`${API}/accounts`);
    if (!d || d.code !== 0) return;
    const users = d.data.users || [];
    const tbody = document.querySelector("#accounts-table tbody");
    tbody.innerHTML = users.map(u => `
        <tr>
            <td>${u.id}</td>
            <td>${u.username}</td>
            <td>${u.permission}</td>
            <td><button class="danger" onclick="delUser(${u.id})">删除</button></td>
        </tr>`).join("");
}

async function createUser() {
    const u = prompt("用户名:");
    if (!u) return;
    const p = prompt("密码:");
    if (!p) return;
    const perm = prompt("权限 (锁定/访客/管理员/最高管理员):", "访客");
    if (!perm) return;
    const d = await apiPost(`${API}/accounts`, { username: u, password: p, permission: perm });
    alert(d.msg); loadAccounts();
}

async function delUser(id) {
    if (!confirm(`确认删除用户 #${id}？`)) return;
    const d = await apiDelete(`${API}/accounts/${id}`);
    alert(d.msg); loadAccounts();
}
