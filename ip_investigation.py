#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║         IP INVESTIGATOR PRO v3.0 — FINAL BEAST MODE        ║
║      SIM | WiFi | Carrier | Location | OS | Ports          ║
║                Authorized Pentesting Use Only                ║
╚══════════════════════════════════════════════════════════════╝

USAGE:  python3 ip_investigator_v3.py
        python3 ip_investigator_v3.py 8.8.8.8
        python3 ip_investigator_v3.py --single 1.1.1.1
"""

import json, sys, socket, requests, ipaddress, os, time
from datetime import datetime


# ===================== CONFIG =====================
from dotenv import load_dotenv

load_dotenv()

IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "").strip()
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY", "").strip()
# ==================================================

class Colors:
    HEADER = '\033[95m'; BLUE = '\033[94m'; CYAN = '\033[96m'
    GREEN = '\033[92m'; YELLOW = '\033[93m'; RED = '\033[91m'
    MAGENTA = '\033[35m'; BOLD = '\033[1m'; END = '\033[0m'; WHITE = '\033[97m'

# ════════════════ ASCII BANNER — NMAP STYLE EYE ════════════════
BANNER = f"""
{Colors.YELLOW}{Colors.BOLD}
        ___
     .-"   "-.       
    /  .-. .-.\      
   |   \o| |o |      ██╗██████╗
   |     ^    |      ██║██╔══██╗
   |   '---'  |      ██║██████╔╝
    \         /      ██║██╔═══╝
  ___'._____.'___    ██║██║
 /   /  | |  \   \   ╚═╝╚═╝ v2.0 Coded by argcyberskillhub⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
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

# ─────────── INDIAN CARRIER DATABASE ───────────
INDIAN_CARRIERS = {
    "AS55836": {"name": "Reliance Jio", "type": "4G/5G Mobile", "mcc": "405", "mnc": "840"},
    "AS9829":  {"name": "Bharti Airtel", "type": "4G/5G Mobile", "mcc": "404", "mnc": "90"},
    "AS55410": {"name": "Vodafone Idea (VI)", "type": "4G Mobile", "mcc": "404", "mnc": "94"},
    "AS45528": {"name": "Vodafone Idea (VI)", "type": "4G Mobile", "mcc": "404", "mnc": "95"},
    "AS24309": {"name": "BSNL", "type": "3G/4G Mobile", "mcc": "404", "mnc": "70"},
    "AS17813": {"name": "Bharti Airtel", "type": "Mobile/Broadband", "mcc": "404", "mnc": "90"},
    "AS17924": {"name": "Vodafone Idea (VI)", "type": "Mobile", "mcc": "404", "mnc": "94"},
    "AS9845":  {"name": "BSNL", "type": "Mobile/Broadband", "mcc": "404", "mnc": "70"},
    "AS17488": {"name": "Hathway", "type": "Broadband/Cable"},
    "AS45893": {"name": "YOU Broadband", "type": "Cable/Fiber"},
    "AS133982":{"name": "Excitel", "type": "Fiber Broadband"},
    "AS18101": {"name": "Tata Communications", "type": "Enterprise"},
    "AS4755":  {"name": "Tata Communications", "type": "Enterprise"},
    "AS15169": {"name": "Google LLC", "type": "Cloud/Datacenter"},
    "AS16509": {"name": "Amazon AWS", "type": "Cloud/Datacenter"},
    "AS8075":  {"name": "Microsoft Azure", "type": "Cloud/Datacenter"},
    "AS36351": {"name": "IBM Cloud", "type": "Cloud/Datacenter"},
    "AS24940": {"name": "Hetzner", "type": "Cloud/Datacenter"},
}

CARRIER_KEYWORDS = {
    "mobile": ["jio", "airtel", "vodafone", "idea", "vi ", "bsnl", "mtnl", "cell", "mobile", 
               "lte", "4g", "5g", "telecom", "cellular", "gsm", "umts"],
    "broadband": ["broadband", "dsl", "fiber", "fibre", "cable", "adsl", "hathway", "excitel",
                  "spectra", "you broadband", "tikona", "railwire", "comcast", "cox", "spectrum"],
    "datacenter": ["amazon", "aws", "azure", "microsoft", "google cloud", "gcp", "digitalocean",
                   "linode", "vultr", "ovh", "hetzner", "softlayer", "ibm", "oracle cloud",
                   "alibaba", "tencent", "cloudflare", "akamai"],
}

