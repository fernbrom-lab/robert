import os
import json
import re
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any

def fetch_tenders_from_gov_data(keyword: str = "景觀", max_budget: int = 36000000, limit: int = 50) -> List[Dict]:
    """
    從政府開放資料平台抓取標案資料
    
    使用資料集：公共工程標案（資料集 ID: 16834）
    來源：https://data.gov.tw/dataset/16834
    """
    tenders = []
    
    # 政府開放資料平台 API
    dataset_id = "16834"  # 公共工程標案
    url = f"https://data.gov.tw/api/v1/rest/dataset/{dataset_id}"
    
    try:
        print(f"📡 從政府開放資料平台查詢標案...")
        print(f"   關鍵字：{keyword}")
        print(f"   預算上限：${max_budget:,}")
        
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # 解析回應
            records = []
            if 'result' in data and 'records' in data['result']:
                records = data['result']['records']
            elif 'records' in data:
                records = data['records']
            
            print(f"   📊 取得 {len(records)} 筆原始資料")
            
            # 定義過濾關鍵字
            include_keywords = ["景觀", "植生", "綠牆", "綠美化", "園藝", "圍籬", "鷹架", "安全圍籬", "新建", "公廁"]
            
            for record in records[:100]:  # 限制處理筆數
                # 嘗試不同的欄位名稱
                title = (
                    record.get('標案名稱') or 
                    record.get('title') or 
                    record.get('案名') or 
                    record.get('標案名稱（案號）') or 
                    ''
                )
                
                budget_str = (
                    record.get('預算金額') or 
                    record.get('budget') or 
                    record.get('預算金額（元）') or 
                    '0'
                )
                
                unit = (
                    record.get('招標機關') or 
                    record.get('unit') or 
                    record.get('機關名稱') or 
                    record.get('機關') or 
                    ''
                )
                
                date = (
                    record.get('公告日期') or 
                    record.get('date') or 
                    record.get('招標公告日期') or 
                    record.get('公告日') or 
                    ''
                )
                
                # 清理預算金額
                budget = parse_budget(budget_str)
                
                # 過濾條件
                if not title or budget <= 0:
                    continue
                    
                if budget > max_budget:
                    continue
                
                # 關鍵字比對（如果有關鍵字）
                if keyword:
                    keyword_match = keyword in title
                    if not keyword_match:
                        # 檢查是否包含其他相關關鍵字
                        keyword_match = any(kw in title for kw in include_keywords)
                    if not keyword_match:
                        continue
                
                tenders.append({
                    'title': title,
                    'budget': budget,
                    'unit': unit or '未提供',
                    'date': date,
                    'source': '政府開放資料平台'
                })
            
            print(f"   ✅ 過濾後找到 {len(tenders)} 筆符合條件的標案")
            
        else:
            print(f"   ❌ API 請求失敗：{response.status_code}")
            
    except requests.exceptions.Timeout:
        print("   ⏰ 請求超時")
    except requests.exceptions.ConnectionError:
        print("   🔌 連線失敗")
    except Exception as e:
        print(f"   ❌ 發生錯誤：{e}")
    
    return tenders

def fetch_tenders_from_multiple_sources(keyword: str = "景觀", max_budget: int = 36000000, limit: int = 50) -> List[Dict]:
    """
    從多個政府開放資料來源抓取標案
    """
    all_tenders = []
    
    # 多個可能的資料集 ID
    dataset_ids = [
        "16834",  # 公共工程標案
        "15863",  # 政府採購公告
        "16964",  # 決標公告
    ]
    
    seen_titles = set()
    
    for dataset_id in dataset_ids:
        try:
            url = f"https://data.gov.tw/api/v1/rest/dataset/{dataset_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('result', {}).get('records', [])
                
                for record in records[:50]:
                    title = record.get('標案名稱') or record.get('title') or ''
                    
                    # 去重
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)
                    
                    budget = parse_budget(record.get('預算金額') or record.get('budget') or 0)
                    unit = record.get('招標機關') or record.get('unit') or ''
                    
                    if title and budget > 0 and budget <= max_budget:
                        if keyword in title:
                            all_tenders.append({
                                'title': title,
                                'budget': budget,
                                'unit': unit or '未提供',
                                'date': record.get('公告日期') or '',
                                'source': f'政府開放資料 (資料集 {dataset_id})'
                            })
                
                print(f"   ✅ 資料集 {dataset_id}：找到 {len(all_tenders)} 筆")
                
        except Exception as e:
            print(f"   ⚠️ 資料集 {dataset_id} 無法存取：{e}")
    
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
    """產生 HTML 報告（可選）"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>標案查詢結果</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .budget {{ color: #e74c3c; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>🏗️ 標案查詢結果</h1>
    <p>查詢時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>找到 <strong>{len(tenders)}</strong> 筆符合條件的標案</p>
    
    <table>
        <tr>
            <th>#</th>
            <th>標案名稱</th>
            <th>預算金額</th>
            <th>招標機關</th>
            <th>公告日期</th>
            <th>資料來源</th>
        </tr>
"""
    
    for i, t in enumerate(tenders, 1):
        html += f"""
        <tr>
            <td>{i}</td>
            <td>{t['title']}</td>
            <td class="budget">${t['budget']:,}</td>
            <td>{t['unit']}</td>
            <td>{t.get('date', 'N/A')}</td>
            <td>{t.get('source', 'N/A')}</td>
        </tr>
"""
    
    html += """
    </table>
</body>
</html>
"""
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ HTML 報告已儲存至 {filename}")

def main():
    """主程式"""
    print("="*60)
    print("🏗️ 政府開放資料平台 - 標案查詢工具")
    print("="*60)
    
    # 查詢標案
    tenders = fetch_tenders_from_gov_data(
        keyword="景觀",
        max_budget=36000000,
        limit=50
    )
    
    # 如果找不到，嘗試放寬條件
    if not tenders:
        print("\n⚠️ 沒有找到符合條件的標案，嘗試放寬關鍵字...")
        tenders = fetch_tenders_from_gov_data(
            keyword="工程",  # 放寬關鍵字
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
            print(f"   公告日期：{t.get('date', 'N/A')}")
    else:
        print("\n⚠️ 沒有找到符合條件的標案")
        print("建議：")
        print("  1. 嘗試不同的關鍵字（如：工程、採購、新建）")
        print("  2. 放寬預算上限")
        print("  3. 直接至政府電子採購網查詢：https://web.pcc.gov.tw")

if __name__ == "__main__":
    main()
