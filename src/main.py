import os, json, requests
from datetime import datetime
from dotenv import load_dotenv
from platforms import linkedin

load_dotenv()

def get_ai_analysis(raw_data):
    url = f"{os.getenv('OLLAMA_BASE_URL').rstrip('/')}/api/chat"
    model = os.getenv("OLLAMA_MODEL", "llama3")
    
    prompt = f"""
    Analyze this LinkedIn data and provide two specific sections:
    1. EXECUTIVE SUMMARY: A detailed summary of performance.
    2. STRATEGIC ACTION PLAN: What topics to focus on next and specific steps to take.
    
    Data: {json.dumps(raw_data)}
    """
    
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False}
    try:
        r = requests.post(url, json=payload, timeout=180)
        return r.json()['message']['content']
    except Exception as e:
        return f"AI Analysis failed: {e}"

def main():
    print("--- Starting LinkedIn Analytics Bot ---")
    data = linkedin.fetch_data()
    if not data: return

    # 1. Get AI content (Handles Section 1 & 2)
    print("Generating AI Insights...")
    ai_content = get_ai_analysis(data)

    # 2. Prepare Notable Metrics (Section 3)
    stats = data.get('elements', [{}])[0].get('totalShareStatistics', {})
    metrics_table = f"""
| Metric | Value |
| :--- | :--- |
| **Total Impressions** | {stats.get('impressionCount', 0):,} |
| **Total Clicks** | {stats.get('clickCount', 0):,} |
| **Total Likes** | {stats.get('likeCount', 0):,} |
| **Comments** | {stats.get('commentCount', 0):,} |
| **Engagement Rate** | {float(stats.get('engagement', 0))*100:.2f}% |
"""

    # 3. Assemble the Final Markdown
    report_md = f"""# LinkedIn Performance Report ({datetime.now().strftime('%Y-%m-%d')})

## 1. Strategic Analysis
{ai_content}

## 2. Notable Metrics
{metrics_table}

## 3. Raw Data Audit
```json
{json.dumps(data, indent=4)}
```
"""

    # 4. Save to file
    filename = f"report-{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(filename, "w") as f:
        f.write(report_md)
    
    print(f"--- SUCCESS: {filename} generated in current folder ---")

if __name__ == "__main__":
    main()
