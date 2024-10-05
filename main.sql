-- 刪除現有的資料表（如果存在）
DROP TABLE IF EXISTS Line_IDs;
DROP TABLE IF EXISTS Light_On_Record;
DROP TABLE IF EXISTS Emergency_Info;
DROP TABLE IF EXISTS Elder_Info;
DROP TABLE IF EXISTS Login_Info;
DROP TABLE IF EXISTS Detection_Records;

-- 登入資訊表
CREATE TABLE Login_Info (
    id SERIAL PRIMARY KEY,  -- 自動遞增的唯一ID
    login_name VARCHAR(50) NOT NULL,  -- 使用者名稱
    login_account VARCHAR(50) UNIQUE NOT NULL,  -- 帳號需唯一
    login_password VARCHAR(200) NOT NULL,  -- 加密後的密碼
    bot_key VARCHAR(100) NOT NULL,  -- 每個使用者的唯一 bot_key
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 建立時間戳記
);

-- 長者資訊表
CREATE TABLE Elder_Info (
    elder_id SERIAL PRIMARY KEY,  -- 自動遞增的唯一ID
    region_id INTEGER NOT NULL,  -- 區域ID
    elder_name VARCHAR(50) NOT NULL,  -- 長者名稱
    bot_key VARCHAR(100) NOT NULL,  -- 使用者的 bot_key
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 建立時間戳記
);

-- 緊急事件資訊表
CREATE TABLE Emergency_Info (
    id SERIAL PRIMARY KEY,  -- 自動遞增的唯一ID
    region_id TEXT NOT NULL,  -- 區域ID
    emergency_message TEXT NOT NULL,  -- 緊急事件訊息
    emergency_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 緊急事件時間
    bot_key VARCHAR(100) NOT NULL,  -- 使用者的 bot_key
    urgency TEXT NOT NULL,  -- 緊急程度
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 建立時間戳記
);

-- 燈條開啟記錄表
CREATE TABLE Light_On_Record (
    id SERIAL PRIMARY KEY,  -- 自動遞增的唯一ID
    region_id INTEGER NOT NULL,  -- 區域ID
    light_on_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 燈條開啟時間
    bot_key VARCHAR(100) NOT NULL,  -- 使用者的 bot_key
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 建立時間戳記
);

-- Line 使用者對應的 bot_key
CREATE TABLE Line_IDs (
    id SERIAL PRIMARY KEY,  -- 自動遞增的唯一ID
    line_id VARCHAR(100) NOT NULL,  -- LINE ID
    bot_key VARCHAR(100) NOT NULL,  -- 使用者的 bot_key
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 建立時間戳記
);

-- 新增偵測紀錄資料表
CREATE TABLE Detection_Records (
    id SERIAL PRIMARY KEY,  -- 自動遞增的唯一ID
    bot_key VARCHAR(100) NOT NULL,  -- 與使用者關聯的 bot_key
    model_name VARCHAR(50) NOT NULL,  -- 使用的模型名稱
    image_path VARCHAR(255) NOT NULL,  -- 偵測結果圖片的存放路徑
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP  -- 偵測時間戳記
);
