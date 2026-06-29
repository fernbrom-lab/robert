import os
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any

class TwinkleHubClient:
    """Twinkle Hub MCP 客戶端（加入除錯功能）"""
    
    def __init__(self, api_key: str, debug: bool = True):
        self.api_key = api_key
        self.base_url = "https://api.twinkleai.tw/mcp/"
        self.session_id = None
        self.request_id = 0
        self.debug = debug  # 加入除錯模式
    
    def _log(self, message: str, level: str = "INFO"):
        """除錯日誌"""
        if self.debug:
            print(f"[{level}] {message}")
    
    def _get_next_id(self) -> int:
        self.request_id += 1
        return self.request_id
    
    def _parse_sse_response(self, text: str) -> Optional[Dict]:
        """解析 SSE 格式的回應"""
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
            self._log(f"呼叫工具：{tool_name}，參數：{json.dumps(arguments, ensure_ascii=False)}")
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self._log(f"回應狀態碼：200")
                self._log(f"原始回應：{response.text[:500]}")
                
                result = self._parse_sse_response(response.text)
                if result:
                    self._log(f"解析後結果：{json.dumps(result, ensure_ascii=False)[:500]}")
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
        print("📡 嘗試取得所有資料領域...")
        result = self.call_tool("opendata-list_domains", {})
        
        if result:
            print(f"✅ list_domains 回應：{json.dumps(result, ensure_ascii=False)[:500]}")
        
        if result and 'result' in result:
            content = result['result'].get('content', [])
            if content and len(content) > 0:
                try:
                    data = json.loads(content[0]['text'])
                    print(f"✅ 取得 {len(data)} 個資料領域")
                    return data
                except Exception as e:
                    print(f"⚠️ 解析 domains 失敗：{e}")
                    print(f"   原始內容：{content[0]['text'][:200]}")
        return None
    
    def search_datasets(self, query: str, domain: str = None, limit: int = 10) -> Optional[List[Dict]]:
        """搜尋資料集（加入詳細除錯）"""
        arguments = {"query": query, "limit": limit}
        if domain:
            arguments["domain"] = domain
        
        print(f"📡 搜尋資料集：query='{query}', domain='{domain}', limit={limit}")
        result = self.call_tool("opendata-search_datasets", arguments)
        
        # 詳細印出原始回應
        if result:
            print(f"✅ search_datasets 原始回應：{json.dumps(result, ensure_ascii=False)[:800]}")
        
        if result and 'result' in result:
            content = result['result'].get('content', [])
            if content and len(content) > 0:
                try:
                    data = json.loads(content[0]['text'])
                    print(f"✅ 解析成功，找到 {len(data) if isinstance(data, list) else 'N/A'} 筆資料集")
                    return data
                except Exception as e:
                    print(f"⚠️ 解析 datasets 失敗：{e}")
                    print(f"   原始內容：{content[0]['text'][:300]}")
            else:
                print("⚠️ result 中沒有 content 欄位")
                print(f"   result 結構：{list(result['result'].keys())}")
        else:
            print("⚠️ result 中沒有 'result' 欄位")
            if result:
                print(f"   回應結構：{list(result.keys())}")
        
        return None
    
    def get_dataset(self, dataset_id: str) -> Optional[Dict]:
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
    api_key = os.environ.get('TWINKLE_API_KEY')
    if not api_key:
        print("❌ 錯誤：找不到 TWINKLE_API_KEY 環境變數")
        return []
    
    client = TwinkleHubClient(api_key, debug=True)
    
    if not client.initialize():
        print("❌ 初始化失敗，請檢查 API Key")
        return []
    
    # 先嘗試列出所有工具，確認連線正常
    print("\n🔧 列出所有可用工具...")
    tools = client.list_tools()
    if tools:
        print(f"✅ 可用工具：{tools}")
    else:
        print("⚠️ 無法取得工具列表")
    
    # 嘗試列出所有領域
    print("\n📂 列出所有資料領域...")
    domains = client.list_domains()
    if domains:
        print(f"✅ 找到 {len(domains)} 個領域")
        for d in domains[:5]:
            print(f"   - {d}")
    else:
        print("⚠️ 無法取得領域列表")
    
    # 搜尋資料集
    print(f"\n🔍 搜尋關鍵字：{keyword}")
    datasets = client.search_datasets(
        query=keyword,
        domain="procurement_subsidy",
        limit=5
    )
    
    if not datasets:
        print("❌ 找不到相關資料集")
        print("💡 嘗試不指定 domain 再搜尋一次...")
        datasets = client.search_datasets(
            query=f"{keyword} 採購 工程",
            domain=None,
            limit=5
        )
    
    if not datasets:
        print("❌ 仍然找不到資料集")
        return []
    
    print(f"✅ 找到 {len(datasets)} 個相關資料集")
    
    all_tenders = []
    
    for ds in datasets[:3]:
        dataset_id = ds.get('dataset_id')
        title = ds.get('title', '')
        print(f"\n📂 查詢資料集：{title}")
        print(f"   ID: {dataset_id}")
        
        if not dataset_id:
            continue
        
        rows = client.query_rows(
            dataset_id=dataset_id,
            where={"預算金額": {"$lte": max_budget}},
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
    import re
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        clean = re.sub(r'[^\d]', '', value)
        return int(clean) if clean.isdigit() else 0
    return 0


def save_results(tenders: List[Dict], filename: str = "tender_results.json"):
    result = {
        "query_time": datetime.now().isoformat(),
        "total_count": len(tenders),
        "tenders": tenders
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 結果已儲存至 {filename}")


def main():
    print("="*60)
    print("🧪 Twinkle Hub 標案查詢工具（除錯模式）")
    print("="*60)
    
    tenders = search_tenders(
        keyword="景觀",
        max_budget=36000000,
        limit=20
    )
    
    save_results(tenders)
    
    if tenders:
        print(f"\n✅ 共找到 {len(tenders)} 筆符合條件的標案：")
        for i, t in enumerate(tenders[:10], 1):
            print(f"\n{i}. {t['title']}")
            print(f"   預算金額：${t['budget']:,}")
            print(f"   招標機關：{t['unit']}")
    else:
        print("\n⚠️ 沒有找到符合條件的標案")


if __name__ == "__main__":
    main()
