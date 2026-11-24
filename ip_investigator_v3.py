#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║         IP INVESTIGATOR PRO v3.0 — FINAL BEAST MODE        ║
║      SIM | WiFi | Carrier | Location | OS | Ports          ║
║                Authorized Pentesting Use Only                ║
╚══════════════════════════════════════════════════════════════╝

USAGE:  python3 ip_investigator_v3.py                     (menu)
        python3 ip_investigator_v3.py 8.8.8.8             (report, then menu)
        python3 ip_investigator_v3.py --single 1.1.1.1    (report only, no menu)
        python3 ip_investigator_v3.py --json 8.8.8.8      (JSON on stdout, non-interactive)
"""

import argparse, json, sys, socket, requests, ipaddress, os, re, time
from datetime import datetime


# ===================== CONFIG =====================
from dotenv import load_dotenv

load_dotenv()

IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "").strip()
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY", "").strip()
# ip-api.com : the FREE plan is HTTP only (HTTPS is a paid "pro" feature),
# limited to 45 requests/minute and non-commercial use. Traffic to ip-api is
# therefore NOT encrypted unless you set IPAPI_KEY (pro plan -> HTTPS).
IPAPI_KEY = os.getenv("IPAPI_KEY", "").strip()
# ==================================================

JSON_MODE = False          # --json : logs go to stderr, JSON to stdout
_IPAPI_HTTP_WARNED = False

class Colors:
    HEADER = '\033[95m'; BLUE = '\033[94m'; CYAN = '\033[96m'
    GREEN = '\033[92m'; YELLOW = '\033[93m'; RED = '\033[91m'
    MAGENTA = '\033[35m'; BOLD = '\033[1m'; END = '\033[0m'; WHITE = '\033[97m'

# ════════════════ ASCII BANNER — NMAP STYLE EYE ════════════════
# raw string (rf): the ASCII art contains backslashes
BANNER = rf"""
{Colors.YELLOW}{Colors.BOLD}
        ___
     .-"   "-.       
    /  .-. .-.\      
   |   \o| |o |      ██╗██████╗
   |     ^    |      ██║██╔══██╗
   |   '---'  |      ██║██████╔╝
    \         /      ██║██╔═══╝
  ___'._____.'___    ██║██║
 /   /  | |  \   \   ╚═╝╚═╝ v3.0 Coded by argcyberskillhub⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
/   /   | |   \   \
   /    | |    \       
                   
{Colors.END}
{Colors.GREEN}{Colors.BOLD}      

