import psycopg2
from dotenv import load_dotenv
import os

# 讀取 .env 文件中的環境變數
load_dotenv()

# 取得資料庫連接 URL
DATABASE_URL = os.getenv('EXTERNAL_DB_URL')  # 或使用 INTERNAL_DB_URL

def execute_sql_file(filename):
    # 讀取 SQL 檔案內容
    with open(filename, 'r', encoding='utf-8') as file:
        sql_commands = file.read()

    try:
        # 連接到資料庫
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # 將 SQL 指令拆分為單獨的命令
        commands = sql_commands.split(';')

        # 逐一執行每個命令
        for command in commands:
            command = command.strip()
            if command:
                cursor.execute(command + ';')

        # 確認變更
        conn.commit()

        print(f"成功執行 {filename} 檔案中的 SQL 指令。")

    except Exception as e:
        print(f"執行過程中發生錯誤: {e}")
    finally:
        # 關閉游標和連接
        cursor.close()
        conn.close()

if __name__ == "__main__":
    execute_sql_file('main.sql')