# ─────────── HELPERS ───────────

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def p_header(t): print(f"\n{Colors.BOLD}{Colors.CYAN}╔══ {t} {'═'*(60-len(t))}╗{Colors.END}")
def p_sub(t): print(f"{Colors.BOLD}{Colors.GREEN}├─ {t}{Colors.END}")
def p_kv(k, v, c=Colors.WHITE):
    if v and str(v) not in ["", "N/A", "None"]:
        print(f"│  {Colors.YELLOW}{k:<25}{Colors.END} : {c}{v}{Colors.END}")
def p_sep(): print(f"{Colors.CYAN}│{'─'*65}│{Colors.END}")
def p_err(m): print(f"{Colors.RED}[!] {m}{Colors.END}")
def p_ok(m): print(f"{Colors.GREEN}[✓] {m}{Colors.END}")
def p_info(m): print(f"{Colors.BLUE}[*] {m}{Colors.END}")
def p_warn(m): print(f"{Colors.YELLOW}[!] {m}{Colors.END}")

def validate_ip(ip):
    try:
        ipaddress.ip_address(ip); return True
    except: return False

def reverse_dns(ip):
    try: return socket.gethostbyaddr(ip)[0]
    except: return "N/A"

def spinner(seconds=0.5):
    for s in ['|', '/', '-', '\\']:
        print(f'\r{Colors.CYAN}{s}{Colors.END}', end='', flush=True)
        time.sleep(0.1)
    print('\r ', end='', flush=True)

# ─────────── API QUERIES ───────────

def query_ipapi(ip):
    p_info(f"📡 Querying ip-api.com for {ip}...")
    spinner()
    fields = "status,message,continent,continentCode,country,countryCode,region,regionName,city,district,zip,lat,lon,timezone,offset,currency,isp,org,as,asname,mobile,proxy,hosting,query"
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields={fields}", timeout=10)
        d = r.json()
        if d.get("status") == "fail":
            p_err(f"ip-api: {d.get('message')}"); return None
        p_ok("ip-api.com response received")
        return d
    except Exception as e:
        p_err(f"ip-api failed: {e}"); return None

def query_ipinfo(ip):
    p_info(f"📡 Querying ipinfo.io for {ip}...")
    spinner()
    try:
        url = f"https://ipinfo.io/{ip}/json"
        if IPINFO_TOKEN: url = f"https://ipinfo.io/{ip}?token={IPINFO_TOKEN}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            p_ok("ipinfo.io response received")
            return r.json()
        else:
            p_warn(f"ipinfo: HTTP {r.status_code}")
            return None
    except Exception as e:
        p_err(f"ipinfo failed: {e}"); return None

def query_shodan(ip):
    if not SHODAN_API_KEY:
        p_warn("Shodan API key not configured — skipping OS/Port scan")
        return None
    p_info(f"📡 Querying Shodan for {ip}...")
    spinner()
    try:
        r = requests.get(f"https://api.shodan.io/shodan/host/{ip}?key={SHODAN_API_KEY}", timeout=15)
        if r.status_code == 200:
            p_ok("Shodan response received")
            return r.json()
        elif r.status_code == 401:
            p_err("Shodan: Invalid API key!")
            return None
        elif r.status_code == 404:
            p_info("Shodan: No data found for this IP (not scanned)")
            return None
        else:
            p_warn(f"Shodan: HTTP {r.status_code}")
            return None
    except Exception as e:
        p_err(f"Shodan failed: {e}")
        return None