┌───────────────────────────────────────────┐
│  IP INVESTIGATOR PRO v3.0 — DESI EDITION  │
│    SIM · WiFi · Carrier · Location · OS   │
│      🛡️ Authorized Pentesting Only       │
└───────────────────────────────────────────┘
{Colors.END}
{Colors.CYAN}
 ══════════════════════════════════════════
     🔴 RECON 🟡 ANALYZE 🟢 REPORT
 ══════════════════════════════════════════
{Colors.END}"""

# ─────────── KNOWN ASN DATABASE ───────────
# (ASN holders checked against RIPEstat, 22-Nov-2026)
# kind = "mobile"     : mobile operator (may also sell fixed/fiber lines)
#        "mixed"      : fixed + mobile operator (ip-api "mobile" flag decides)
#        "broadband"  : fixed ISP
#        "datacenter" : cloud / hosting — never classified as mobile
KNOWN_ASNS = {
    # 🇮🇳 India
    "AS55836": {"name": "Reliance Jio", "type": "4G/5G Mobile", "kind": "mobile", "mcc": "405", "mnc": "840"},
    "AS9829":  {"name": "BSNL", "type": "Mobile/Broadband", "kind": "mixed", "mcc": "404", "mnc": "70"},
    "AS55410": {"name": "Vodafone Idea (VI)", "type": "4G Mobile", "kind": "mobile", "mcc": "404", "mnc": "94"},
    "AS45528": {"name": "Tikona Infinet", "type": "Wireless Broadband", "kind": "broadband"},
    "AS24309": {"name": "ACT Fibernet", "type": "Fiber Broadband", "kind": "broadband"},
    "AS17813": {"name": "MTNL", "type": "Mobile/Broadband", "kind": "mixed", "mcc": "404", "mnc": "68"},
    "AS4755":  {"name": "Tata Communications", "type": "Enterprise/ISP", "kind": "broadband"},
    "AS24560": {"name": "Bharti Airtel", "type": "Mobile/Broadband", "kind": "mixed", "mcc": "404", "mnc": "90"},
    "AS45609": {"name": "Bharti Airtel", "type": "4G/5G Mobile", "kind": "mobile", "mcc": "404", "mnc": "90"},
    "AS17488": {"name": "Hathway", "type": "Broadband/Cable", "kind": "broadband"},
    "AS133982":{"name": "Excitel", "type": "Fiber Broadband", "kind": "broadband"},
    # 🇧🇯 Bénin
    "AS37424": {"name": "MTN Bénin (Spacetel)", "type": "Mobile", "kind": "mobile", "mcc": "616", "mnc": "03"},
    "AS37136": {"name": "Moov Africa Bénin (ex-Etisalat)", "type": "Mobile", "kind": "mobile", "mcc": "616", "mnc": "02"},
    "AS28683": {"name": "Celtiis / SBIN", "type": "Mobile/Fixed", "kind": "mixed", "mcc": "616"},
    "AS328228":{"name": "Celtiis / SBIN", "type": "Mobile/Fixed", "kind": "mixed", "mcc": "616"},
    "AS37090": {"name": "Isocel", "type": "Fixed/Wireless ISP", "kind": "broadband"},
    # 🌍 Africa
    "AS29465": {"name": "MTN Nigeria", "type": "Mobile", "kind": "mobile", "mcc": "621", "mnc": "30"},
    "AS29571": {"name": "Orange Côte d'Ivoire", "type": "Mobile/Fixed", "kind": "mixed", "mcc": "612", "mnc": "03"},
    "AS30985": {"name": "Orange Mali", "type": "Mobile/Fixed", "kind": "mixed", "mcc": "610", "mnc": "02"},
    "AS8346":  {"name": "Sonatel (Orange Sénégal)", "type": "Mobile/Fixed", "kind": "mixed", "mcc": "608", "mnc": "01"},
    "AS33771": {"name": "Safaricom", "type": "Mobile", "kind": "mobile", "mcc": "639", "mnc": "02"},
    "AS36926": {"name": "Airtel Kenya", "type": "Mobile", "kind": "mobile", "mcc": "639", "mnc": "03"},
    # 🇫🇷 / 🇪🇺 / 🇺🇸
    "AS3215":  {"name": "Orange France", "type": "Fixed/Mobile", "kind": "mixed", "mcc": "208", "mnc": "01"},
    "AS51207": {"name": "Free Mobile", "type": "4G/5G Mobile", "kind": "mobile", "mcc": "208", "mnc": "15"},
    "AS5410":  {"name": "Bouygues Telecom", "type": "Fixed/Mobile", "kind": "mixed", "mcc": "208", "mnc": "20"},
    "AS15557": {"name": "SFR", "type": "Fixed/Mobile", "kind": "mixed", "mcc": "208", "mnc": "10"},
    "AS21928": {"name": "T-Mobile USA", "type": "4G/5G Mobile", "kind": "mobile", "mcc": "310", "mnc": "260"},
    "AS22394": {"name": "Verizon Wireless", "type": "4G/5G Mobile", "kind": "mobile", "mcc": "311", "mnc": "480"},
    "AS20057": {"name": "AT&T Mobility", "type": "4G/5G Mobile", "kind": "mobile", "mcc": "310", "mnc": "410"},
    # ☁️ Cloud / hosting (never mobile)
    "AS15169": {"name": "Google LLC", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS396982":{"name": "Google Cloud", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS16509": {"name": "Amazon AWS", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS14618": {"name": "Amazon AWS", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS8075":  {"name": "Microsoft Azure", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS36351": {"name": "IBM Cloud", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS24940": {"name": "Hetzner", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS16276": {"name": "OVHcloud", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS13335": {"name": "Cloudflare", "type": "Cloud/CDN", "kind": "datacenter"},
    "AS14061": {"name": "DigitalOcean", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS63949": {"name": "Akamai / Linode", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS20940": {"name": "Akamai", "type": "CDN", "kind": "datacenter"},
    "AS20473": {"name": "Vultr", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS31898": {"name": "Oracle Cloud", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS51167": {"name": "Contabo", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS12876": {"name": "Scaleway", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS45102": {"name": "Alibaba Cloud", "type": "Cloud/Datacenter", "kind": "datacenter"},
    "AS132203":{"name": "Tencent Cloud", "type": "Cloud/Datacenter", "kind": "datacenter"},
}

# Keywords are matched as whole words only (no "vi " / "cell" / "idea" substrings).
CARRIER_KEYWORDS = {
    "mobile": ["mobile", "mobility", "wireless", "cellular", "cellco", "lte", "gsm", "umts",
               "jio", "mtn", "moov", "celtiis", "safaricom", "vodacom", "t-mobile"],
    "broadband": ["broadband", "dsl", "adsl", "vdsl", "fiber", "fibre", "ftth", "cable",
                  "hathway", "excitel", "spectra", "tikona", "railwire", "comcast", "cox",
                  "spectrum", "free sas", "isocel"],
    "datacenter": ["amazon", "aws", "azure", "microsoft", "google llc", "google cloud", "gcp", "digitalocean",
                   "linode", "akamai", "vultr", "ovh", "ovhcloud", "hetzner", "softlayer", "ibm",
                   "oracle", "alibaba", "tencent", "cloudflare", "contabo", "scaleway",
                   "hosting", "datacenter", "data center", "colocation", "vps"],
}

# ─────────── HELPERS ───────────

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def mask_secrets(text):
    """Never print API keys: replace known secrets and any key=/token= value."""
    s = str(text)
    for secret in (IPINFO_TOKEN, SHODAN_API_KEY, IPAPI_KEY):
        if secret:
            s = s.replace(secret, "***")
    return re.sub(r"(?i)\b(key|token)=[^&\s'\")]+", r"\1=***", s)

def _log_out():
    # In --json mode, stdout is reserved for the JSON document.
    return sys.stderr if JSON_MODE else sys.stdout

def p_header(t): print(f"\n{Colors.BOLD}{Colors.CYAN}╔══ {t} {'═'*(60-len(t))}╗{Colors.END}")
def p_sub(t): print(f"{Colors.BOLD}{Colors.GREEN}├─ {t}{Colors.END}")
def p_kv(k, v, c=Colors.WHITE):
    if v and str(v) not in ["", "N/A", "None"]:
        print(f"│  {Colors.YELLOW}{k:<25}{Colors.END} : {c}{v}{Colors.END}")
def p_sep(): print(f"{Colors.CYAN}│{'─'*65}│{Colors.END}")
def p_err(m): print(f"{Colors.RED}[!] {mask_secrets(m)}{Colors.END}", file=_log_out())
def p_ok(m):
    if not JSON_MODE: print(f"{Colors.GREEN}[✓] {m}{Colors.END}")
def p_info(m):
    if not JSON_MODE: print(f"{Colors.BLUE}[*] {m}{Colors.END}")
def p_warn(m): print(f"{Colors.YELLOW}[!] {mask_secrets(m)}{Colors.END}", file=_log_out())

def validate_ip(ip):
    try:
        ipaddress.ip_address(ip); return True
    except ValueError: return False

def ip_scope_problem(ip):
    """Return why an IP must NOT be sent to online services (None = public IP)."""
    a = ipaddress.ip_address(ip)
    if a.is_unspecified: return "unspecified (0.0.0.0 / ::)"
    if a.is_loopback:    return "loopback (this machine)"
    if a.is_link_local:  return "link-local (169.254.x.x / fe80::)"
    if a.is_multicast:   return "multicast"
    if a.is_reserved:    return "reserved (IETF, 240.0.0.0/4…)"
    if a.is_private:     return "private / non-routable (LAN 10.x, 172.16-31.x, 192.168.x, fc00::/7, documentation…)"
    if not a.is_global:  return "non-public (shared / CGNAT / documentation range)"
    return None

def resolve_target(target):
    """IP stays as is; a domain is resolved to its IP. Returns None if impossible."""
    if validate_ip(target): return target
    try:
        resolved = socket.gethostbyname(target)
        p_info(f"Domain '{target}' resolved to {resolved}")
        return resolved
    except (socket.gaierror, UnicodeError, OSError):
        p_err(f"'{target}' is not a valid IP and cannot be resolved as a domain")
        return None

def reverse_dns(ip):
    try: return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror, OSError): return "N/A"

def spinner(seconds=0.5):
    if JSON_MODE: return
    for s in ['|', '/', '-', '\\']:
        print(f'\r{Colors.CYAN}{s}{Colors.END}', end='', flush=True)
        time.sleep(0.1)
    print('\r ', end='', flush=True)

# ─────────── API QUERIES ───────────

def _net_error(source, e):
    """Readable message for network errors (secrets masked by p_err)."""
    if isinstance(e, requests.exceptions.Timeout):
        p_err(f"{source}: timeout — service too slow or unreachable")
    elif isinstance(e, requests.exceptions.ConnectionError):
        p_err(f"{source}: network error (no connection / DNS / blocked)")
    else:
        p_err(f"{source} failed: {e}")

def query_ipapi(ip):
    global _IPAPI_HTTP_WARNED
    p_info(f"📡 Querying ip-api.com for {ip}...")
    spinner()
    fields = "status,message,continent,continentCode,country,countryCode,region,regionName,city,district,zip,lat,lon,timezone,offset,currency,isp,org,as,asname,mobile,proxy,hosting,query"
    if IPAPI_KEY:
        url, params = f"https://pro.ip-api.com/json/{ip}", {"fields": fields, "key": IPAPI_KEY}
    else:
        # Free plan = HTTP only (HTTPS is paid). Kept on purpose, but the user is warned.
        url, params = f"http://ip-api.com/json/{ip}", {"fields": fields}
        if not _IPAPI_HTTP_WARNED:
            p_warn("ip-api free plan uses plain HTTP (unencrypted). Set IPAPI_KEY (pro) in .env for HTTPS.")
            _IPAPI_HTTP_WARNED = True
    try:
        r = requests.get(url, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        _net_error("ip-api", e); return None
    left, ttl = r.headers.get("X-Rl"), r.headers.get("X-Ttl")
    if r.status_code == 429:
        p_err(f"ip-api: rate limit reached (45 requests/min on the free plan). Retry in {ttl or '60'}s.")
        return None
    if r.status_code != 200:
        p_warn(f"ip-api: HTTP {r.status_code}"); return None
    try:
        d = r.json()
    except ValueError:
        p_err("ip-api: invalid (non-JSON) response"); return None
    if d.get("status") == "fail":
        p_err(f"ip-api: {d.get('message', 'unknown error')}"); return None
    if left is not None and left.isdigit() and int(left) <= 5:
        p_warn(f"ip-api: only {left} requests left this minute (reset in {ttl}s)")
    p_ok("ip-api.com response received")
    return d

def query_ipinfo(ip):
    p_info(f"📡 Querying ipinfo.io for {ip}...")
    spinner()
    headers = {"Accept": "application/json"}
    if IPINFO_TOKEN:
        headers["Authorization"] = f"Bearer {IPINFO_TOKEN}"   # token in header, not in URL
    try:
        r = requests.get(f"https://ipinfo.io/{ip}/json", headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        _net_error("ipinfo", e); return None
    if r.status_code == 200:
        try:
            d = r.json()
        except ValueError:
            p_err("ipinfo: invalid (non-JSON) response"); return None
        p_ok("ipinfo.io response received")
        return d
    if r.status_code in (401, 403):
        p_err("ipinfo: token rejected (check IPINFO_TOKEN)")
    elif r.status_code == 429:
        p_err("ipinfo: quota exceeded (HTTP 429)")
    else:
        p_warn(f"ipinfo: HTTP {r.status_code}")
    return None

def query_shodan(ip):
    if not SHODAN_API_KEY:
        p_warn("Shodan API key not configured — skipping OS/Port data")
        return None
    p_info(f"📡 Querying Shodan for {ip}...")
    spinner()
    try:
        # Shodan only accepts the key as ?key= ; every error message is masked.
        r = requests.get(f"https://api.shodan.io/shodan/host/{ip}",
                         params={"key": SHODAN_API_KEY}, timeout=15)
    except requests.exceptions.RequestException as e:
        _net_error("Shodan", e); return None
    if r.status_code == 200:
        try:
            d = r.json()
        except ValueError:
            p_err("Shodan: invalid (non-JSON) response"); return None
        p_ok("Shodan response received")
        return d
    if r.status_code == 401:
        p_err("Shodan: Invalid API key!")
    elif r.status_code == 404:
        p_info("Shodan: No data found for this IP (not indexed)")
    elif r.status_code == 429:
        p_err("Shodan: rate limit / credits exhausted (HTTP 429)")
    else:
        p_warn(f"Shodan: HTTP {r.status_code}")
    return None

# ─────────── ANALYSIS ───────────

def _kw_match(text, words):
    """Whole-word keyword match; returns the matched keyword or None."""
    for w in words:
        if re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", text):
            return w
    return None

def identify_network_type(ip_api, ipinfo):
    result = {
        "type": "❓ Unknown",
        "confidence": "Low",
        "carrier": None,
        "mcc": None,
        "mnc": None,
        "is_mobile": False,
        "is_proxy": False,
        "is_hosting": False,
        "is_tor": False,
        "details": []
    }

    asn_number = None
    asn_name = isp_name = org_name = ""
    isp_display = None
    api_mobile = False

    if ip_api:
        asn_full = ip_api.get("as", "") or ""
        if asn_full: asn_number = asn_full.split()[0]
        asn_name = (ip_api.get("asname") or "").lower()
        isp_name = (ip_api.get("isp") or "").lower()
        org_name = (ip_api.get("org") or "").lower()
        isp_display = ip_api.get("isp") or ip_api.get("org")
        if ip_api.get("proxy"): result["is_proxy"] = True
        if ip_api.get("hosting"): result["is_hosting"] = True
        api_mobile = bool(ip_api.get("mobile"))

    ipinfo_carrier = None
    if ipinfo:
        priv = ipinfo.get("privacy", {}) if isinstance(ipinfo.get("privacy"), dict) else {}
        if priv.get("vpn"): result["is_proxy"] = True
        if priv.get("proxy"): result["is_proxy"] = True
        if priv.get("tor"): result["is_tor"] = True
        if priv.get("hosting"): result["is_hosting"] = True

        mobile_data = ipinfo.get("mobile") or ipinfo.get("carrier")
        if mobile_data and isinstance(mobile_data, dict):
            ipinfo_carrier = mobile_data
            api_mobile = True

        asn_info = ipinfo.get("asn", {})
        if isinstance(asn_info, dict) and asn_info.get("asn"):
            asn_number = asn_number or asn_info["asn"]
            if not asn_name: asn_name = (asn_info.get("name") or "").lower()
        if not asn_number and ipinfo.get("org"):          # free ipinfo: "AS13335 Cloudflare, Inc."
            first = str(ipinfo["org"]).split()[0]
            if first.upper().startswith("AS"): asn_number = first
        if not isp_display and ipinfo.get("org"):
            isp_display = " ".join(str(ipinfo["org"]).split()[1:]) or ipinfo["org"]
        if not org_name: org_name = (ipinfo.get("org") or "").lower()

    if asn_number: asn_number = asn_number.upper()
    known = KNOWN_ASNS.get(asn_number) if asn_number else None
    combined = f"{asn_name} {isp_name} {org_name}"

    # 1) Cloud / hosting first: a datacenter IP is never a SIM.
    dc_kw = _kw_match(combined, CARRIER_KEYWORDS["datacenter"])
    if (known and known["kind"] == "datacenter") or dc_kw or result["is_hosting"]:
        result["is_hosting"] = True
        name = known["name"] if known else (isp_display or "")
        result["type"] = f"🏢 Datacenter / Cloud{(' — ' + name) if name else ''}"
        result["confidence"] = "High" if (known or (ip_api and ip_api.get("hosting"))) else "Medium"
        if known: result["details"].append(f"ASN matched: {asn_number} = {known['name']} ({known['type']})")
        elif dc_kw: result["details"].append(f"Keyword '{dc_kw}' in ISP/ASN name")
        else: result["details"].append("Hosting flag set by ip-api/ipinfo")
        return result

    def _fill_mcc():
        if known:
            result["mcc"] = known.get("mcc"); result["mnc"] = known.get("mnc")
        if ipinfo_carrier:
            result["mcc"] = ipinfo_carrier.get("mcc") or result["mcc"]
            result["mnc"] = ipinfo_carrier.get("mnc") or result["mnc"]

    # 2) Mobile flag from ip-api / ipinfo carrier data = most reliable signal.
    if api_mobile:
        result["is_mobile"] = True
        result["carrier"] = ((ipinfo_carrier or {}).get("name")
                             or (known["name"] if known else None) or isp_display or "Unknown")
        result["type"] = f"📱 {result['carrier']} (Mobile Network)"
        result["confidence"] = "High"
        result["details"].append("Mobile flag set by ip-api/ipinfo")
        if known: result["details"].append(f"ASN matched: {asn_number} = {known['name']}")
        _fill_mcc()
        return result

    # 3) Known ASN without mobile flag.
    if known and known["kind"] == "mobile":
        result["is_mobile"] = True
        result["carrier"] = known["name"]
        result["type"] = f"📱 {known['name']} ({known['type']}) — fixed line possible"
        result["confidence"] = "Medium"
        result["details"].append(f"ASN matched: {asn_number} = {known['name']} (mobile operator)")
        result["details"].append("ip-api mobile flag = false → could also be a fixed/fiber line")
        _fill_mcc()
        return result
    if known and known["kind"] in ("mixed", "broadband"):
        result["type"] = f"🏠 Fixed Broadband / WiFi — {known['name']}"
        result["confidence"] = "Medium"
        extra = " (operator also sells mobile; ip-api says not mobile)" if known["kind"] == "mixed" else ""
        result["details"].append(f"ASN matched: {asn_number} = {known['name']}{extra}")
        return result

    # 4) Whole-word keywords (weak signal).
    m_kw = _kw_match(combined, CARRIER_KEYWORDS["mobile"])
    if m_kw:
        result["is_mobile"] = True
        result["carrier"] = isp_display or "Unknown"
        result["type"] = f"📱 {result['carrier']} (Mobile Network?)"
        result["confidence"] = "Low"
        result["details"].append(f"Keyword '{m_kw}' in ISP/ASN name (no mobile flag)")
        return result
    b_kw = _kw_match(combined, CARRIER_KEYWORDS["broadband"])
    if b_kw:
        result["type"] = "🏠 Residential Broadband / WiFi"
        result["confidence"] = "Medium"
        result["details"].append(f"Keyword '{b_kw}' in ISP/ASN name")
        return result

    if result["is_proxy"]: result["type"] = "🔒 VPN / Proxy Server"; result["confidence"] = "High"
    elif result["is_tor"]: result["type"] = "🧅 TOR Exit Node"; result["confidence"] = "High"
    elif isp_display:
        result["type"] = f"❓ Unknown (ISP: {isp_display})"
        result["details"].append("No mobile/hosting flag — probably a fixed line")

    return result

def compute_risk(net):
    risk = 0; risks = []
    if net['is_tor']: risk += 50; risks.append("🚨 TOR Exit Node — Extreme anonymity")
    if net['is_proxy']: risk += 30; risks.append("🔥 VPN/Proxy — High anonymity")
    if net['is_hosting']: risk += 15; risks.append("⚠️ Datacenter IP — VPS/Cloud possible")
    level = "CRITICAL" if risk >= 50 else "HIGH" if risk >= 30 else "MEDIUM" if risk >= 15 else "LOW"
    return min(risk, 100), risks, level

# ─────────── REPORT ───────────

def show_report(ip, ip_api, ipinfo, shodan):
    net = identify_network_type(ip_api, ipinfo)
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'═'*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}   📊 FINAL REPORT: {ip}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}   🕐 {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'═'*70}{Colors.END}")
    
    # ── 1. BASIC ──
    p_header("📋 BASIC INFO")
    ip_ver = f"IPv{ipaddress.ip_address(ip).version}"
    p_kv("IP Address", ip, Colors.CYAN)
    p_kv("Version", ip_ver)
    p_kv("Reverse DNS", reverse_dns(ip), Colors.GREEN)
    p_sep()
    
    # ── 2. LOCATION ──
    p_header("📍 GEOLOCATION")
    if ip_api:
        lat, lon = ip_api.get("lat"), ip_api.get("lon")
        p_kv("Continent", f"{ip_api.get('continent','N/A')} ({ip_api.get('continentCode','N/A')})")
        p_kv("Country", f"{ip_api.get('country','N/A')} ({ip_api.get('countryCode','N/A')})")
        p_kv("Region/State", ip_api.get("regionName","N/A"))
        p_kv("City", ip_api.get("city","N/A"))
        p_kv("District", ip_api.get("district","N/A"))
        p_kv("ZIP Code", ip_api.get("zip","N/A"))
        if lat and lon:
            p_kv("Latitude", lat, Colors.CYAN)
            p_kv("Longitude", lon, Colors.CYAN)
            p_kv("📍 Google Maps", f"https://www.google.com/maps?q={lat},{lon}", Colors.BLUE)
        p_kv("Timezone", ip_api.get("timezone","N/A"))
        p_kv("Currency", ip_api.get("currency","N/A"))
    p_sep()
    
    # ── 3. ISP / CARRIER ──
    p_header("🏢 ISP & CARRIER INFO")
    if ip_api:
        p_kv("ISP", ip_api.get("isp","N/A"), Colors.GREEN)
        p_kv("Organization", ip_api.get("org","N/A"))
        p_kv("AS Number", ip_api.get("as","N/A"))
        p_kv("AS Name", ip_api.get("asname","N/A"))
    if ipinfo:
        comp = ipinfo.get("company", {})
        if isinstance(comp, dict):
            p_kv("Company", comp.get("name","N/A"))
            p_kv("Domain", comp.get("domain","N/A"))
    p_sep()
    
    # ── 4. CONNECTION TYPE ──
    p_header("📶 SIM vs WiFi vs DATACENTER")
    print(f"│  {Colors.BOLD}{Colors.YELLOW}Detected Type        {Colors.END} : {Colors.BOLD}{Colors.MAGENTA}{net['type']}{Colors.END}")
    p_kv("Confidence", net['confidence'])
    if net['carrier']:
        print(f"│  {Colors.BOLD}{Colors.YELLOW}📱 Carrier Name      {Colors.END} : {Colors.GREEN}{Colors.BOLD}{net['carrier']}{Colors.END}")
    if net['mcc']:
        mcc_map = {"404":"🇮🇳 India","405":"🇮🇳 India","310":"🇺🇸 USA","234":"🇬🇧 UK","440":"🇯🇵 Japan","250":"🇷🇺 Russia","208":"🇫🇷 France","262":"🇩🇪 Germany","460":"🇨🇳 China","520":"🇹🇭 Thailand",
                   "311":"🇺🇸 USA","616":"🇧🇯 Benin","621":"🇳🇬 Nigeria","612":"🇨🇮 Côte d'Ivoire","610":"🇲🇱 Mali","608":"🇸🇳 Senegal","639":"🇰🇪 Kenya"}
        ctry = mcc_map.get(net['mcc'], f"MCC {net['mcc']}")
        p_kv("MCC", f"{net['mcc']} ({ctry})")
        p_kv("MNC", net['mnc'])
    
    p_sep()
    p_header("🚦 Traffic Classification:")
    # Mobile is information, not a "good" result: neutral colour, no green tick.
    m = net['is_mobile']
    conf = f"  (confidence: {net['confidence']})" if m else ""
    print(f"│  {'📱 Mobile (SIM)':<22}: {Colors.CYAN}{'ℹ️  YES' if m else '•  NO'}{conf}{Colors.END}")
    for label, val in [
        ("🔒 VPN/Proxy", net['is_proxy']),
        ("🏢 Datacenter", net['is_hosting']),
        ("🧅 TOR Node", net['is_tor'])
    ]:
        c = Colors.RED if val else Colors.GREEN
        icon = "⚠️" if val else "✅"
        print(f"│  {label:<22}: {c}{icon} {'YES' if val else 'NO'}{Colors.END}")
    
    if net['details']:
        print(f"│  {Colors.YELLOW}Detection Details:{Colors.END}")
        for d in net['details']: print(f"│    • {d}")
    p_sep()
    
    # ── 5. OS & PORTS ──
    p_header("🖥️ OS FINGERPRINTING & PORTS")
    if shodan:
        os_name = shodan.get("os", "N/A")
        p_kv("Operating System", os_name, Colors.MAGENTA)
        
        ports = shodan.get("data", [])
        if ports:
            p_sub("🔓 Open Ports:")
            for pi in ports[:8]:
                port = pi.get("port"); proto = pi.get("transport")
                prod = pi.get("product",""); ver = pi.get("version","")
                svc = pi.get("_shodan",{}).get("module","?")
                l = f"│    {Colors.CYAN}{port}/{proto}{Colors.END} {svc}"
                if prod: l += f" - {Colors.GREEN}{prod} {ver}{Colors.END}"
                print(l)
            if len(ports) > 8: print(f"│    ... +{len(ports)-8} more")
        
        hns = shodan.get("hostnames", [])
        if hns:
            p_sub("Hostnames:")
            for hn in hns[:5]: print(f"│    • {hn}")
    elif SHODAN_API_KEY:
        print(f"│  {Colors.YELLOW}⏭️  No Shodan data for this IP (not indexed, quota or error){Colors.END}")
    else:
        print(f"│  {Colors.YELLOW}⏭️  Skipped — no Shodan API key configured{Colors.END}")
        print(f"│  {Colors.YELLOW}   To enable OS/Port data (from Shodan's index, no active scan):{Colors.END}")
        print(f"│  {Colors.YELLOW}   1. Sign up at https://account.shodan.io{Colors.END}")
        print(f"│  {Colors.YELLOW}   2. Set SHODAN_API_KEY in the .env file{Colors.END}")
    p_sep()
    
    # ── 6. THREAT ──
    p_header("🛡️ ANONYMITY & THREAT SCORE")
    risk, risks, _level = compute_risk(net)
    
    print(f"│  {Colors.BOLD}{Colors.YELLOW}Risk Score          {Colors.END}: ", end="")
    if risk >= 50: print(f"{Colors.RED}{Colors.BOLD}{risk}/100 — CRITICAL{Colors.END}")
    elif risk >= 30: print(f"{Colors.RED}{risk}/100 — HIGH{Colors.END}")
    elif risk >= 15: print(f"{Colors.YELLOW}{risk}/100 — MEDIUM{Colors.END}")
    else: print(f"{Colors.GREEN}{risk}/100 — LOW (Clean){Colors.END}")
    
    for r in risks: print(f"│    • {r}")
    if not risks: print(f"│  {Colors.GREEN}✅ No threats detected{Colors.END}")
    
    if ipinfo:
        abuse = ipinfo.get("abuse", {})
        if isinstance(abuse, dict) and abuse.get("email"):
            p_sep()
            p_sub("📧 Abuse Contact:")
            p_kv("Email", abuse.get("email"))
            p_kv("Country", abuse.get("country","N/A"))
    
    # ── SUMMARY ──
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'═'*70}{Colors.END}")
    if not ip_api and not ipinfo:
        print(f"{Colors.BOLD}{Colors.RED}   ⚠️  No data received from ip-api / ipinfo — check network, quota or keys{Colors.END}")
        print(f"{Colors.HEADER}{'═'*70}{Colors.END}")
        return
    print(f"{Colors.BOLD}{Colors.GREEN}   ✅ Investigation Complete{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}   📡 Network: {net['type']}{Colors.END}")
    if net['is_mobile']:
        sure = "" if net['confidence'] == "High" else f" (probably — confidence {net['confidence']})"
        print(f"{Colors.BOLD}{Colors.CYAN}   📱 This is a MOBILE (SIM Card) IP{sure}{Colors.END}")
        if net['carrier']: print(f"{Colors.BOLD}{Colors.MAGENTA}   🏢 Carrier: {net['carrier']}{Colors.END}")
    else:
        kind = "DATACENTER / CLOUD" if net['is_hosting'] else "BROADBAND / WiFi (fixed line)"
        print(f"{Colors.BOLD}{Colors.BLUE}   🏠 This is a {kind} IP{Colors.END}")
    print(f"{Colors.HEADER}{'═'*70}{Colors.END}")

# ═══════════════ CORE LOOP ═══════════════

def build_json(ip, ip_api, ipinfo, shodan):
    """Machine-readable result for --json."""
    net = identify_network_type(ip_api, ipinfo)
    risk, risks, level = compute_risk(net)
    loc = None
    if ip_api:
        loc = {k: ip_api.get(k) for k in ("continent", "country", "countryCode", "regionName",
                                          "city", "zip", "lat", "lon", "timezone")}
    network = {
        "isp": (ip_api or {}).get("isp"),
        "org": (ip_api or {}).get("org") or (ipinfo or {}).get("org"),
        "as": (ip_api or {}).get("as"),
        "asname": (ip_api or {}).get("asname"),
    }
    sh = None
    if shodan:
        sh = {
            "os": shodan.get("os"),
            "ports": sorted({p.get("port") for p in shodan.get("data", []) if p.get("port")}),
            "hostnames": shodan.get("hostnames", []),
        }
    rdns = reverse_dns(ip)
    result = {
        "ip": ip,
        "version": ipaddress.ip_address(ip).version,
        "reverse_dns": None if rdns == "N/A" else rdns,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "location": loc,
        "network": network,
        "classification": net,
        "risk": {"score": risk, "level": level, "reasons": risks},
        "shodan": sh,
        "sources": {"ip-api": ip_api is not None, "ipinfo": ipinfo is not None, "shodan": shodan is not None},
    }
    if ip_api is None and ipinfo is None:
        result["error"] = "no data received from ip-api / ipinfo (network, quota or keys)"
    return result

def process_ip(ip):
    """Single IP processing with complete flow.
    Returns True (report shown) / dict (--json) / None (error)."""
    if not ip or ip == "":
        p_info("Fetching your public IP...")
        try:
            ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
            p_ok(f"Your public IP: {ip}")
        except requests.exceptions.RequestException:
            p_err("Can't fetch your IP")
            return {"error": "cannot fetch own public IP"} if JSON_MODE else None

    if not validate_ip(ip):
        p_err(f"Invalid IP format: {ip}")
        return {"ip": ip, "error": "invalid IP"} if JSON_MODE else None

    problem = ip_scope_problem(ip)
    if problem:
        p_warn(f"{ip} is a {problem} address — nothing was sent to online services.")
        p_warn("Public IP intelligence only works on public (global) addresses.")
        return {"ip": ip, "error": f"non-public address: {problem}"} if JSON_MODE else None

    if not JSON_MODE:
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═'*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}   🔍 TARGET LOCKED: {ip}{Colors.END}")
        print(f"{Colors.CYAN}{'═'*70}{Colors.END}")

    d1 = query_ipapi(ip)
    d2 = query_ipinfo(ip)
    d3 = query_shodan(ip)

    if JSON_MODE:
        return build_json(ip, d1, d2, d3)
    show_report(ip, d1, d2, d3)
    return True

def main_loop():
    """Main loop — wapas yahin aata hai investigation ke baad."""
    while True:
        clear_screen()
        print(BANNER)

        print(f"\n{Colors.BOLD}{Colors.CYAN}┌─────────────────────────────────────────────────┐{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}│               MAIN MENU                        │{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}├─────────────────────────────────────────────────┤{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}│  [1] 🔍 Single IP Investigation                │{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}│  [2] 🌐 Check My Own IP                       │{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}│  [3] 🔄 Interactive Mode (Continuous)         │{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}│  [0] 🚪 Exit                                  │{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}└─────────────────────────────────────────────────┘{Colors.END}")

        choice = input(f"\n{Colors.YELLOW}{Colors.BOLD}╰➤  Enter choice [0-3]: {Colors.END}").strip()

        if choice == "0" or choice.lower() in ["exit", "quit", "q"]:
            print(f"\n{Colors.GREEN}{Colors.BOLD}👋 Exiting... Stay safe, bhai!{Colors.END}")
            break

        elif choice == "1":
            ip = input(f"\n{Colors.CYAN}{Colors.BOLD}Enter IP Address: {Colors.END}").strip()
            if ip.lower() in ["exit","quit","q","back","menu"]:
                continue
            if ip == "":
                p_warn("No IP entered!")
                input(f"\n{Colors.YELLOW}Press ENTER to continue...{Colors.END}")
                continue
            ip = resolve_target(ip)
            if ip is None:
                input(f"\n{Colors.YELLOW}Press ENTER to continue...{Colors.END}")
                continue
            process_ip(ip)
            input(f"\n{Colors.YELLOW}{Colors.BOLD}╰➤  Press ENTER to return to Main Menu...{Colors.END}")

        elif choice == "2":
            process_ip("")
            input(f"\n{Colors.YELLOW}{Colors.BOLD}╰➤  Press ENTER to return to Main Menu...{Colors.END}")

        elif choice == "3":
            print(f"\n{Colors.GREEN}{Colors.BOLD}Interactive Mode — type 'menu' to return or 'exit' to quit{Colors.END}\n")
            while True:
                try:
                    ip = input(f"{Colors.CYAN}{Colors.BOLD}IP > {Colors.END}").strip()
                    if ip.lower() in ["exit","quit","q"]:
                        print(f"\n{Colors.GREEN}👋 Exiting...{Colors.END}")
                        return  # Exit entire program
                    if ip.lower() in ["menu", "back", "main"]:
                        break  # Break to main menu
                    if ip.lower() in ["me", "my", ""]:
                        process_ip("")
                    else:
                        target = resolve_target(ip)
                        if target: process_ip(target)
                    print()
                except KeyboardInterrupt:
                    print("\n"); break

        else:
            p_err(f"Invalid choice: {choice}")
            input(f"\n{Colors.YELLOW}Press ENTER to continue...{Colors.END}")

# ═══════════════ ENTRY POINT ═══════════════

def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="ip_investigator_v3.py",
        description="IP INVESTIGATOR PRO v3.0 — passive IP intelligence (ip-api, ipinfo, Shodan). "
                    "Authorized / educational use only.")
    p.add_argument("target", nargs="?", help="IP or domain: show the report, then the menu")
    p.add_argument("--single", metavar="IP", help="investigate one IP/domain and exit (no menu)")
    p.add_argument("--json", action="store_true",
                   help="print the result as JSON on stdout (non-interactive, no menu)")
    return p.parse_args(argv)

def main(argv=None):
    global JSON_MODE
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.json:
        JSON_MODE = True
        target = args.single or args.target
        if not target:
            print(json.dumps({"error": "no target: use --json <ip|domain>"}))
            return 2
        ip = resolve_target(target)
        data = process_ip(ip) if ip else {"target": target, "error": "invalid IP or unresolvable domain"}
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0 if isinstance(data, dict) and "error" not in data else 1

    if args.single:
        print(BANNER)
        ip = resolve_target(args.single)
        ok = process_ip(ip) if ip else None
        return 0 if ok else 1

    if args.target:
        # Agar command line mein IP diya hai toh direct process karo, fir loop mein chale jao
        clear_screen()
        print(BANNER)
        ip = resolve_target(args.target)
        if ip: process_ip(ip)
        print()
        input(f"{Colors.YELLOW}{Colors.BOLD}╰➤  Press ENTER to enter Main Menu...{Colors.END}")

    main_loop()
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.GREEN}{Colors.BOLD}👋 Exiting... Stay safe, bhai!{Colors.END}", file=sys.stderr)
        sys.exit(130)
    except EOFError:
        print(f"\n{Colors.YELLOW}[!] No more input (EOF) — exiting. Use --single or --json for scripts.{Colors.END}",
              file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal Error: {mask_secrets(e)}{Colors.END}", file=sys.stderr)
        sys.exit(1)
