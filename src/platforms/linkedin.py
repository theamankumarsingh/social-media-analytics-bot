import os
from datetime import datetime

import requests


def _build_org_urn(org_id):
    if org_id.startswith("urn:li:organization:"):
        return org_id
    return f"urn:li:organization:{org_id}"


def _build_share_urn(share_id):
    value = str(share_id or "").strip()
    if not value:
        return ""
    if value.startswith("urn:li:share:"):
        return value
    return f"urn:li:share:{value}"


def _linkedin_get(url, token, params):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def _fetch_organization_share_stats(token, org_urn):
    url = "https://api.linkedin.com/v2/organizationalEntityShareStatistics"
    params = {"q": "organizationalEntity", "organizationalEntity": org_urn}
    return _linkedin_get(url, token, params)


def _fetch_recent_shares(token, org_urn, limit):
    url = "https://api.linkedin.com/v2/shares"
    params = {
        "q": "owners",
        "owners": org_urn,
        "sortBy": "LAST_MODIFIED",
        "count": limit,
        "start": 0,
    }
    response = _linkedin_get(url, token, params)
    return response.get("elements", [])


def _fetch_share_statistics(token, org_urn, share_urn):
    url = "https://api.linkedin.com/v2/organizationalEntityShareStatistics"
    params = {
        "q": "organizationalEntity",
        "organizationalEntity": org_urn,
        "shares[0]": share_urn,
    }
    response = _linkedin_get(url, token, params)
    elements = response.get("elements", [])
    if not elements:
        return {}
    return elements[0].get("totalShareStatistics", {})


def _extract_post_text(share):
    commentary = (
        share.get("text", {})
        .get("text")
        or share.get("shareCommentary", {})
        .get("text")
        or ""
    )
    return commentary.strip()


def _parse_int_env(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def fetch_data():
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    org_id = os.getenv("LINKEDIN_ORGANIZATION_ID")
    if not token or not org_id:
        return None

    org_urn = _build_org_urn(org_id)
    # Fetch up to N recent posts; LinkedIn may return fewer when fewer posts exist.
    recent_limit = max(1, _parse_int_env("LINKEDIN_RECENT_POST_MAX", 25))

    try:
        org_stats_response = _fetch_organization_share_stats(token, org_urn)
        org_elements = org_stats_response.get("elements", [])
        org_totals = (org_elements[0] if org_elements else {}).get("totalShareStatistics", {})

        recent_shares = _fetch_recent_shares(token, org_urn, recent_limit)
        recent_posts = []
        recent_summary = {
            "postsAnalyzed": 0,
            "impressionCount": 0,
            "clickCount": 0,
            "likeCount": 0,
            "commentCount": 0,
            "shareCount": 0,
            "engagement": 0.0,
        }

        for share in recent_shares:
            share_urn = _build_share_urn(share.get("id"))
            if not share_urn:
                continue

            try:
                post_stats = _fetch_share_statistics(token, org_urn, share_urn)
            except Exception as post_err:
                # Continue building the report even if one post's stats request fails.
                print(f"LinkedIn API warning for {share_urn}: {post_err}")
                post_stats = {}

            post = {
                "shareUrn": share_urn,
                "createdTime": share.get("created", {}).get("time"),
                "lastModifiedTime": share.get("lastModified", {}).get("time"),
                "text": _extract_post_text(share),
                "visibility": share.get("visibility", {}),
                "lifecycleState": share.get("lifecycleState"),
                "distribution": share.get("distribution", {}),
                "statistics": post_stats,
            }
            recent_posts.append(post)

            recent_summary["postsAnalyzed"] += 1
            recent_summary["impressionCount"] += int(post_stats.get("impressionCount", 0) or 0)
            recent_summary["clickCount"] += int(post_stats.get("clickCount", 0) or 0)
            recent_summary["likeCount"] += int(post_stats.get("likeCount", 0) or 0)
            recent_summary["commentCount"] += int(post_stats.get("commentCount", 0) or 0)
            recent_summary["shareCount"] += int(post_stats.get("shareCount", 0) or 0)

        if recent_summary["impressionCount"] > 0:
            interactions = (
                recent_summary["clickCount"]
                + recent_summary["likeCount"]
                + recent_summary["commentCount"]
                + recent_summary["shareCount"]
            )
            recent_summary["engagement"] = interactions / recent_summary["impressionCount"]

        return {
            "generatedAt": datetime.utcnow().isoformat() + "Z",
            "organizationUrn": org_urn,
            "organization_share_statistics": org_totals,
            "organization_share_statistics_raw": org_stats_response,
            "recent_posts": recent_posts,
            "recent_posts_summary": recent_summary,
        }
    except Exception as e:
        print(f"LinkedIn API Error: {e}")
        return None
