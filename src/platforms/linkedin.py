import os, requests, logging

def fetch_data():
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    org_id = os.getenv("LINKEDIN_ORGANIZATION_ID")
    if not token or not org_id: return None
    
    url = "https://api.linkedin.com/v2/organizationalEntityShareStatistics"
    params = {"q": "organizationalEntity", "organizationalEntity": org_id}
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"LinkedIn API Error: {e}")
        return None
