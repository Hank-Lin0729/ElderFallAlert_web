function switchToRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
}

function switchToLogin() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
}

function handleLogin() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    // 發送 POST 請求到後端的 /login 路由
    fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.message === '登入成功') {
                // 登入成功後跳轉到使用者專屬頁面
                window.location.href = '/user_page';
            } else {
                alert(data.error || '登入失敗');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('登入過程中出現錯誤，請稍後再試');
        });

    return false; // 阻止表單提交
}

function handleRegister() {
    const name = document.getElementById('register-name').value;
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;
    const botkey = document.getElementById('register-botkey').value;

    // 檢查密碼是否符合長度要求和包含字母與數字
    if (password.length < 6 || password.length > 18) {
        alert("密碼長度需為6到18位數");
        return false;
    }
    if (!/[a-zA-Z]/.test(password) || !/[0-9]/.test(password)) {
        alert("密碼必須包含英文字母和數字");
        return false;
    }

    // 發送 POST 請求到後端的 /register 路由
    fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                username: username,
                password: password,
                bot_key: botkey
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.message === '註冊成功') {
                // 註冊成功後跳轉到登入頁面
                alert('註冊成功，請登入');
                switchToLogin();
            } else {
                alert(data.error || '註冊失敗');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('註冊過程中出現錯誤，請稍後再試');
        });

    return false; // 阻止表單提交
}