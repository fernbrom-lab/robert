import requests
import json
import os
from datetime import datetime

def search_tenders_with_twinkle(keyword="景觀", limit=20):
    """使用 Twinkle Hub API 查詢標案"""
    # 這裡是函數主體，必須縮排
    api_key = os.environ.get('TWINKLE_API_KEY')
    if not api_key:
        print("❌ 錯誤：找不到 TWINKLE_API_KEY 環境變數")
        return []
    
    url = "https://api.twinkleai.tw/mcp/"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    # Twinkle Hub 使用 JSON-RPC 格式
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "search_tenders",
            "arguments": {
                "keyword": keyword,
                "max_budget": 36000000,
                "limit": limit,
                "days": 30
            }
        },
        "id": 1
    }
    
    try:
        print(f"📡 正在查詢：{keyword}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 回應成功")
            
            if 'result' in data:
                return parse_twinkle_response(data['result'])
            elif 'error' in data:
                print(f"⚠️ API 錯誤：{data['error'].get('message', '未知錯誤')}")
                return []
            else:
                print(f"⚠️ 無法解析回應：{json.dumps(data, ensure_ascii=False)[:200]}...")
                return []
        else:
            print(f"❌ API 請求失敗：{response.status_code}")
            print(f"   回應：{response.text[:200]}")
            return []
            
    except Exception as e:
        print(f"❌ 發生錯誤：{e}")
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
    """解析預算金額（移除千分位、貨幣符號等）"""
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
    
    # 查詢標案
    results = search_tenders_with_twinkle("景觀", limit=10)
    
    # 無論結果如何，都儲存檔案
    save_results(results)
    
    if results:
        print(f"\n✅ 找到 {len(results)} 筆標案：")
        for i, t in enumerate(results, 1):
            print(f"{i}. {t['title']}")
            print(f"   預算：${t['budget']:,} | 機關：{t['unit']}")
    else:
        print("\n⚠️ 沒有找到標案，但已產生結果檔案")