# ─────────── ANALYSIS ───────────

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
    
    if ip_api:
        asn_full = ip_api.get("as", "")
        if asn_full: asn_number = asn_full.split()[0] if " " in asn_full else asn_full
        asn_name = (ip_api.get("asname") or "").lower()
        isp_name = (ip_api.get("isp") or "").lower()
        org_name = (ip_api.get("org") or "").lower()
        if ip_api.get("proxy"): result["is_proxy"] = True
        if ip_api.get("hosting"): result["is_hosting"] = True
        if ip_api.get("mobile"): result["is_mobile"] = True
    
    if ipinfo:
        priv = ipinfo.get("privacy", {}) if isinstance(ipinfo.get("privacy"), dict) else {}
        if priv.get("vpn"): result["is_proxy"] = True
        if priv.get("proxy"): result["is_proxy"] = True
        if priv.get("tor"): result["is_tor"] = True
        if priv.get("hosting"): result["is_hosting"] = True
        
        mobile_data = ipinfo.get("mobile") or ipinfo.get("carrier")
        if mobile_data and isinstance(mobile_data, dict):
            result["is_mobile"] = True
            result["carrier"] = mobile_data.get("name") or mobile_data.get("carrier")
            result["mcc"] = mobile_data.get("mcc")
            result["mnc"] = mobile_data.get("mnc")
        
        if ipinfo.get("is_mobile") == True: result["is_mobile"] = True
        
        asn_info = ipinfo.get("asn", {})
        if isinstance(asn_info, dict) and asn_info.get("asn"):
            asn_number = asn_info["asn"]
            if not asn_name: asn_name = (asn_info.get("name") or "").lower()
    
    # ASN database match
    if asn_number and asn_number in INDIAN_CARRIERS:
        c = INDIAN_CARRIERS[asn_number]
        result["carrier"] = c["name"]
        result["type"] = f"📱 {c['name']} ({c['type']})"
        result["is_mobile"] = True
        result["confidence"] = "High"
        result["details"].append(f"ASN matched: {asn_number} = {c['name']}")
        if "mcc" in c: result["mcc"] = c["mcc"]
        if "mnc" in c: result["mnc"] = c["mnc"]
        return result
    
    combined = f"{asn_name} {isp_name} {org_name}"
    
    for kw in CARRIER_KEYWORDS["mobile"]:
        if kw in combined:
            result["is_mobile"] = True
            result["confidence"] = "Medium" if result["confidence"] == "Low" else result["confidence"]
            result["details"].append(f"Keyword '{kw}' in ISP/ASN name")
            if "jio" in combined: result["carrier"] = "Reliance Jio"
            elif "airtel" in combined: result["carrier"] = "Bharti Airtel"
            elif "vodafone" in combined or "idea" in combined or "vi " in combined: 
                result["carrier"] = "Vodafone Idea (VI)"
            elif "bsnl" in combined: result["carrier"] = "BSNL"
            else: result["carrier"] = "Indian Mobile Carrier"
            result["type"] = f"📱 {result['carrier']} (Mobile Network)"
            return result
    
    for kw in CARRIER_KEYWORDS["broadband"]:
        if kw in combined:
            result["type"] = "🏠 Residential Broadband / WiFi"
            result["confidence"] = "Medium"
            result["details"].append(f"Keyword '{kw}' in ISP/ASN name")
            return result
    
    for kw in CARRIER_KEYWORDS["datacenter"]:
        if kw in combined:
            result["type"] = "🏢 Datacenter / Cloud"
            result["is_hosting"] = True
            result["confidence"] = "High"
            result["details"].append(f"Keyword '{kw}' in ISP/ASN name")
            return result
    
    if result["is_hosting"]: result["type"] = "🏢 Datacenter / Cloud Hosting"; result["confidence"] = "High"
    elif result["is_proxy"]: result["type"] = "🔒 VPN / Proxy Server"; result["confidence"] = "High"
    elif result["is_tor"]: result["type"] = "🧅 TOR Exit Node"; result["confidence"] = "High"
    
    return result

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
    if net['mcc'] and net['mnc']:
        mcc_map = {"404":"🇮🇳 India","405":"🇮🇳 India","310":"🇺🇸 USA","234":"🇬🇧 UK","440":"🇯🇵 Japan","250":"🇷🇺 Russia","208":"🇫🇷 France","262":"🇩🇪 Germany","460":"🇨🇳 China","520":"🇹🇭 Thailand"}
        ctry = mcc_map.get(net['mcc'], f"MCC {net['mcc']}")
        p_kv("MCC", f"{net['mcc']} ({ctry})")
        p_kv("MNC", net['mnc'])
    
    p_sep()
    p_header("🚦 Traffic Classification:")
    for label, val, good in [
        ("📱 Mobile (SIM)", net['is_mobile'], True),
        ("🔒 VPN/Proxy", net['is_proxy'], False),
        ("🏢 Datacenter", net['is_hosting'], False),
        ("🧅 TOR Node", net['is_tor'], False)
    ]:
        c = Colors.GREEN if (good and val) or not val else Colors.RED
        icon = "✅" if (good and val) or not val else "⚠️"
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
            p_subheader("🔓 Open Ports:")
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
            p_subheader("Hostnames:")
            for hn in hns[:5]: print(f"│    • {hn}")
    else:
        print(f"│  {Colors.YELLOW}⏭️  Skipped — no Shodan API key configured{Colors.END}")
        print(f"│  {Colors.YELLOW}   To enable OS/Port detection:{Colors.END}")
        print(f"│  {Colors.YELLOW}   1. Sign up at https://account.shodan.io{Colors.END}")
        print(f"│  {Colors.YELLOW}   2. Set SHODAN_API_KEY in the script{Colors.END}")
    p_sep()
    
    # ── 6. THREAT ──
    p_header("🛡️ ANONYMITY & THREAT SCORE")
    risk = 0; risks = []
    if net['is_tor']: risk += 50; risks.append("🚨 TOR Exit Node — Extreme anonymity")
    if net['is_proxy']: risk += 30; risks.append("🔥 VPN/Proxy — High anonymity")
    if net['is_hosting']: risk += 15; risks.append("⚠️ Datacenter IP — VPS/Cloud possible")
    
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
            p_subheader("📧 Abuse Contact:")
            p_kv("Email", abuse.get("email"))
            p_kv("Country", abuse.get("country","N/A"))
    
    # ── SUMMARY ──
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'═'*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}   ✅ Investigation Complete{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}   📡 Network: {net['type']}{Colors.END}")
    if net['is_mobile']:
        print(f"{Colors.BOLD}{Colors.GREEN}   📱 This is a MOBILE (SIM Card) IP{Colors.END}")
        if net['carrier']: print(f"{Colors.BOLD}{Colors.MAGENTA}   🏢 Carrier: {net['carrier']}{Colors.END}")
    else:
        print(f"{Colors.BOLD}{Colors.BLUE}   🏠 This is BROADBAND / WiFi / Datacenter IP{Colors.END}")
    print(f"{Colors.HEADER}{'═'*70}{Colors.END}")

