import requests
import json
from datetime import datetime, timedelta

def fetch_realtime_tenders():
    """從 PCC-API 抓取真實標案"""
    tenders = []
    
    try:
        print("📡 從 PCC-API 抓取真實標案...")
        
        # 使用 PCC-API 端點
        api_url = "https://pcc-api.openfun.app/api/getinfo"
        
        # 設定查詢參數（可依需求調整）
        params = {
            # 可選：指定日期，格式 YYYY-MM-DD
            # "date": datetime.now().strftime("%Y-%m-%d"),
            # 可選：指定機關名稱
            # "unit": "台北市政府",
            # 可選：指定關鍵字
            # "keyword": "景觀"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # 根據 PCC-API 的回應格式解析
            # 實際格式可能需要根據 API 回應調整
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and 'records' in data:
                records = data['records']
            else:
                records = data.get('data', []) if isinstance(data, dict) else []
            
            print(f"  ✅ API 回應成功，取得 {len(records)} 筆資料")
            
            for item in records[:50]:  # 限制筆數避免過多
                # 根據實際 API 回應欄位名稱調整
                title = item.get('title') or item.get('標案名稱') or item.get('案名', '')
                budget_str = item.get('budget') or item.get('預算金額') or item.get('price', '0')
                unit = item.get('unit') or item.get('機關名稱') or item.get('unit_name', '')
                
                # 清理預算金額（只保留數字）
                import re
                budget_clean = re.sub(r'[^0-9]', '', str(budget_str))
                budget = int(budget_clean) if budget_clean.isdigit() else 0
                
                if title and budget > 0:
                    tenders.append({
                        'title': title,
                        'budget': budget,
                        'unit': unit or '未知機關',
                        'source': 'PCC-API 真實標案'
                    })
            
            print(f"  ✅ 成功解析 {len(tenders)} 筆有效標案")
            
        else:
            print(f"  ⚠️ API 回應錯誤: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("  ⚠️ API 請求超時")
    except requests.exceptions.ConnectionError:
        print("  ⚠️ 無法連線至 API")
    except Exception as e:
        print(f"  ⚠️ 抓取標案時發生錯誤: {e}")
    
    return tenders
