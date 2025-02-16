# 長者即時照護系統

## 專案簡介
長者即時照護系統是一個基於 Flask 和 PostgreSQL 的後端應用程式，旨在提供長者的即時照護服務。此系統會記錄長者的起床時間、處理緊急情況、並且通過 LINE 提供通知功能。系統整合了 YOLO 模型進行跌倒偵測，並且可以與 Arduino 燈條系統同步，用來記錄長者起床的情況。

此系統的前端應用是使用 Flutter 及 HTML (RWD響應式網頁）開發的，用戶可以通過前端應用查看相關數據及狀態。

### 目錄結構
- **app.py**: 主程式文件，負責處理註冊、登入、長者管理等功能的 API。
- **templates/**: 網頁模板，包括用於顯示用戶頁面的 HTML 檔案。
- **static/**: 靜態資源資料夾，用於儲存偵測後的圖片。

### 技術
- **後端框架**: Flask
- **資料庫**: Render PostgreSQL
- **偵測模型**: YOLO（v8 版本）
- **硬體**: CPU i7 13700, GPU RTX 4070 12GB
- **外部設備**: Arduino 燈條控制器
- **Flutter**: Flutter 應用程式（[長者即時照護系統](https://github.com/Hank-Lin0729/ElderFallAlert_flutter_ios/blob/main/README.md))

## 功能描述
1. **用戶註冊與登入**
    - 使用者可以透過註冊 API 建立帳號，並登入系統來查看長者資訊。
    - 提供 JWT 驗證以保護用戶資料。

2. **長者資訊管理**
    - 增加、查看、刪除長者的資訊。
    - 每個長者都有對應的 region_id 以及名稱。

3. **緊急狀況通知**
    - 系統可以透過 YOLO 模型進行跌倒偵測，一旦發現跌倒情況，會自動存入資料庫，並且向 LINE 用戶發送通知。

4. **燈條狀態紀錄**
    - Arduino 會傳送燈條開啟時間，紀錄長者起床的情況。
    - 燈條的開啟會被記錄在資料庫的 `Light_On_Record` 表中。

5. **偵測圖片紀錄**
    - 系統會將跌倒偵測結果圖片儲存，使用者可以透過 API 來查看最近的圖片。

## 資料庫結構
- **Login_Info**: 儲存用戶登入資訊，包括帳號、密碼（已加密）及唯一的 bot_key。
- **Elder_Info**: 儲存長者的基本資訊，包括 elder_id、名稱、區域 ID 以及 bot_key。
- **Emergency_Info**: 儲存緊急事件資訊，包括事件訊息、緊急程度、時間及與長者相關的 region_id。
- **Light_On_Record**: 記錄燈條的開啟時間，用來推斷長者的起床情況。
- **Line_IDs**: 與 LINE 的 bot_key 對應，用於推送緊急通知。
- **Detection_Records**: 偵測記錄表，儲存 YOLO 模型偵測後的圖片及相關信息。

## 安裝與使用

### 前置需求
- Python 3.8 以上版本
- PostgreSQL 資料庫

### 安裝步驟
1. clone專案：
   ```
   git clone https://github.com/Hank-Lin0729/ElderFallAlert_web.git
   ```
2. 安裝相依庫：
   ```
   pip install -r requirements.txt
   ```
3. 設定環境變數：
   - 創建 `.env` 文件，並設定 `EXTERNAL_DB_URL`（資料庫連接 URL）及 `SECRET_KEY`（應用程式密鑰）。
4. 啟動應用程式：
   ```
   python app.py
   ```
5. 在瀏覽器中開啟 [http://localhost:5011](http://localhost:5011)

## API 端點
- **/register**: 用戶註冊。
- **/login**: 用戶登入。
- **/user_page**: 用戶頁面，顯示長者及緊急資訊。
- **/reset_password**: 重設密碼。
- **/add_elder**: 新增長者資料。
- **/get_latest_photos**: 查看最近的偵測圖片。

## 注意事項
- **權限保護**: 多數端點需要使用者登入後才能操作，確保資料安全性。
- **密碼加密**: 使用 bcrypt 對密碼進行加密存儲。
- **緊急通知**: 若發現跌倒情況，系統會透過 LINE 向設定的用戶發送通知，確保緊急情況即時處理。

## 開發者
- 此專案由林柏翰開發，歡迎進行改進與討論。
