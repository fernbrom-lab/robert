import os
import json
import re
import asyncio
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright

async def fetch_tenders_from_pcc_playwright(keyword: str = "景觀", max_budget: int = 36000000, limit: int = 30) -> List[Dict]:
    """
    使用 Playwright 從政府電子採購網抓取標案資料
    """
    tenders = []
    
    async with async_playwright() as p:
        # 啟動瀏覽器（無頭模式）
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f"   🔍 正在查詢：{keyword}")
            
            # 前往查詢頁面
            url = "https://web.pcc.gov.tw/tps/QueryTender.do"
            await page.goto(url, wait_until="networkidle")
            
            # 等待並填入查詢條件
            await page.wait_for_selector('input[name="tenderName"]', timeout=10000)
            await page.fill('input[name="tenderName"]', keyword)
            
            # 點擊查詢按鈕
            await page.click('input[value="查詢"]')
            
            # 等待結果表格載入
            await page.wait_for_selector('table', timeout=10000)
            
            # 解析表格內容
            rows = await page.query_selector_all('table tr')
            
            for row in rows:
                cells = await row.query_selector_all('td')
                if len(cells) >= 3:
                    title = await cells[0].inner_text()
                    budget_text = await cells[1].inner_text() if len(cells) > 1 else "0"
                    unit = await cells[2].inner_text() if len(cells) > 2 else ""
                    
                    budget = parse_budget(budget_text)
                    
                    if title and budget > 0 and budget <= max_budget:
                        tenders.append({
                            'title': title.strip(),
                            'budget': budget,
                            'unit': unit.strip() or '未提供',
                            'date': '',
                            'source': '政府電子採購網 (Playwright)'
                        })
            
            print(f"   ✅ 找到 {len(tenders)} 筆標案")
            
        except Exception as e:
            print(f"   ❌ 查詢發生錯誤：{e}")
            # 截圖除錯
            await page.screenshot(path="debug_screenshot.png")
            print(f"   💡 已儲存除錯截圖：debug_screenshot.png")
            
        finally:
            await browser.close()
    
    return tenders[:limit]

def parse_budget(value) -> int:
    """解析預算金額"""
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        clean = re.sub(r'[^\d]', '', value)
        return int(clean) if clean.isdigit() else 0
    return 0

async def main_async():
    """非同步主程式"""
    print("="*60)
    print("🏗️ 政府電子採購網 - 標案查詢工具 (Playwright 版)")
    print("="*60)
    
    keywords = ["景觀", "綠美化", "圍籬", "新建"]
    all_tenders = []
    seen_titles = set()
    
    for keyword in keywords:
        tenders = await fetch_tenders_from_pcc_playwright(keyword)
        for t in tenders:
            if t['title'] not in seen_titles:
                seen_titles.add(t['title'])
                all_tenders.append(t)
    
    # 儲存結果
    save_results(all_tenders)
    generate_html_report(all_tenders)
    
    if all_tenders:
        print(f"\n✅ 共找到 {len(all_tenders)} 筆標案")
    else:
        print("\n⚠️ 沒有找到標案")

def save_results(tenders, filename="tender_results.json"):
    result = {
        "query_time": datetime.now().isoformat(),
        "total_count": len(tenders),
        "tenders": tenders
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 結果已儲存至 {filename}")

def generate_html_report(tenders, filename="tender_report.html"):
    # ... (與之前相同的 HTML 生成邏輯) ...
    pass

if __name__ == "__main__":
    asyncio.run(main_async())
