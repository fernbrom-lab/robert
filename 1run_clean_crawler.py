import os
import requests
import json
from datetime import datetime

today_date = datetime.now().strftime("%Y-%m-%d")
today_str = datetime.now().strftime("%Y%m%d")
print(f"🚀 開始執行全新網頁版標案過濾... 今日日期：{today_date}")

# 1. 漏斗篩選規則
MAX_BUDGET = 36000000  # 丙級營造上限 3600 萬
INCLUDE_KEYWORDS = ["景觀", "植生", "綠牆", "綠美化", "園藝", "假設工程", "圍籬", "鷹架", "新建", "公廁"]
EXCLUDE_KEYWORDS = ["主體建築", "下水道", "橋樑", "隧道", "捷運", "高鐵", "都市更新"]

# 2. 【終極防竄改】將網址打碎成獨立單字，強迫 Python 執行時才拼接，徹底避開系統自動文字替換
part1 = "https://"
part2 = "pcc"
part3 = "g0v"
part4 = "ronny"
part5 = "tw"
api_url = f"{part1}{part2}.{part3}.{part4}.{part5}/api/listbydate?date={today_str}"

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
    print(f"📡 【終極安全連線】正在請求正確官方 API 網址: {api_url}")
    
    # 模擬一般瀏覽器標頭，避免被當成惡意連線
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(api_url, headers=headers, timeout=25)
    
    if response.status_code != 200:
        print(f"❌ 無法讀取 API，狀態碼: {response.status_code}")
        exit()
        
    data = response.json()
    tenders = data.get("records", [])
    today_tenders_formatted = []

    for t in tenders:
        title = t.get("title", "")
        try: budget = int(t.get("price", 0))
        except: budget = 0

        if budget > MAX_BUDGET: continue
        if any(ex in title for ex in EXCLUDE_KEYWORDS): continue
        
        if any(inc in title for inc in INCLUDE_KEYWORDS):
            job_number = t.get("job_number", "")
            pcc_url = f"https://pcc.gov.tw{job_number}"

            today_tenders_formatted.append({
                "title": title,
                "budget": budget,
                "unit": t.get("unit_name", "未知機關"),
                "url": pcc_url
            })

    os.makedirs("dist", exist_ok=True)

    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    table_content = f"<h2>📅 {today_date} 適合公司投標之標案日報</h2>"
    table_content += f"<p class='text-muted'>系統最後更新時間：{current_time_str}</p><hr>"
    
    if not today_tenders_formatted:
        table_content += "<p class='text-muted'>今日目前無符合條件的新標案。</p>"
    else:
        table_content += "<div class='table-responsive'><table class='table table-striped table-hover'><thead>"
        table_content += "<tr><th>標案名稱</th><th>預算金額</th><th>招標機關</th><th>官方連結</th></tr></thead><tbody>"
        for t in today_tenders_formatted:
            table_content += f"<tr><td><b>{t['title']}</b></td><td class='text-danger'>${t['budget']:,}</td><td>{t['unit']}</td><td><a href='{t['url']}' target='_blank' class='btn btn-primary btn-sm'>查看公告</a></td></tr>"
        table_content += "</tbody></table></div>"

    save_html(f"{today_date} 標案日報", table_content, "dist/index.html")
    print("🎉 網頁成功生成完畢！")

except Exception as e:
    print(f"❌ 錯誤: {e}")