# ═══════════════ CORE LOOP ═══════════════

def process_ip(ip):
    """Single IP processing with complete flow."""
    if not ip or ip == "":
        try:
            ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
            p_ok(f"Your public IP: {ip}")
        except:
            p_err("Can't fetch your IP"); return None
    
    if not validate_ip(ip):
        p_err(f"Invalid IP format: {ip}")
        return None
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═'*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}   🔍 TARGET LOCKED: {ip}{Colors.END}")
    print(f"{Colors.CYAN}{'═'*70}{Colors.END}")
    
    d1 = query_ipapi(ip)
    d2 = query_ipinfo(ip)
    d3 = query_shodan(ip)
    
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
            if not validate_ip(ip):
                try:
                    resolved = socket.gethostbyname(ip)
                    p_info(f"Domain '{ip}' resolved to {resolved}")
                    ip = resolved
                except:
                    p_err(f"Cannot resolve '{ip}' as domain/IP")
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
                    elif not validate_ip(ip):
                        try:
                            r = socket.gethostbyname(ip)
                            p_info(f"Resolved {ip} → {r}")
                            process_ip(r)
                        except:
                            p_err(f"Can't resolve: {ip}")
                    else:
                        process_ip(ip)
                    print()
                except KeyboardInterrupt:
                    print("\n"); break
        
        else:
            p_err(f"Invalid choice: {choice}")
            input(f"\n{Colors.YELLOW}Press ENTER to continue...{Colors.END}")

# ═══════════════ ENTRY POINT ═══════════════

if __name__ == "__main__":
    try:
        # Agar command line mein IP diya hai toh direct process karo, fir loop mein chale jao
        if len(sys.argv) >= 2 and not sys.argv[1].startswith("--"):
            ip = sys.argv[1]
            if validate_ip(ip):
                clear_screen()
                print(BANNER)
                process_ip(ip)
                print()
                input(f"{Colors.YELLOW}{Colors.BOLD}╰➤  Press ENTER to enter Main Menu...{Colors.END}")
                main_loop()
            else:
                print(BANNER)
                p_err(f"Invalid IP: {ip}")
                input(f"\n{Colors.YELLOW}Press ENTER to continue...{Colors.END}")
                main_loop()
        else:
            main_loop()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.GREEN}{Colors.BOLD}👋 Exiting... Stay safe, bhai!{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Fatal Error: {e}{Colors.END}")
        sys.exit(1)