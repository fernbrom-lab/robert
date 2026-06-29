import os
import requests
import json
from datetime import datetime

today_date = datetime.now().strftime("%Y-%m-%d")
today_str = datetime.now().strftime("%Y%m%d")
print(f"🚀 開始執行網頁版標案過濾... 今日日期：{today_date}")

# 1. 漏斗篩選規則
MAX_BUDGET = 36000000  # 丙級營造上限 3600 萬
INCLUDE_KEYWORDS = ["景觀", "植生", "綠牆", "綠美化", "園藝", "假設工程", "圍籬", "鷹架", "新建", "公廁"]
EXCLUDE_KEYWORDS = ["主體建築", "下水道", "橋樑", "隧道", "捷運", "高鐵", "都市更新"]

# 2. 串接 g0v API
api_url = f"https://ronny.tw{today_str}"

# 3. 讀取或初始化歷史檔案資料庫
db_file = "history_data.json"
if os.path.exists(db_file):
    with open(db_file, "r", encoding="utf-8") as f:
        history_db = json.load(f)
else:
    history_db = {}

# HTML 頁面公用模板 (整合 Bootstrap)
def save_html(title, content, filename):
    html_code = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <link href="https://jsdelivr.net" rel="stylesheet">
    </head>
    <body class="bg-light">
        <nav class="navbar navbar-dark bg-dark mb-4">
            <div class="container">
                <span class="navbar-brand mb-0 h1">🏗️ 丙級營造廠標案自動偵測系統</span>
                <div>
                    <a href="/index.html" class="btn btn-outline-light btn-sm me-2">今日最新</a>
                    <a href="/history.html" class="btn btn-outline-light btn-sm">歷史日報存檔</a>
                </div>
            </div>
        </nav>
        <div class="container bg-white p-4 rounded shadow-sm">{content}</div>
    </body>
    </html>
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_code)

try:
    response = requests.get(api_url, timeout=20)
    if response.status_code != 200:
        print("❌ 無法讀取 API")
        exit()
        
    data = response.json()
    tenders = data.get("records", [])
    today_tenders = []

    # 4. 漏斗過濾
    for t in tenders:
        title = t.get("title", "")
        try: 
            budget = int(t.get("price", 0))
        except: 
            budget = 0

        if budget > MAX_BUDGET: continue
        if any(ex in title for ex in EXCLUDE_KEYWORDS): continue
        
        if any(inc in title for inc in INCLUDE_KEYWORDS):
            job_number = t.get("job_number", "")
            pcc_url = f"https://pcc.gov.tw{job_number}"

            today_tenders.append([title, budget, t.get("unit_name", "未知機關"), pcc_url])

    # 格式化儲存進 JSON 的資料
    today_tenders_formatted = []
    for item in today_tenders:
        today_tenders_formatted.append({
            "title": item[0],
            "budget": item[1],
            "unit": item[2],
            "url": item[3]
        })

    # 5. 更新歷史資料庫
    history_db[today_date] = today_tenders_formatted
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(history_db, f, ensure_ascii=False, indent=4)

    # 6. 建立前端發布目錄
    os.makedirs("dist/daily_reports", exist_ok=True)

    # 7. 生成【今日最新日報 (index.html)】與【獨立歷史日報】
    table_content = f"<h2>📅 {today_date} 適合公司投標之標案日報</h2><hr>"
    if not today_tenders_formatted:
        table_content += "<p class='text-muted'>今日無符合條件的新標案。</p>"
    else:
        table_content += "<div class='table-responsive'><table class='table table-striped table-hover'><thead>"
        table_content += "<tr><th>標案名稱</th><th>預算金額</th><th>招標機關</th><th>官方連結</th></tr></thead><tbody>"
        for t in today_tenders_formatted:
            table_content += f"<tr><td><b>{t['title']}</b></td><td class='text-danger'>${t['budget']:,}</td><td>{t['unit']}</td><td><a href='{t['url']}' target='_blank' class='btn btn-primary btn-sm'>查看公告</a></td></tr>"
        table_content += "</tbody></table></div>"

    save_html(f"{today_date} 標案日報", table_content, "dist/index.html")
    save_html(f"{today_date} 標案日報", table_content, f"dist/daily_reports/{today_date}.html")

    # 8. 生成【歷史存檔總覽庫 (history.html)】
    # 加入最後更新時間戳記，徹底解決 GitHub Actions 偵測不到檔案變動的報錯問題
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    history_content = "<h2>📚 歷史日報存檔庫</h2>"
    history_content += f"<p class='text-muted'>點選日期即可查看當天篩選出的所有案源（系統最後更新時間：{current_time_str}）：</p><hr>"
    history_content += "<div class='list-group'>"
    
    for date in sorted(history_db.keys(), reverse=True):
        count = len(history_db[date])
        history_content += f"<a href='/daily_reports/{date}.html' class='list-group-item list-group-item-action d-flex justify-content-between align-items-center'>"
        history_content += f"📅 {date} 發布之標案日報 <span class='badge bg-secondary rounded-pill'>{count} 件標案</span></a>"
    history_content += "</div>"
    
    save_html("歷史標案日報存檔庫", history_content, "dist/history.html")
    print("🎉 網頁與歷史存檔成功生成完畢！")

except Exception as e:
    print(f"❌ 錯誤: {e}")
