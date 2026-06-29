import requests
import json
import os
from datetime import datetime

def search_tenders_with_twinkle(keyword="景觀", limit=20):
    # ... (你的 API 呼叫程式碼) ...

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
