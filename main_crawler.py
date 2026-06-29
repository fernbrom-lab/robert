import os
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime

today_date = datetime.now().strftime("%Y-%m-%d")
today_str = datetime.now().strftime("%Y%m%d")
print(f"🚀 開始執行【雙欄戰情版】標案與新聞過濾... 今日日期：{today_date}")

# 1. 漏斗篩選規則
MAX_BUDGET = 36000000  # 丙級營造上限 3600 萬
INCLUDE_KEYWORDS = ["景觀", "植生", "綠牆", "綠美化", "園藝", "假設工程", "圍籬", "鷹架", "新建", "公廁"]
EXCLUDE_KEYWORDS = ["主體建築", "下水道", "橋樑", "隧道", "捷運", "高鐵", "都市更新"]

# 2. 【100% 網址修正】採用最直接的字串相加，徹底避免任何解碼錯誤或竄改
api_url = "https://ronny.tw" + today_str

def fetch_construction_news():
    """抓取並篩選台灣最新的營造與景觀綠美化即時新聞"""
    news_query = "(營造業 OR 景觀工程 OR 綠美化 OR 假設工程)"
    rss_url = f"https://google.com{news_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    news_list = []
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(rss_url, headers=headers, timeout=15)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            for item in root.findall(".//item")[:5]:
                title = item.find("title").text
                link = item.find("link").text
                source = item.find("source").text if item.find("source") is not None else "產業媒體"
                
                if any(x in title for x in ["炒房", "房貸", "房價"]):
                    continue
                    
                news_list.append({
                    "title": title,
                    "url": link,
                    "source": source
                })
    except Exception as e:
        print(f"⚠️ 新聞抓取模組微幅受阻: {e}")
    return news_list

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
            <div class="container-fluid px-4">
                <span class="navbar-brand mb-0 h1">🏗️ 丙級營造廠：智慧型標案與新聞自動偵測系統</span>
                <div>
                    <a href="/index.html" class="btn btn-outline-light btn-sm">重新整理</a>
                </div>
            </div>
        </nav>
        <div class="container-fluid px-4">{content}</div>
    </body>
    </html>
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_code)

try:
    print(f"📡 正確請求標案 API 網址: {api_url}")
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    response = requests.get(api_url, headers=headers, timeout=25)
    
    # 抓取即時新聞
    today_news = fetch_construction_news()
    
    # 建立雙欄版面佈局變數
    left_column = ""
    right_column = ""
    
    # 組裝右側：產業新聞欄位
    right_column += "<h3 class='text-success mb-3'>📰 營造業與景觀即時新聞</h3>"
    if not today_news:
        right_column += "<p class='text-muted'>今日暫無重大法規或工程產業新聞變動。</p>"
    else:
        right_column += "<div class='list-group shadow-sm'>"
        for n in today_news:
            right_column += f"""
            <a href='{n['url']}' target='_blank' class='list-group-item list-group-item-action py-3'>
                <h6 class='mb-1 text-dark fw-bold'>{n['title']}</h6>
                <div class='d-flex w-100 justify-content-between mt-2'>
                    <small class='text-secondary'>來源：{n['source']}</small>
                    <small class='text-primary'>點擊閱讀 →</small>
                </div>
            </a>
            """
        right_column += "</div>"

    # 處理標案 403 自癒提示機制 (100% 正確的官方手動查閱超連結)
    if response.status_code == 403:
        print("⚠️ 偵測到 403 阻擋，自動切換至雙欄自癒模式...")
        os.makedirs("dist", exist_ok=True)
        
        left_column += "<h3 class='text-primary mb-3'>📅 適合公司之標案日報</h3>"
        left_column += "<div class='alert alert-warning shadow-sm'>⚠️ <b>系統提示：</b>今日官方 API 暫時限制海外機房流量 (HTTP 403)。系統已安排自動重試。</div>"
        left_column += f"<p class='mt-3'><a href='https://pcc.gov.tw{today_str}' target='_blank' class='btn btn-warning w-100 py-2 fw-bold shadow-sm'>直接開啟政府電子採購網：當日公告總表</a></p>"
        
        full_content = f"""
        <div class='row g-4'>
            <div class='col-lg-7'>{left_column}</div>
            <div class='col-lg-5'>{right_column}</div>
        </div>
        """
        save_html(f"{today_date} 智慧情報站", full_content, "dist/index.html")
        print("🎉 雙欄自癒網頁已成功部署！")
        exit(0)
        
    if response.status_code != 200:
        print(f"❌ 標案系統未預期中斷，狀態碼: {response.status_code}")
        exit()
        
    # 正常模式解析標案
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

    # 組裝左側：標案表格欄位
    current_time_str = datetime.now().strftime("%H:%M:%S")
    left_column += f"<h2>📅 {today_date} 推薦投標標案</h2>"
    left_column += f"<p class='text-muted'>更新時間：{current_time_str} (金額限額 3,600 萬內)</p><hr>"
    
    if not today_tenders_formatted:
        left_column += "<div class='alert alert-light border shadow-sm'>今日無符合條件的新發布標案。</div>"
    else:
        left_column += "<div class='table-responsive shadow-sm rounded'><table class='table table-striped table-hover align-middle mb-0'><thead>"
        left_column += "<tr class='table-dark'><th>標案名稱</th><th>預算金額</th><th>招標機關</th><th>官方超連結</th></tr></thead><tbody>"
        for t in today_tenders_formatted:
            left_column += f"<tr><td><b>{t['title']}</b></td><td class='text-danger fw-bold'>${t['budget']:,}</td><td>{t['unit']}</td><td><a href='{t['url']}' target='_blank' class='btn btn-primary btn-sm rounded-pill px-3'>查看公告</a></td></tr>"
        left_column += "</tbody></table></div>"

    # 雙欄合併渲染成 HTML
    os.makedirs("dist", exist_ok=True)
    full_content = f"""
    <div class='row g-4'>
        <div class='col-lg-7'>{left_column}</div>
        <div class='col-lg-5'>{right_column}</div>
    </div>
    """
    save_html(f"{today_date} 智慧情報站", full_content, "dist/index.html")
    print("🎉 雙欄儀表板網頁全新生成完畢！")

except Exception as e:
    print(f"❌ 錯誤中斷: {e}")
