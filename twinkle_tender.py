import os
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any

class TwinkleHubClient:
    """Twinkle Hub MCP 客戶端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twinkleai.tw/mcp/"
        self.session_id = None
        self.request_id = 0
        
    def _get_next_id(self) -> int:
        """取得下一個請求 ID"""
        self.request_id += 1
        return self.request_id
    
    def _parse_sse_response(self, text: str) -> Optional[Dict]:
        """解析 SSE (Server-Sent Events) 格式的回應"""
        lines = text.strip().split('\n')
        for line in reversed(lines):
            if line.startswith('data: '):
                data_str = line[6:]
                if data_str == '[DONE]':
                    continue
                try:
                    return json.loads(data_str)
                except:
                    continue
        return None
    
    def initialize(self) -> bool:
        """步驟 1：初始化 MCP 連線，取得 Session ID"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json"
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "twinkle-tender-client",
                    "version": "1.0.0"
                }
            }
        }
        
        try:
            print("🔑 正在初始化 Twinkle Hub 連線...")
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self.session_id = response.headers.get('mcp-session-id')
                if self.session_id:
                    print(f"✅ 初始化成功，Session ID: {self.session_id[:20]}...")
                    return True
                else:
                    print("⚠️ 初始化成功但未取得 Session ID")
                    return False
            else:
                print(f"❌ 初始化失敗：{response.status_code}")
                print(f"   回應：{response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ 初始化發生錯誤：{e}")
            return False
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict]:
        """步驟 2：使用已建立的 session 呼叫 MCP 工具"""
        if not self.session_id:
            print("❌ 尚未初始化，請先呼叫 initialize()")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "mcp-session-id": self.session_id
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            print(f"📡 呼叫工具：{tool_name}")
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = self._parse_sse_response(response.text)
                if result:
                    return result
                else:
                    print("⚠️ 無法解析 SSE 回應")
                    return None
            else:
                print(f"❌ 工具呼叫失敗：{response.status_code}")
                print(f"   回應：{response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ 工具呼叫發生錯誤：{e}")
            return None
    
    def list_tools(self) -> Optional[List[str]]:
        """列出所有可用的工具"""
        result = self.call_tool("tools/list", {})
        if result and 'result' in result:
            tools = result['result'].get('tools', [])
            return [t.get('name') for t in tools]
        return None
    
    def list_domains(self) -> Optional[List[Dict]]:
        """列出所有資料領域"""
        result = self.call_tool("opendata-list_domains", {})
        if result and 'result' in result:
            content = result['result'].get('content', [])
            if content and len(content) > 0:
                try:
                    return json.loads(content[0]['text'])
                except:
                    pass
        return None
    
    def search_datasets(self, query: str, domain: str = None, limit: int = 10) -> Optional[List[Dict]]:
        """搜尋資料集"""
        arguments = {"query": query, "limit": limit}
        if domain:
            arguments["domain"] = domain
        
        result = self.call_tool("opendata-search_datasets", arguments)
        if result and 'result' in result:
            content = result['result'].get('content', [])
            if content and len(content) > 0:
                try:
                    return json.loads(content[0]['text'])
                except:
                    pass
        return None
    
    def get_dataset(self, dataset_id: str) -> Optional[Dict]:
        """取得資料集詳細資訊"""
        result = self.call_tool("opendata-get_dataset", {"dataset_id": dataset_id})
        if result and 'result' in result:
            content = result['result'].get('content', [])
            if content and len(content) > 0:
                try:
                    return json.loads(content[0]['text'])
                except:
                    pass
        return None
    
    def query_rows(self, dataset_id: str, where: Dict = None, limit: int = 100) -> Optional[List[Dict]]:
        """查詢資料集中的資料列"""
        arguments = {"dataset_id": dataset_id, "limit": limit}
        if where:
            arguments["where"] = where
        
        result = self.call_tool("opendata-query_rows", arguments)
        if result and 'result' in result:
            content = result['result'].get('content', [])
            if content and len(content) > 0:
                try:
                    return json.loads(content[0]['text'])
                except:
                    pass
        return None


