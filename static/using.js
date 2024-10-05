// 密碼重設
function handleResetPassword() {
    const oldPassword = document.getElementById('old-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmNewPassword = document.getElementById('confirm-new-password').value;

    // 發送 POST 請求到後端的 /reset_password 路由
    fetch('/reset_password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword,
                confirm_new_password: confirmNewPassword
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.message === '更新成功') {
                alert('密碼更新成功');
            } else {
                alert(data.error || '密碼更新失敗');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });

    return false; // 阻止表單提交
}

// Bot Key 重設
function handleResetBotkey() {
    const newBotkey = document.getElementById('new-botkey').value;

    // 發送 POST 請求到後端的 /reset_botkey 路由
    fetch('/reset_botkey', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                new_bot_key: newBotkey
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.message === '更新成功') {
                alert('Bot Key 更新成功');
            } else {
                alert(data.error || 'Bot Key 更新失敗');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });

    return false; // 阻止表單提交
}

// 新增長者
function handleAddElder() {
    const elderName = document.getElementById('elder-name').value;
    const regionId = document.getElementById('region-id').value;

    // 發送 POST 請求到後端的 /add_elder 路由
    fetch('/add_elder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                elder_name: elderName,
                region_id: regionId
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.message === '長者新增成功') {
                alert('長者新增成功');
                // 更新長者卡片區域
                addElderCard(elderName, regionId);
            } else {
                alert(data.error || '新增長者失敗');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });

    return false; // 阻止表單提交
}

// 更新長者卡片區域
function addElderCard(elderName, regionId) {
    const elderCardsContainer = document.getElementById('elder-cards');

    const elderCard = document.createElement('div');
    elderCard.className = 'elder-card';

    elderCard.innerHTML = `
        <p>長者姓名: ${elderName}</p>
        <p>區域編號: ${regionId}</p>
    `;

    elderCardsContainer.appendChild(elderCard);
}

// Modal 操作
var resetPasswordModal = document.getElementById("reset-password-modal");
var resetBotkeyModal = document.getElementById("reset-botkey-modal");
var addElderModal = document.getElementById("add-elder-modal");

var resetPasswordBtn = document.getElementById("reset-password-btn");
var resetBotkeyBtn = document.getElementById("reset-botkey-btn");
var addElderBtn = document.getElementById("add-elder-btn");

var closeResetPassword = document.getElementById("close-reset-password");
var closeResetBotkey = document.getElementById("close-reset-botkey");
var closeAddElder = document.getElementById("close-add-elder");

// 打開對應的 Modal
resetPasswordBtn.onclick = function() {
    resetPasswordModal.style.display = "block";
}
resetBotkeyBtn.onclick = function() {
    resetBotkeyModal.style.display = "block";
}
addElderBtn.onclick = function() {
    addElderModal.style.display = "block";
}

// 關閉對應的 Modal
closeResetPassword.onclick = function() {
    resetPasswordModal.style.display = "none";
}
closeResetBotkey.onclick = function() {
    resetBotkeyModal.style.display = "none";
}
closeAddElder.onclick = function() {
    addElderModal.style.display = "none";
}

// 點擊外部區域關閉 Modal
window.onclick = function(event) {
    if (event.target == resetPasswordModal) {
        resetPasswordModal.style.display = "none";
    }
    if (event.target == resetBotkeyModal) {
        resetBotkeyModal.style.display = "none";
    }
    if (event.target == addElderModal) {
        addElderModal.style.display = "none";
    }
}

// // 更新 ESP32CAM 照片
// function updatePhoto() {
//     const photo = document.getElementById('esp32cam-photo');
//     photo.src = `../static/photos/latest_photo.jpg?${new Date().getTime()}`;
// }

// // 定時更新照片（例如每 5 秒）
// setInterval(updatePhoto, 5000);

function updateEmergencyCards() {
    // 使用 fetch 獲取緊急事件的數據
    fetch('/get_emergencies', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            // 清空舊的緊急事件
            const emergencyContainer = document.getElementById('emergency-container');
            emergencyContainer.innerHTML = ''; // 清空原有卡片

            // 迭代數據並創建新的卡片
            data.forEach(emergency => {
                const emergencyCard = document.createElement('div');
                emergencyCard.className = 'emergency-card';

                // 根據 urgency 值動態添加類別
                if (emergency.urgency === '1') {
                    emergencyCard.classList.add('green');
                } else if (emergency.urgency === '2') {
                    emergencyCard.classList.add('yellow');
                } else if (emergency.urgency === '3') {
                    emergencyCard.classList.add('red');
                }

                // 插入緊急事件的內容
                emergencyCard.innerHTML = `
                <p><strong>區域:</strong> ${emergency.region_id}</p>
                <p><strong>時間:</strong> ${emergency.emergency_time}</p>
                <p><strong>狀況:</strong> ${emergency.emergency_message}</p>
            `;
                emergencyContainer.appendChild(emergencyCard);
            });
        })
        .catch(error => {
            console.error('Error fetching emergencies:', error);
        });
}

// 定時更新（例如每 10 秒更新一次）
setInterval(updateEmergencyCards, 1000);

let currentPage = 1;
let totalPages = 1;

function updatePhotos(page = 1) {
    fetch(`/get_latest_photos?page=${page}&per_page=5`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.photo_urls) {
                const photoContainer = document.getElementById('photo-container');
                photoContainer.innerHTML = ''; // 清空原有的圖片

                // 動態插入多張圖片
                data.photo_urls.forEach(photo_url => {
                    const img = document.createElement('img');
                    img.src = `${photo_url}?${new Date().getTime()}`; // 增加時間戳避免圖片緩存
                    img.alt = 'ESP32CAM 照片';
                    img.classList.add('esp32cam-photo'); // 為圖片添加樣式類
                    photoContainer.appendChild(img);
                });

                // 更新當前頁數和總頁數
                currentPage = data.current_page;
                totalPages = data.total_pages;

                // 根據頁數顯示或隱藏翻頁按鈕
                document.getElementById('prev-page-btn').style.display = currentPage > 1 ? 'inline' : 'none';
                document.getElementById('next-page-btn').style.display = currentPage < totalPages ? 'inline' : 'none';
            } else {
                console.error('Error: No photos found');
            }
        })
        .catch(error => {
            console.error('Error fetching latest photos:', error);
        });
}

// 加載下一頁
function loadNextPage() {
    if (currentPage < totalPages) {
        updatePhotos(currentPage + 1);
    }
}

// 加載上一頁
function loadPrevPage() {
    if (currentPage > 1) {
        updatePhotos(currentPage - 1);
    }
}

// 頁面加載後第一次調用
window.onload = function() {
    updateEmergencyCards(); // 更新緊急事件
    updatePhotos(); // 更新照片
};



document.getElementById('clear-emergencies-btn').addEventListener('click', function() {
    if (confirm('確定要清除所有緊急事件嗎？')) {
        fetch('/clear_emergencies', {
                method: 'DELETE', // 使用 DELETE 方法
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.message === '清除成功') {
                    alert('所有緊急事件已清除');
                    document.getElementById('emergency-container').innerHTML = ''; // 清空緊急事件的顯示區域
                } else {
                    alert('清除失敗: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }
});