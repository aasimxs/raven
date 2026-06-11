import asyncio
import aiohttp
import json
import hashlib
import os
import urllib.parse
from typing import Dict, Any

# Load email sites db
SITES_FILE = os.path.join(os.path.dirname(__file__), "..", "emails.json")
try:
    with open(SITES_FILE, 'r', encoding='utf-8') as f:
        EMAIL_SITES = json.load(f).get("sites", [])
except Exception as e:
    print(f"Failed to load email sites: {e}")
    EMAIL_SITES = []

async def check_haveibeenpwned(email: str) -> Dict[str, Any]:
    return {
        "source": "HaveIBeenPwned",
        "url": f"https://haveibeenpwned.com/account/{email}",
        "email": email,
        "breached": False,
        "note": "Requires API Key for real queries",
        "confidence": 0.5
    }

async def check_github_email(session: aiohttp.ClientSession, email: str) -> Dict[str, Any]:
    safe_email = urllib.parse.quote(email)
    url = f"https://api.github.com/search/commits?q=author-email:{safe_email}&sort=author-date&order=desc"
    headers = {
        'User-Agent': 'Raven-OSINT-Bot/1.0',
        'Accept': 'application/vnd.github.v3+json'
    }
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("total_count", 0) > 0:
                    author = data["items"][0].get("author")
                    if author and "login" in author:
                        username = author["login"]
                        return {
                            "source": "GitHub (Commits)",
                            "url": f"https://github.com/{username}",
                            "exists": True,
                            "note": f"Found linked username: {username}",
                            "confidence": 1.0
                        }
            return {
                "source": "GitHub (Commits)",
                "exists": False,
                "confidence": 0.0
            }
    except Exception as e:
        return {
            "source": "GitHub (Commits)",
            "exists": False,
            "error": str(e),
            "confidence": 0.0
        }

async def check_spotify(session: aiohttp.ClientSession, email: str) -> Dict[str, Any]:
    url = "https://spclient.wg.spotify.com/signup/public/v1/account"
    data = urllib.parse.urlencode({'email': email})
    headers = {
        'User-Agent': 'Spotify/8.4.62 Android/26 (SM-G925F)',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        async with session.post(url, data=data, headers=headers) as response:
            html = await response.text()
            if response.status == 200:
                if '"status": 1' in html:
                    return {"source": "Spotify", "url": url, "exists": False, "confidence": 0.9}
                return {"source": "Spotify", "url": url, "exists": True, "confidence": 0.9}
            elif response.status == 400:
                if "email_taken" in html or '"status": 20' in html:
                    return {"source": "Spotify", "url": url, "exists": True, "confidence": 0.9}
            return {"source": "Spotify", "url": url, "exists": False, "confidence": 0.0}
    except Exception as e:
        return {"source": "Spotify", "url": url, "exists": False, "error": str(e), "confidence": 0.0}

async def check_imgur(session: aiohttp.ClientSession, email: str) -> Dict[str, Any]:
    url = "https://imgur.com/signin/ajax_email_available"
    data = urllib.parse.urlencode({'email': email})
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        async with session.post(url, data=data, headers=headers) as response:
            if response.status == 200:
                data_json = await response.json()
                exists = not data_json.get("data", {}).get("available", True)
                return {"source": "Imgur", "url": url, "exists": exists, "confidence": 0.9}
            return {"source": "Imgur", "url": url, "exists": False, "confidence": 0.0}
    except Exception as e:
        return {"source": "Imgur", "url": url, "exists": False, "error": str(e), "confidence": 0.0}

async def check_gravatar(session: aiohttp.ClientSession, email: str) -> Dict[str, Any]:
    email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    url = f"https://en.gravatar.com/{email_hash}.json"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return {"source": "Gravatar", "url": url, "exists": True, "confidence": 0.9}
            return {"source": "Gravatar", "url": url, "exists": False, "confidence": 0.9}
    except Exception as e:
        return {"source": "Gravatar", "url": url, "exists": False, "error": str(e), "confidence": 0.0}

async def check_firefox(session: aiohttp.ClientSession, email: str) -> Dict[str, Any]:
    url = "https://api.accounts.firefox.com/v1/account/status"
    data = json.dumps({"email": email})
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json'
    }
    try:
        async with session.post(url, data=data, headers=headers) as response:
            if response.status == 200:
                data_json = await response.json()
                exists = data_json.get("exists", False)
                return {"source": "Firefox Sync", "url": url, "exists": exists, "confidence": 0.9}
            return {"source": "Firefox Sync", "url": url, "exists": False, "confidence": 0.0}
    except Exception as e:
        return {"source": "Firefox Sync", "url": url, "exists": False, "error": str(e), "confidence": 0.0}

