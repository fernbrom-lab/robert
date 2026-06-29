import requests
import json
import os
from datetime import datetime

def search_tenders_with_twinkle(keyword="景觀", limit=20):
    """使用 Twinkle Hub REST API 查詢標案（替代方案）"""
    
    api_key = os.environ.get('TWINKLE_API_KEY')
    if not api_key:
        print("❌ 錯誤：找不到 TWINKLE_API_KEY 環境變數")
        return []
    
    # 嘗試使用 REST API 端點（根據 Twinkle Hub 文件調整）
    endpoints = [
        "https://api.twinkleai.tw/api/tenders",
        "https://api.twinkleai.tw/v1/tenders", 
        "https://hub.twinkleai.tw/api/search",
        "https://api.twinkleai.tw/tenders"  # 另一個可能的端點
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    params = {
        "keyword": keyword,
        "limit": limit,
        "max_budget": 36000000
    }
    
    for url in endpoints:
        try:
            print(f"📡 嘗試 REST API：{url}")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ REST API 回應成功")
                return parse_twinkle_response(data)
            else:
                print(f"   ⚠️ {url} 回應：{response.status_code}")
        except Exception as e:
            print(f"   ⚠️ {url} 錯誤：{e}")
    
    # 如果 REST API 都失敗，嘗試使用備用方案
    print("\n⚠️ REST API 無法使用，嘗試使用備用方案...")
    return search_tenders_fallback(keyword, limit)

def search_tenders_fallback(keyword="景觀", limit=20):
    """備用方案：使用政府開放資料平台"""
    import requests
    import re
    
    print("📡 使用備用方案：政府開放資料平台")
    
    # 嘗試使用政府開放資料平台
    url = "https://data.gov.tw/api/v1/rest/dataset/16834"  # 公共工程標案
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # 解析政府資料平台的回應
            tenders = []
            records = data.get('result', {}).get('records', [])
            
            for record in records[:limit]:
                title = record.get('標案名稱', '')
                budget_str = record.get('預算金額', '0')
                budget = re.sub(r'[^\d]', '', str(budget_str))
                budget = int(budget) if budget.isdigit() else 0
                unit = record.get('招標機關', '')
                
                if title and budget > 0 and budget <= 36000000:
                    if keyword in title or any(k in title for k in ["景觀", "綠美化", "圍籬", "新建", "公廁"]):
                        tenders.append({
                            'title': title,
                            'budget': budget,
                            'unit': unit,
                            'date': record.get('公告日期', ''),
                            'source': '政府開放資料'
                        })
            
            print(f"✅ 從政府開放資料平台找到 {len(tenders)} 筆標案")
            return tenders
            
    except Exception as e:
        print(f"⚠️ 備用方案失敗：{e}")
    
    return []

def parse_twinkle_response(response_data):
    """解析 Twinkle Hub 回傳的標案資料"""
    tenders = []
    
    try:
        if isinstance(response_data, str):
            try:
                response_data = json.loads(response_data)
            except:
                return tenders
        
        records = []
        if isinstance(response_data, list):
            records = response_data
        elif isinstance(response_data, dict):
            for key in ['records', 'data', 'results', 'items', 'tenders']:
                if key in response_data and isinstance(response_data[key], list):
                    records = response_data[key]
                    break
            if not records and 'tender' in response_data:
                records = [response_data['tender']]
        
        for item in records:
            tender = {
                'title': item.get('title') or item.get('標案名稱') or item.get('name', ''),
                'budget': parse_budget(item.get('budget') or item.get('預算金額') or item.get('price', '0')),
                'unit': item.get('unit') or item.get('招標機關') or item.get('agency', ''),
                'date': item.get('date') or item.get('公告日期') or item.get('publish_date', ''),
                'source': 'Twinkle Hub'
            }
            
            if tender['title'] and tender['budget'] > 0:
                tenders.append(tender)
                
    except Exception as e:
        print(f"⚠️ 解析回應時發生錯誤：{e}")
    
    return tenders

def parse_budget(value):
    """解析預算金額"""
    import re
    if isinstance(value, (int, float)):
        return int(value)
    
    clean = re.sub(r'[^\d]', '', str(value))
    return int(clean) if clean.isdigit() else 0

def save_results(tenders, filename="tender_results.json"):
    """儲存查詢結果到 JSON 檔案"""
    result = {
        "query_time": datetime.now().isoformat(),
        "total_count": len(tenders),
        "tenders": tenders
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 結果已儲存至 {filename}")

if __name__ == "__main__":
    print("🧪 測試 Twinkle Hub API")
    print("="*50)
    
    results = search_tenders_with_twinkle("景觀", limit=10)
    
    save_results(results)
    
    if results:
        print(f"\n✅ 找到 {len(results)} 筆標案：")
        for i, t in enumerate(results, 1):
            print(f"{i}. {t['title']}")
            print(f"   預算：${t['budget']:,} | 機關：{t['unit']} | 日期：{t.get('date', 'N/A')}")
    else:
        print("\n⚠️ 沒有找到標案，但已產生結果檔案")
