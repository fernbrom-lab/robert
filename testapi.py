import requests
import json
from datetime import datetime
import time

def test_pcc_api_endpoints():
    """測試 PCC-API 的各個可能端點，找出能獲取標案資料的途徑"""
    
    print("="*60)
    print("🧪 開始測試 PCC-API 各端點...")
    print("="*60)
    
    base_url = "https://pcc-api.openfun.app"
    
    # 定義要測試的端點與可能的參數組合
    test_cases = [
        # 基本端點
        {"name": "根路徑", "url": "/"},
        {"name": "API 根路徑", "url": "/api"},
        
        # 可能的列表端點
        {"name": "標案列表", "url": "/api/tenders"},
        {"name": "標案列表 (複數)", "url": "/api/tender/list"},
        {"name": "紀錄列表", "url": "/api/records"},
        {"name": "搜尋列表", "url": "/api/search"},
        {"name": "所有標案", "url": "/api/all"},
        {"name": "最新標案", "url": "/api/latest"},
        
        # 加上查詢參數的端點
        {"name": "標案列表 + 日期", "url": "/api/tenders", "params": {"date": "2026-06-23"}},
        {"name": "搜尋 + 關鍵字", "url": "/api/search", "params": {"keyword": "景觀"}},
        {"name": "搜尋 + 日期", "url": "/api/search", "params": {"date": "2026-06-23"}},
        
        # 之前確認可用的端點（對照組）
        {"name": "資訊統計 (已知可用)", "url": "/api/getinfo"},
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    successful_endpoints = []
    
    for case in test_cases:
        url = f"{base_url}{case['url']}"
        params = case.get('params', {})
        
        try:
            print(f"\n📡 測試: {case['name']}")
            print(f"   URL: {url}")
            if params:
                print(f"   參數: {params}")
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            print(f"   狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    data_preview = str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
                    print(f"   回應內容預覽: {data_preview}")
                    
                    # 檢查是否包含標案資料
                    has_records = False
                    record_count = 0
                    
                    if isinstance(data, list):
                        has_records = len(data) > 0
                        record_count = len(data)
                    elif isinstance(data, dict):
                        # 檢查常見的資料容器鍵值
                        for key in ['records', 'data', 'results', 'items', 'tenders', 'list']:
                            if key in data and isinstance(data[key], list):
                                has_records = True
                                record_count = len(data[key])
                                break
                        # 檢查是否直接就是標案物件
                        if not has_records and 'title' in data and 'budget' in data:
                            has_records = True
                            record_count = 1
                    
                    if has_records:
                        print(f"   ✅ 成功！找到 {record_count} 筆標案資料")
                        successful_endpoints.append({
                            'name': case['name'],
                            'url': url,
                            'params': params,
                            'record_count': record_count,
                            'sample': data[0] if isinstance(data, list) and data else data
                        })
                    else:
                        print(f"   ℹ️ 回應成功但沒有標案資料")
                        
                except json.JSONDecodeError:
                    print(f"   ⚠️ 回應不是有效的 JSON")
                    print(f"   原始回應: {response.text[:100]}...")
            else:
                print(f"   ❌ 回應失敗")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ 請求超時")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 連線失敗")
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")
        
        # 避免請求過於頻繁
        time.sleep(0.5)
    
    # 總結結果
    print("\n" + "="*60)
    print("📊 測試總結")
    print("="*60)
    
    if successful_endpoints:
        print("\n✅ 找到以下可用的端點：")
        for ep in successful_endpoints:
            print(f"\n  📌 {ep['name']}")
            print(f"     URL: {ep['url']}")
            if ep['params']:
                print(f"     參數: {ep['params']}")
            print(f"     資料筆數: {ep['record_count']}")
            if ep['sample']:
                print(f"     範例資料: {json.dumps(ep['sample'], ensure_ascii=False, indent=2)[:300]}...")
    else:
        print("\n❌ 沒有找到能回傳標案資料的端點")
        print("\n💡 建議：")
        print("   1. 檢查 API 是否需要認證或 API Key")
        print("   2. 嘗試不同的參數組合")
        print("   3. 查看 API 官方文件（如果有）")
        print("   4. 考慮使用其他資料來源（如政府開放資料平台）")
    
    return successful_endpoints

def test_single_tender():
    """測試查詢單一標案（使用已知的範例）"""
    print("\n" + "="*60)
    print("🔍 測試查詢單一標案")
    print("="*60)
    
    # 使用範例中的參數（從搜尋結果中找到的）
    test_url = "https://pcc-api.openfun.app/api/tender"
    params = {
        "unit_id": "3.97.8.24",  # 機關代碼範例
        "job_number": "101101201"  # 標案編號範例
    }
    
    try:
        print(f"\n📡 查詢單一標案...")
        print(f"   URL: {test_url}")
        print(f"   參數: {params}")
        
        response = requests.get(test_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 查詢成功！")
            print(f"   回應內容: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
            return data
        else:
            print(f"   ❌ 查詢失敗，狀態碼: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        return None

if __name__ == "__main__":
    # 執行測試
    results = test_pcc_api_endpoints()
    
    # 測試單一標案查詢
    single_result = test_single_tender()
    
    # 提供後續建議
    print("\n" + "="*60)
    print("💡 後續建議")
    print("="*60)
    
    if results:
        print("\n🎯 找到可用端點！請根據上述結果修改您的 `fetch_realtime_tenders()` 函數：")
        print("   1. 將 `api_url` 改成成功的端點 URL")
        print("   2. 調整資料解析邏輯，對應正確的資料結構")
    else:
        print("\n⚠️ 沒有找到標案列表端點，建議以下替代方案：")
        print("   1. 使用政府資料開放平台 (data.gov.tw)")
        print("   2. 考慮從政府電子採購網直接爬取（需注意相關規範）")
        print("   3. 使用其他第三方服務如 Twinkle Hub")