async def check_adobe(session: aiohttp.ClientSession, email: str) -> Dict[str, Any]:
    url = "https://auth.services.adobe.com/signin/v2/users/accounts"
    data = json.dumps({"username": email})
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json',
        'x-ims-clientid': 'SunbreakWebUI1'
    }
    try:
        async with session.post(url, data=data, headers=headers) as response:
            if response.status == 200:
                data_json = await response.json()
                exists = len(data_json) > 0
                return {"source": "Adobe", "url": url, "exists": exists, "confidence": 0.9}
            return {"source": "Adobe", "url": url, "exists": False, "confidence": 0.9}
    except Exception as e:
        return {"source": "Adobe", "url": url, "exists": False, "error": str(e), "confidence": 0.0}

async def check_email_site_async(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, site: dict, email: str) -> Dict[str, Any]:
    site_name = site.get("name")
    uri_check = site.get("uri_check")
    e_code = site.get("e_code")
    e_string = site.get("e_string")
    m_string = site.get("m_string")
    method = site.get("method", "GET").upper()
    data_payload = site.get("data")
    headers = site.get("headers") or {}
    input_op = site.get("input_operation")

    # Apply input operations
    account_val = email
    if input_op == "hash-sha256":
        account_val = hashlib.sha256(email.lower().encode('utf-8')).hexdigest()
        
    url = uri_check.replace("{account}", urllib.parse.quote(account_val))
    display_url = url
    
    # Prepare Data
    req_data = None
    if data_payload:
        req_data = data_payload.replace("{account}", account_val)
        
    # Prepare Headers
    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for k, v in headers.items():
        req_headers[k] = v.replace("{account}", account_val)

    async with semaphore:
        try:
            kwargs = {"headers": req_headers, "allow_redirects": True}
            if req_data:
                kwargs["data"] = req_data
                
            async with session.request(method, url, **kwargs) as response:
                status = response.status
                html = ""
                try:
                    html = await response.text()
                except:
                    pass
                
                exists = False
                if status == e_code:
                    exists = True
                    
                if e_string and e_string not in html:
                    exists = False
                    
                if m_string and m_string in html:
                    exists = False
                    
                if not exists:
                    return {
                        "source": site_name,
                        "url": display_url,
                        "exists": False,
                        "status_code": status,
                        "confidence": 0.0,
                        "error": f"HTTP {status}"
                    }
                    
                return {
                    "source": site_name,
                    "url": display_url,
                    "exists": exists,
                    "status_code": status,
                    "confidence": 0.9 if exists else 0.0
                }
        except Exception as e:
            return {"source": site_name, "url": display_url, "exists": False, "error": str(e), "confidence": 0.0}

async def run_email_collection(email: str) -> list:
    semaphore = asyncio.Semaphore(100)
    connector = aiohttp.TCPConnector(limit=100, ssl=False)
    timeout = aiohttp.ClientTimeout(total=5.0)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [
            check_haveibeenpwned(email),
            check_github_email(session, email),
            check_spotify(session, email),
            check_imgur(session, email),
            check_gravatar(session, email),
            check_firefox(session, email),
            check_adobe(session, email)
        ]
        
        for site in EMAIL_SITES:
            tasks.append(check_email_site_async(session, semaphore, site, email))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for r in results:
            if isinstance(r, dict):
                valid_results.append(r)
                
        return valid_results
