def search_tenders_with_twinkle(keyword="景觀", limit=20):
    """使用 Twinkle Hub API 查詢標案"""
    
    api_key = os.environ.get('TWINKLE_API_KEY')
    if not api_key:
        print("❌ 錯誤：找不到 TWINKLE_API_KEY 環境變數")
        return []
    
    url = "https://api.twinkleai.tw/mcp/"
    
    # 修改這裡：Accept 標頭要同時包含兩種格式
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"  # 關鍵修正
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
            
            # 解析 JSON-RPC 回應
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
