import os
import requests
import json
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

today_date = datetime.now().strftime("%Y-%m-%d")
print(f"🚀 開始執行【歷史自癒回溯版】標案與新聞過濾... 今日日期：{today_date}")

# 1. 漏斗篩選規則
MAX_BUDGET = 36000000  # 丙級營造上限 3600 萬
INCLUDE_KEYWORDS = ["景觀", "植生", "綠牆", "綠美化", "園藝", "假設工程", "圍籬", "鷹架", "新建", "公廁"]
EXCLUDE_KEYWORDS = ["主體建築", "下水道", "橋樑", "隧道", "捷運", "高鐵", "都市更新"]

# 2. 【標準唯一官方網址】不拆解、不加密，確保格式 100% 絕對正確
api_base_url = "https://githubusercontent.com"

def fetch_construction_news():
    """抓取最新營造業即時新聞"""
    news_list = []
    try:
        # 直接使用標準編碼過的 Google RSS 網址，避免外掛修改
        rss_url = "https://google.com"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(rss_url, headers=headers, timeout=15)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            for item in root.findall(".//item")[:5]:
                news_list.append({
                    "title": item.find("title").text,
                    "url": item.find("link").text,
                    "source": item.find("source").text if item.find("source") is not None else "產業媒體"
                })
    except Exception as e:
        print(f"⚠️ 新聞模組提示: {e}")
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
    # 先行抓取右側即時新聞
    today_news = fetch_construction_news()
    
    # 3. 核心時光機回溯邏輯
    response = None
    target_fetch_date_str = ""
    target_show_date_str = ""
    
    for i in range(5): # 最多往前追溯 4 天，確保一定能跨越週休二日抓到有上班的檔案
        check_date = datetime.now() - timedelta(days=i)
        target_fetch_date_str = check_date.strftime("%Y%m%d")
        target_show_date_str = check_date.strftime("%Y-%m-%d")
        
        backup_url = f"{api_base_url}{target_fetch_date_str}.json.gz"
        print(f"📡 正在發送正確連線 ──► 正在檢測 {target_show_date_str} 的標案大數據包...")
        
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(backup_url, headers=headers, timeout=15)
        
        if res.status_code == 200:
            response = res
            print(f"🎯 成功對接！系統將自動讀取並清洗 【{target_show_date_str}】 的歷史標案大數據！")
            break
        else:
            print(f"ℹ️ {target_show_date_str} 大數據包尚未就位 (HTTP {res.status_code})，自動繼續往前搜尋...")

    left_column = ""
    right_column = ""
    
    # 組裝右側新聞
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

    if response is None:
        print("⚠️ 警告：連續多日數據均未就位，啟動終極安全安全相容模式...")
        os.makedirs("dist", exist_ok=True)
        left_column += "<h3 class='text-primary mb-3'>📅 適合公司之標案日報</h3>"
        left_column += "<div class='alert alert-warning shadow-sm'>⚠️ <b>系統提示：</b>全台公共工程大數據包正在維護中。</div>"
        left_column += f"<p class='mt-3'><a href='https://pcc.gov.tw' target='_blank' class='btn btn-warning w-100 py-2 fw-bold shadow-sm'>直接開啟：政府電子採購網首頁</a></p>"
        full_content = f"<div class='row g-4'><div class='col-lg-7'>{left_column}</div><div class='col-lg-5'>{right_column}</div></div>"
        save_html(f"{today_date} 智慧情報站", full_content, "dist/index.html")
        exit(0)

    # 4. 正常解壓並過濾數據
    decompressed_data = gzip.decompress(response.content)
    all_records = json.loads(decompressed_data.decode('utf-8'))
    tenders = all_records if isinstance(all_records, list) else all_records.get("records", [])
    today_tenders_formatted = []

    for t in tenders:
        title = t.get("title", "")
        try: budget = int(t.get("price", 0))
        except: budget = 0

        if budget > MAX_BUDGET: continue
        if any(ex in title for ex in EXCLUDE_KEYWORDS): continue
        if any(inc in title for inc in INCLUDE_KEYWORDS):
            job_number = t.get("job_number", "")
            pcc_url = f"https://pcc.gov.tw/tps/QueryTender/query/searchTenderDetail?pkPmsMain={job_number}"
            today_tenders_formatted.append({
                "title": title,
                "budget": budget,
                "unit": t.get("unit_name", "未知機關"),
                "url": pcc_url
            })

    # 組裝左側標案
    current_time_str = datetime.now().strftime("%H:%M:%S")
    left_column += f"<h2>📅 推薦投標標案清單</h2>"
    left_column += f"<p class='text-muted'>📊 <b>數據來源：</b>{target_show_date_str} 發布之全台公告 ｜ ⏱️ <b>更新時間：</b>{current_time_str}</p><hr>"
    
    if not today_tenders_formatted:
        left_column += f"<div class='alert alert-light border shadow-sm'>【{target_show_date_str}】當天無符合公司條件的新發布標案。</div>"
    else:
        left_column += "<div class='table-responsive shadow-sm rounded'><table class='table table-striped table-hover align-middle mb-0'><thead>"
        left_column += "<tr class='table-dark'><th>標案名稱</th><th>預算金額</th><th>招標機關</th><th>官方超連結</th></tr></thead><tbody>"
        for t in today_tenders_formatted:
            left_column += f"<tr><td><b>{t['title']}</b></td><td class='text-danger fw-bold'>${t['budget']:,}</td><td>{t['unit']}</td><td><a href='{t['url']}' target='_blank' class='btn btn-primary btn-sm rounded-pill px-3'>查看公告</a></td></tr>"
        left_column += "</tbody></table></div>"

    # 5. 合併雙欄並發布
    os.makedirs("dist", exist_ok=True)
    full_content = f"<div class='row g-4'><div class='col-lg-7'>{left_column}</div><div class='col-lg-5'>{right_column}</div></div>"
    save_html(f"{today_date} 智慧情報站", full_content, "dist/index.html")
    print(f"🎉 成功解壓並回溯展示【{target_show_date_str}】大數據，雙欄網頁完美建置！")

except Exception as e:
    print(f"❌ 錯誤中斷: {e}")
