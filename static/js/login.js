//import { gsap } from 'https://cdn.jsdelivr.net/npm/gsap@3.13.0/index.js';

//document.addEventListener('DOMContentLoaded', function() {
    //const preload = document.querySelector('.preload');
    //for(let i=0;i<80;i++){
    //    const wrap = document.createElement('div');
    //    wrap.style.height = `100vh`;
    //    wrap.classList.add('preload-wrap');
    //    preload.appendChild(wrap);
    //    console.log("wrap:"+i);

    //}

    //let tl = gsap.timeline();
    

    //for(let i=0;i<80;i++){
        

    //}
//});


/**
 * 通用 API 请求封装
 * @param {string} url - 请求地址
 * @param {string} method - HTTP 方法 (GET/POST/PUT/DELETE)
 * @param {object} data - 请求体数据（对象或 FormData）
 * @returns {Promise<Response>} fetch 原始 Response
 */
async function API(url = "", method = "GET", data = null) {
    const options = {
        method: method,
        credentials: "include",  // 允许携带/接收 cookie
        headers: {}
    };

    if (method.toUpperCase() !== "GET" && data) {
        if (data instanceof FormData) {
            options.body = data;
            // FormData 不设 Content-Type，浏览器自动带 boundary
        } else {
            options.headers["Content-Type"] = "application/json";
            options.body = JSON.stringify(data);
        }
    }

    const response = await fetch(url, options);
    return response;
}

/**
 * 登录函数
 * 流程：收集表单 → POST 请求 → code 判断成败 → 存 token → 跳转
 *
 * 后端 JSON 规范（与 __username_password_check 一致）：
 *   成功: {"code": 0, "token": "...", "msg": "..."}
 *   失败: {"code": -1, "msg": "错误提示", "ErrorDetails": "..."}
 *   code === 0 表示成功，code < 0 表示业务失败
 */
async function login() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!username || !password) {
        alert("用户名和密码不能为空喵~");
        return;
    }

    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    try {
        const response = await API("/api/auth/login", "POST", formData);
        const body = await response.json();
        const jwtFromCookie = getJwtFromCookie();

        // 按后端规范：code === 0 为成功
        if (body.code === 0 || body.code === "0") {
            const token = jwtFromCookie || body.token || body.access_token || null;
            if (token) {
                localStorage.setItem("jwt_token", token);
                console.log("JWT token 已存储~");
            }
            const redirectUrl = body.redirect || "/";
            window.location.href = redirectUrl;
        } else {
            // 业务失败：显示 msg，控制台打印 ErrorDetails
            if (body.ErrorDetails) {
                console.error("登录失败详情:", body.ErrorDetails);
            }
            alert(body.msg || body.error || "登录失败，请重试");
        }
    } catch (err) {
        console.error("登录请求异常:", err);
        alert("网络错误，请稍后重试喵~");
    }
}

/**
 * 从 document.cookie 中提取 jwt_token
 * @returns {string|null}
 */
function getJwtFromCookie() {
    const match = document.cookie.match(/(?:^|;\s*)jwt_token=([^;]*)/);
    return match ? decodeURIComponent(match[1]) : null;
}

// ========== 绑定登录按钮 ==========
document.addEventListener("DOMContentLoaded", () => {
    const submitBtn = document.querySelector(".login-submitLine input[type='submit']");
    if (submitBtn) {
        submitBtn.addEventListener("click", (e) => {
            e.preventDefault();
            login();
        });
    }

    // 顺便支持回车登录
    const passwordInput = document.getElementById("password");
    if (passwordInput) {
        passwordInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                login();
            }
        });
    }
});