import asyncio
import aiohttp
import json
import os
from typing import Dict, Any

# Load Raven Username data (comprehensive dataset)
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'usernames.json')
try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        RAVEN_DATA = json.load(f)
        SITES = RAVEN_DATA.get("sites", {})
except Exception as e:
    SITES = {}
    print(f"Failed to load OSINT data: {e}")

async def check_site_async(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, site_name: str, site: Dict[str, Any], username: str) -> Dict[str, Any]:
    url_template = site.get("url")
    if not url_template or "{username}" not in url_template:
        # Ignore sites that don't have the username in the URL (like POST API checks)
        # to prevent false positives from generic homepages like discord.com
        return {"source": site_name, "url": "", "exists": False, "error": "Unsupported check type", "confidence": 0.0}
        
    url = url_template.replace("{username}", username)
    display_url = site.get("urlMain", url)
    
    headers = site.get("headers", {})
    if 'User-Agent' not in headers:
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
    check_type = site.get("checkType", "status_code")
    presenseStrs = site.get("presenseStrs", [])
    absenceStrs = site.get("absenceStrs", [])
    
    async with semaphore:
        try:
            async with session.get(url, headers=headers, timeout=5.0, allow_redirects=True) as response:
                status = response.status
                html = ""
                try:
                    html = await response.text()
                except:
                    pass
                    
                exists = True
                
                # Check 1: Status Code
                if status >= 400:
                    exists = False
                    
                # Check 2: Redirects
                final_url = str(response.url)
                def get_path(u):
                    return u.split("://")[-1].split("?")[0].rstrip("/")
                
                if get_path(url) != get_path(final_url):
                    exists = False

                # Check 3: Content Validation
                if check_type == "message" or presenseStrs or absenceStrs:
                    is_valid_content = True
                    
                    if presenseStrs:
                        for pstr in presenseStrs:
                            if pstr not in html:
                                is_valid_content = False
                                
                    if absenceStrs:
                        for astr in absenceStrs:
                            if astr in html:
                                is_valid_content = False
                                
                    if presenseStrs or absenceStrs:
                        # Only override to False. Never override a 404 (already False) back to True.
                        if not is_valid_content:
                            exists = False
                    else:
                        if status >= 400:
                            exists = False
                            
                # If there's an error status code but it somehow survived, kill it
                if status >= 400:
                    exists = False
                        
                if not exists:
                    return {
                        "source": site_name,
                        "url": url,
                        "exists": False,
                        "status_code": status,
                        "confidence": 0.0,
                        "error": f"HTTP {status} or content validation failed"
                    }

                return {
                    "source": site_name,
                    "url": url,
                    "exists": exists,
                    "status_code": status,
                    "confidence": 0.9 if exists else 0.0
                }
        except Exception as e:
            return {"source": site_name, "url": url, "exists": False, "error": str(e), "confidence": 0.0}

async def run_username_collection(username: str) -> list:
    # Aiohttp allows massive non-blocking concurrency safely!
    semaphore = asyncio.Semaphore(200) 
    
    # We use a custom connector to ignore SSL errors and avoid pooling limits
    connector = aiohttp.TCPConnector(limit=200, ssl=False)
    timeout = aiohttp.ClientTimeout(total=5.0)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [check_site_async(session, semaphore, site_name, site, username) for site_name, site in SITES.items() if site.get("url")]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for r in results:
            if isinstance(r, dict):
                valid_results.append(r)
                
        return valid_results
