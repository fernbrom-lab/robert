import requests
import json
import os
from datetime import datetime

def search_tenders_with_twinkle(keyword="景觀", limit=20):
    """使用 Twinkle Hub API 查詢標案"""
    
    api_key = os.environ.get('TWINKLE_API_KEY')
    if not api_key:
        print("❌ 錯誤：找不到 TWINKLE_API_KEY 環境變數")
        return []
    
    # Twinkle Hub MCP 端點
    url = "https://api.twinkleai.tw/mcp/"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 準備查詢指令（使用自然語言）
    query = f"""
    請幫我查詢政府採購標案，條件如下：
    1. 標案名稱包含關鍵字：「{keyword}」
    2. 預算金額低於 3600 萬
    3. 最近 30 天內公告的標案
    4. 請回傳 JSON 格式，包含：標案名稱、預算金額、招標機關、公告日期
    5. 最多回傳 {limit} 筆
    """
    
    payload = {
        "query": query,
        "format": "json"
    }
    
    try:
        print(f"📡 正在查詢：{keyword}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # 根據 Twinkle Hub 的回應格式解析（實際格式可能略有不同）
            if 'result' in data:
                return parse_twinkle_response(data['result'])
            elif 'data' in data:
                return parse_twinkle_response(data['data'])
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
        # 如果回應是字串，先轉為 JSON
        if isinstance(response_data, str):
            try:
                response_data = json.loads(response_data)
            except:
                # 可能是純文字，嘗試解析
                print("⚠️ 回應為文字格式，嘗試解析...")
                return parse_text_response(response_data)
        
        # 根據實際回應結構解析
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
    
    # 清理字串
    clean = re.sub(r'[^\d]', '', str(value))
    return int(clean) if clean.isdigit() else 0

def parse_text_response(text):
    """處理純文字回應（備用）"""
    tenders = []
    lines = text.split('\n')
    for line in lines:
        if '標案名稱' in line or '預算' in line:
            # 簡單解析，實際可能需要更複雜的邏輯
            pass
    return tenders

# 測試函數
if __name__ == "__main__":
    print("🧪 測試 Twinkle Hub API")
    print("="*50)
    
    # 查詢包含「景觀」的標案
    results = search_tenders_with_twinkle("景觀", limit=10)
    
    if results:
        print(f"\n✅ 找到 {len(results)} 筆標案：")
        for i, t in enumerate(results, 1):
            print(f"{i}. {t['title']}")
            print(f"   預算：${t['budget']:,} | 機關：{t['unit']} | 日期：{t['date']}")
            print()
    else:
        print("\n❌ 沒有找到標案")
