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
    Prioritize recent post-level performance trends over only aggregate totals.
    
    Data: {json.dumps(raw_data)}
    """
    
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False}
    try:
        r = requests.post(url, json=payload, timeout=180)
        return r.json()['message']['content']
    except Exception as e:
        return f"AI Analysis failed: {e}"


def _safe_metric(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _truncate(text, limit=85):
    if not text:
        return "(no text)"
    cleaned = " ".join(str(text).split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def _escape_pipes(text):
    return text.replace("|", "\\|")


def _format_epoch_ms(epoch_ms):
    if not epoch_ms:
        return "N/A"
    try:
        return datetime.fromtimestamp(int(epoch_ms) / 1000).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return "N/A"

def main():
    print("--- Starting LinkedIn Analytics Bot ---")
    data = linkedin.fetch_data()
    if not data: return

    # 1. Get AI content (Handles Section 1 & 2)
    print("Generating AI Insights...")
    ai_content = get_ai_analysis(data)

    # 2. Prepare Notable Metrics (Section 3)
    stats = data.get("organization_share_statistics", {})
    recent_summary = data.get("recent_posts_summary", {})
    recent_posts = data.get("recent_posts", [])

    metrics_table = f"""
| Metric | Value |
| :--- | :--- |
| **Total Impressions** | {_safe_metric(stats.get('impressionCount')):,} |
| **Total Clicks** | {_safe_metric(stats.get('clickCount')):,} |
| **Total Likes** | {_safe_metric(stats.get('likeCount')):,} |
| **Comments** | {_safe_metric(stats.get('commentCount')):,} |
| **Shares** | {_safe_metric(stats.get('shareCount')):,} |
| **Unique Impressions** | {_safe_metric(stats.get('uniqueImpressionsCount')):,} |
| **Engagement Rate** | {float(stats.get('engagement', 0) or 0)*100:.2f}% |
"""

    recent_summary_table = f"""
| Metric | Value |
| :--- | :--- |
| **Posts Analyzed** | {_safe_metric(recent_summary.get('postsAnalyzed')):,} |
| **Recent Impressions** | {_safe_metric(recent_summary.get('impressionCount')):,} |
| **Recent Clicks** | {_safe_metric(recent_summary.get('clickCount')):,} |
| **Recent Likes** | {_safe_metric(recent_summary.get('likeCount')):,} |
| **Recent Comments** | {_safe_metric(recent_summary.get('commentCount')):,} |
| **Recent Shares** | {_safe_metric(recent_summary.get('shareCount')):,} |
| **Recent Engagement Rate** | {float(recent_summary.get('engagement', 0) or 0)*100:.2f}% |
"""

    recent_posts_rows = []
    for idx, post in enumerate(recent_posts, start=1):
        pstats = post.get("statistics", {})
        recent_posts_rows.append(
            "| {idx} | {date} | {text} | {impressions:,} | {clicks:,} | {likes:,} | {comments:,} | {shares:,} | {engagement:.2f}% |".format(
                idx=idx,
                date=_format_epoch_ms(post.get("createdTime")),
                text=_escape_pipes(_truncate(post.get("text"))),
                impressions=_safe_metric(pstats.get("impressionCount")),
                clicks=_safe_metric(pstats.get("clickCount")),
                likes=_safe_metric(pstats.get("likeCount")),
                comments=_safe_metric(pstats.get("commentCount")),
                shares=_safe_metric(pstats.get("shareCount")),
                engagement=float(pstats.get("engagement", 0) or 0) * 100,
            )
        )

    recent_posts_table = "\n".join(
        [
            "| # | Date | Post Preview | Impressions | Clicks | Likes | Comments | Shares | Engagement |",
            "| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
            *(recent_posts_rows or ["| - | - | No recent posts found | 0 | 0 | 0 | 0 | 0 | 0.00% |"]),
        ]
    )

    # 3. Assemble the Final Markdown
    report_md = f"""# LinkedIn Performance Report ({datetime.now().strftime('%Y-%m-%d')})

## 1. Strategic Analysis
{ai_content}

## 2. Notable Metrics
{metrics_table}

## 3. Recent Posts Snapshot
{recent_summary_table}

## 4. Recent Posts Detail
{recent_posts_table}

## 5. Raw Data Audit
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