def search_tenders(keyword: str = "景觀", max_budget: int = 36000000, limit: int = 20):
    """
    搜尋符合條件的標案
    """
    api_key = os.environ.get('TWINKLE_API_KEY')
    if not api_key:
        print("❌ 錯誤：找不到 TWINKLE_API_KEY 環境變數")
        return []
    
    client = TwinkleHubClient(api_key)
    
    # 步驟 1：初始化
    if not client.initialize():
        print("❌ 初始化失敗，請檢查 API Key")
        return []
    
    # 步驟 2：搜尋採購相關資料集
    print(f"\n🔍 搜尋關鍵字：{keyword}")
    datasets = client.search_datasets(
        query=f"{keyword} 政府採購 工程標案",
        domain="procurement_subsidy",
        limit=5
    )
    
    if not datasets:
        print("❌ 找不到相關資料集")
        return []
    
    print(f"✅ 找到 {len(datasets)} 個相關資料集")
    
    # 步驟 3：從資料集中查詢標案
    all_tenders = []
    
    for ds in datasets[:3]:  # 只處理前 3 個資料集
        dataset_id = ds.get('dataset_id')
        title = ds.get('title', '')
        print(f"\n📂 查詢資料集：{title}")
        print(f"   ID: {dataset_id}")
        
        if not dataset_id:
            continue
        
        # 查詢符合條件的資料列
        where = {
            "預算金額": {"$lte": max_budget}
        }
        
        rows = client.query_rows(
            dataset_id=dataset_id,
            where=where,
            limit=limit
        )
        
        if rows:
            print(f"   ✅ 找到 {len(rows)} 筆資料")
            for row in rows:
                if isinstance(row, dict):
                    tender = {
                        'title': row.get('標案名稱') or row.get('title') or row.get('案名', ''),
                        'budget': parse_budget(row.get('預算金額') or row.get('budget') or row.get('price', 0)),
                        'unit': row.get('招標機關') or row.get('unit') or row.get('機關名稱', ''),
                        'date': row.get('公告日期') or row.get('date') or '',
                        'source': f'Twinkle Hub - {title[:30]}'
                    }
                    if tender['title'] and tender['budget'] > 0:
                        all_tenders.append(tender)
        else:
            print(f"   ⚠️ 此資料集無符合條件的資料")
    
    return all_tenders


def parse_budget(value) -> int:
    """解析預算金額"""
    import re
    if isinstance(value, (int, float)):
        return int(value)
    
    if isinstance(value, str):
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


def main():
    """主程式"""
    print("="*60)
    print("🧪 Twinkle Hub 標案查詢工具")
    print("="*60)
    
    # 查詢標案
    tenders = search_tenders(
        keyword="景觀",
        max_budget=36000000,
        limit=20
    )
    
    # 儲存結果
    save_results(tenders)
    
    # 顯示結果
    if tenders:
        print(f"\n✅ 共找到 {len(tenders)} 筆符合條件的標案：")
        for i, t in enumerate(tenders[:10], 1):
            print(f"\n{i}. {t['title']}")
            print(f"   預算金額：${t['budget']:,}")
            print(f"   招標機關：{t['unit']}")
            print(f"   公告日期：{t.get('date', 'N/A')}")
            print(f"   資料來源：{t.get('source', 'N/A')}")
        
        if len(tenders) > 10:
            print(f"\n... 還有 {len(tenders) - 10} 筆標案，請查看完整結果檔案")
    else:
        print("\n⚠️ 沒有找到符合條件的標案")
        print("建議：")
        print("  1. 調整關鍵字（嘗試：工程、新建、採購）")
        print("  2. 放寬預算上限")
        print("  3. 檢查 API Key 是否有效")


if __name__ == "__main__":
    main()
