import os
import json
import re
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

def fetch_tenders_from_pcc(keyword: str = "景觀", max_budget: int = 36000000, limit: int = 30, debug: bool = False) -> List[Dict]:
    """
    從政府電子採購網的公開頁面解析標案資料
    """
    tenders = []
    
    try:
        if debug:
            print(f"   🔍 查詢關鍵字：{keyword}")
        
        # 政府電子採購網的查詢頁面
        url = "https://web.pcc.gov.tw/tps/QueryTender.do"
        
        params = {
            "method": "search",
            "searchType": "basic",
            "tenderName": keyword,
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            if debug:
                print(f"   ✅ 連線成功，正在解析網頁...")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 嘗試多種可能的標案列表選擇器
            selectors = [
                'table tr',           # 通用表格
                '.tender-list tr',    # 可能的 class
                '#tenderTable tr',    # 可能的 ID
                'tr.tender-item',     # 可能的 class
            ]
            
            rows = []
            for selector in selectors:
                rows = soup.select(selector)
                if len(rows) > 1:
                    if debug:
                        print(f"   ✅ 使用選擇器 '{selector}' 找到 {len(rows)} 列")
                    break
            
            if len(rows) <= 1 and debug:
                print(f"   ⚠️ 找不到標案列表，嘗試搜尋所有包含數字的表格列...")
                # 備用：找所有包含數字的表格列
                all_rows = soup.find_all('tr')
                rows = [r for r in all_rows if re.search(r'\d+[,]?\d+', str(r))]
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    title = cells[0].get_text(strip=True) if cells else ""
                    budget_text = cells[1].get_text(strip=True) if len(cells) > 1 else "0"
                    unit = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    
                    # 過濾掉明顯不是標案的列
                    if not title or len(title) < 5:
                        continue
                    if '總計' in title or '合計' in title:
                        continue
                    
                    budget = parse_budget(budget_text)
                    
                    if title and budget > 0 and budget <= max_budget:
                        tenders.append({
                            'title': title,
                            'budget': budget,
                            'unit': unit or '未提供',
                            'date': '',
                            'source': '政府電子採購網'
                        })
            
            if debug:
                print(f"   ✅ 解析完成，找到 {len(tenders)} 筆符合條件的標案")
            
        else:
            if debug:
                print(f"   ❌ 請求失敗：{response.status_code}")
            
    except Exception as e:
        if debug:
            print(f"   ❌ 發生錯誤：{e}")
    
    return tenders[:limit]

def search_with_multiple_keywords(keywords: List[str], max_budget: int = 36000000, limit: int = 30) -> List[Dict]:
    """
    使用多個關鍵字進行查詢，並合併結果
    """
    all_tenders = []
    seen_titles = set()
    
    print(f"📡 嘗試 {len(keywords)} 個關鍵字查詢...")
    
    for keyword in keywords:
        print(f"\n   🔍 關鍵字：{keyword}")
        tenders = fetch_tenders_from_pcc(keyword, max_budget, limit, debug=True)
        
        for t in tenders:
            if t['title'] not in seen_titles:
                seen_titles.add(t['title'])
                all_tenders.append(t)
        
        print(f"   📊 找到 {len(tenders)} 筆，累計 {len(all_tenders)} 筆")
    
    return all_tenders[:limit]

def parse_budget(value) -> int:
    """解析預算金額"""
    if isinstance(value, (int, float)):
        return int(value)
    
    if isinstance(value, str):
        # 移除千分位、貨幣符號等
        clean = re.sub(r'[^\d]', '', value)
        return int(clean) if clean.isdigit() else 0
    
    return 0

def save_results(tenders: List[Dict], filename: str = "tender_results.json"):
    """儲存查詢結果"""
    result = {
        "query_time": datetime.now().isoformat(),
        "total_count": len(tenders),
        "tenders": tenders
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 結果已儲存至 {filename}")

def generate_html_report(tenders: List[Dict], filename: str = "tender_report.html"):
    """產生 HTML 報告"""
    html = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>標案查詢結果</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .stats {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 15px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        tr:hover {{ background-color: #f1f1f1; }}
        .budget {{ color: #e74c3c; font-weight: bold; }}
        .source {{ color: #7f8c8d; font-size: 0.9em; }}
        .info {{ background: #d4edda; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        .warning {{ background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏗️ 標案查詢結果</h1>
        <div class="stats">
            <strong>查詢時間：</strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>符合條件的標案數量：</strong>{len(tenders)} 筆
        </div>
        
        <div class="info">
            💡 資料來源：政府電子採購網（https://web.pcc.gov.tw）
        </div>
"""
    
    if not tenders:
        html += """
        <div class="warning">
            ⚠️ 目前沒有找到符合條件的標案<br>
            建議：<br>
            1. 直接至 <a href="https://web.pcc.gov.tw" target="_blank">政府電子採購網</a> 查詢更多標案<br>
            2. 調整查詢關鍵字（如：工程、採購、新建）<br>
            3. 放寬預算上限
        </div>
"""
    else:
        html += """
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>標案名稱</th>
                    <th>預算金額</th>
                    <th>招標機關</th>
                    <th>資料來源</th>
                </tr>
            </thead>
            <tbody>
"""
        for i, t in enumerate(tenders, 1):
            html += f"""
                <tr>
                    <td>{i}</td>
                    <td>{t['title']}</td>
                    <td class="budget">${t['budget']:,}</td>
                    <td>{t['unit']}</td>
                    <td class="source">{t.get('source', 'N/A')}</td>
                </tr>
"""
        html += """
            </tbody>
        </table>
"""
    
    html += """
        <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
            <h4>📌 使用說明</h4>
            <p>1. 直接至 <a href="https://web.pcc.gov.tw" target="_blank">政府電子採購網</a> 查詢更多標案</p>
            <p>2. 可使用「標案查詢系統」設定更多過濾條件</p>
            <p>3. 此為自動查詢結果，建議以官方網站最新資訊為準</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ HTML 報告已儲存至 {filename}")

def main():
    """主程式"""
    print("="*60)
    print("🏗️ 政府電子採購網 - 標案查詢工具")
    print("="*60)
    
    # 使用多個關鍵字查詢
    keywords = ["景觀", "綠美化", "圍籬", "新建", "工程", "採購"]
    
    tenders = search_with_multiple_keywords(
        keywords=keywords,
        max_budget=36000000,
        limit=50
    )
    
    # 儲存結果
    save_results(tenders)
    generate_html_report(tenders)
    
    # 顯示結果
    if tenders:
        print(f"\n✅ 共找到 {len(tenders)} 筆符合條件的標案：")
        for i, t in enumerate(tenders[:10], 1):
            print(f"\n{i}. {t['title']}")
            print(f"   預算金額：${t['budget']:,}")
            print(f"   招標機關：{t['unit']}")
            print(f"   資料來源：{t.get('source', 'N/A')}")
    else:
        print("\n⚠️ 沒有找到符合條件的標案")
        print("\n📌 建議：")
        print("  1. 直接至政府電子採購網查詢：https://web.pcc.gov.tw")
        print("  2. 調整關鍵字（如：工程、採購、新建）")
        print("  3. 放寬預算上限")
        print("  4. 此為自動化工具，建議以官方網站最新資訊為準")

if __name__ == "__main__":
    main()
