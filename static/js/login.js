// ============================================================
//  Lorian 登录页面 JS
//  功能：登录 / Token 管理 / 自动刷新 / 受保护 API 调用示例
// ============================================================

const TOKEN_KEY = "lorian_access_token";
const REFRESH_KEY = "lorian_refresh_token";
const USER_KEY = "lorian_user";


// ============================================================
//  Token 工具函数
// ============================================================

function saveToken(accessToken, refreshToken, user) {
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_KEY, refreshToken);
    if (user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
    }
}

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken() {
    return localStorage.getItem(REFRESH_KEY);
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
}


// ============================================================
//  通用 API 封装
// ============================================================

/**
 * @param {string} url      请求地址
 * @param {string} method   GET/POST/PUT/DELETE
 * @param {*}      data     FormData / 普通对象 / null
 * @param {boolean} auth    是否自动附带 Authorization 头
 * @returns {Promise<Response>}
 */
async function API(url = "", method = "GET", data = null, auth = false) {
    const options = {
        method: method,
        credentials: "include",
        headers: {}
    };

    if (auth) {
        const token = getToken();
        if (token) {
            options.headers["Authorization"] = `Bearer ${token}`;
        }
    }

    if (method.toUpperCase() !== "GET" && data) {
        if (data instanceof FormData) {
            options.body = data;
        } else {
            options.headers["Content-Type"] = "application/json";
            options.body = JSON.stringify(data);
        }
    }

    const response = await fetch(url, options);

    // 自动刷新：如果返回 401 且不是 login 接口本身，尝试 refresh
    if (response.status === 401 && auth && !url.endsWith('/login')) {
        const refreshed = await tryRefreshToken();
        if (refreshed) {
            // 重试原请求
            options.headers["Authorization"] = `Bearer ${getToken()}`;
            return fetch(url, options);
        } else {
            // 刷新失败，跳回登录页
            clearToken();
            window.location.href = '/api/auth/login';
        }
    }

    return response;
}

/**
 * 用 refresh_token 无感刷新 access_token
 * @returns {boolean} 是否刷新成功
 */
async function tryRefreshToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    try {
        const res = await fetch("/api/auth/refresh", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${refreshToken}`,
                "Content-Type": "application/json"
            }
        });
        if (!res.ok) return false;

        const body = await res.json();
        if (body.code === 0 && body.access_token) {
            localStorage.setItem(TOKEN_KEY, body.access_token);
            return true;
        }
    } catch (e) {
        console.error("Token 刷新失败:", e);
    }
    return false;
}


// ============================================================
//  登录函数
// ============================================================

/**
 * 登录
 * 流程：收集表单 → POST → code 判断 → 存 token → 跳转
 */
async function login() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const errorEl = document.getElementById("login-error");

    // 清空旧错误
    if (errorEl) errorEl.textContent = "";

    if (!username || !password) {
        showError("用户名和密码不能为空喵~");
        return;
    }

    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    try {
        const response = await API("/api/auth/login", "POST", formData);
        const body = await response.json();

        if (body.code === 0) {
            // 存储 token（优先使用新的 access_token 字段，兼容旧版 token 字段）
            const accessToken = body.access_token || body.token || null;
            const refreshToken = body.refresh_token || null;
            const user = body.user || null;

            if (accessToken) {
                saveToken(accessToken, refreshToken, user);
            }

            const redirectUrl = body.redirect || "/";
            window.location.href = redirectUrl;
        } else {
            showError(body.msg || "登录失败，请重试");
        }
    } catch (err) {
        console.error("登录请求异常:", err);
        showError("网络错误，请稍后重试喵~");
    }
}

function showError(msg) {
    const errorEl = document.getElementById("login-error");
    if (errorEl) {
        errorEl.textContent = msg;
        errorEl.style.display = "block";
    } else {
        alert(msg);
    }
}


// ============================================================
//  注册示例（可选，登录页暂不用）
// ============================================================

async function register(username, password, permission = "访客") {
    try {
        const res = await API("/api/auth/register", "POST", {
            username, password, permission
        });
        const body = await res.json();
        if (body.code === 0) {
            alert("注册成功，请登录~");
            return true;
        } else {
            alert(body.msg || "注册失败");
            return false;
        }
    } catch (e) {
        console.error(e);
        alert("网络错误");
        return false;
    }
}


// ============================================================
//  绑定事件
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    const submitBtn = document.querySelector(".login-submitLine input[type='submit']");
    if (submitBtn) {
        submitBtn.addEventListener("click", (e) => {
            e.preventDefault();
            login();
        });
    }

    // 回车登录
    const passwordInput = document.getElementById("password");
    if (passwordInput) {
        passwordInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                login();
            }
        });
    }

    // 如果已登录，跳转首页
    // if (getToken()) {
    //     window.location.href = "/";
    // }
});


// ============================================================
//  导出（如果需要被其他模块引用，使用 ES module export）
//  当前 login.html 使用 <script type="module">，可以 export
// ============================================================

export { API, getToken, clearToken, login, register, tryRefreshToken };