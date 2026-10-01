#!/usr/bin/env python3
"""Safe, resumable public-web research crawler (stdlib baseline)."""
from __future__ import annotations
import argparse, datetime as dt, fnmatch, hashlib, heapq, html, ipaddress, json, os
import re, socket, ssl, http.client, sys, tempfile, time, urllib.error, urllib.parse, urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.robotparser import RobotFileParser

VERSION = "1.0.0"
UA = "MinisPublicResearch/1.0"
TRACKING = {"fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid"}
INJECTION_PATTERNS = {
    "ignore_instructions": re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.I),
    "tool_or_shell_command": re.compile(r"(?:run|execute|call)\s+(?:this\s+)?(?:shell|terminal|tool|command)", re.I),
    "secret_exfiltration": re.compile(r"(?:reveal|print|send|exfiltrate).{0,40}(?:secret|token|password|api[_ -]?key)", re.I),
    "role_override": re.compile(r"(?:system|developer)\s*(?:message|prompt)|you\s+are\s+now", re.I),
}
ACCESS_PATTERNS = {
    "captcha": re.compile(r"captcha|verify you are human|unusual traffic", re.I),
    "login_wall": re.compile(r"log in to continue|sign in to continue|login required", re.I),
    "paywall": re.compile(r"subscribe to continue|subscription required|already a subscriber", re.I),
}


def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha256_bytes(data): return hashlib.sha256(data).hexdigest()
def canon_json(obj): return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
def atomic_json(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def append_jsonl(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(canon_json(obj) + "\n"); f.flush(); os.fsync(f.fileno())
def safe_child(root, *parts):
    root = Path(root).resolve(); out = root.joinpath(*parts).resolve()
    if root != out and root not in out.parents: raise ValueError("output path escapes run root")
    return out


def canonicalize(url):
    p = urllib.parse.urlsplit(url.strip())
    if p.scheme.lower() not in ("http", "https"): raise ValueError("only http/https URLs are allowed")
    if p.username or p.password: raise ValueError("URL userinfo is forbidden")
    host = (p.hostname or "").rstrip(".").lower()
    if not host: raise ValueError("missing hostname")
    try: port = p.port
    except ValueError: raise ValueError("invalid port")
    default = 80 if p.scheme.lower() == "http" else 443
    if port not in (None, default): raise ValueError("non-default ports are forbidden")
    netloc = host if port in (None, default) else f"{host}:{port}"
    path = p.path or "/"
    # Normalize percent encoding without changing path case or slash semantics.
    path = urllib.parse.quote(urllib.parse.unquote(path), safe="/%:@!$&'()*+,;=-._~")
    pairs = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    pairs = [(k, v) for k, v in pairs if not k.lower().startswith("utm_") and k.lower() not in TRACKING]
    query = urllib.parse.urlencode(pairs, doseq=True)
    return urllib.parse.urlunsplit((p.scheme.lower(), netloc, path, query, ""))


def host_allowed(host, allowed):
    host = host.lower().rstrip(".")
    return any(host == d or host.endswith("." + d) for d in allowed)

def resolve_public(url):
    p = urllib.parse.urlsplit(url); host = p.hostname
    if host in ("localhost", "localhost.localdomain") or host.endswith(".local"): raise ValueError("local hostname denied")
    infos = socket.getaddrinfo(host, p.port or (443 if p.scheme == "https" else 80), type=socket.SOCK_STREAM)
    ips = sorted({x[4][0] for x in infos})
    if not ips: raise ValueError("hostname resolved to no address")
    for raw in ips:
        ip = ipaddress.ip_address(raw.split("%", 1)[0])
        if not ip.is_global: raise ValueError(f"non-public address denied: {ip}")
    return ips


def policy_check(url, protocol):
    url = canonicalize(url); p = urllib.parse.urlsplit(url)
    if not host_allowed(p.hostname, protocol["allowed_domains"]): raise ValueError("domain outside allowlist")
    for pat in protocol["filters"]["deny_patterns"]:
        if fnmatch.fnmatch(url, pat): raise ValueError("URL matched deny pattern")
    inc = protocol["filters"]["include_patterns"]
    if inc and not any(fnmatch.fnmatch(url, pat) for pat in inc): raise ValueError("URL did not match include pattern")
    resolve_public(url)
    return url


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

class PinnedHTTPConnection(http.client.HTTPConnection):
    """Connect to a prevalidated IP while retaining the original Host header."""
    def __init__(self, host, port, connect_ip, timeout):
        super().__init__(host, port=port, timeout=timeout); self._connect_ip = connect_ip
    def connect(self):
        self.sock = socket.create_connection((self._connect_ip, self.port), self.timeout, self.source_address)

class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, port, connect_ip, timeout):
        super().__init__(host, port=port, timeout=timeout, context=ssl.create_default_context()); self._connect_ip = connect_ip
    def connect(self):
        sock = socket.create_connection((self._connect_ip, self.port), self.timeout, self.source_address)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def open_pinned(url, protocol):
    p = urllib.parse.urlsplit(url); ips = resolve_public(url); connect_ip = ips[0]
    host = p.hostname; port = p.port or (443 if p.scheme == "https" else 80)
    cls = PinnedHTTPSConnection if p.scheme == "https" else PinnedHTTPConnection
    conn = cls(host, port, connect_ip, protocol["budgets"]["timeout_seconds"])
    target = urllib.parse.urlunsplit(("", "", p.path or "/", p.query, ""))
    conn.request("GET", target, headers={"Host": host, "User-Agent": protocol["user_agent"], "Accept": "text/html,application/xhtml+xml,application/xml,text/plain;q=0.8,*/*;q=0.1", "Accept-Encoding": "identity", "Connection": "close"})
    return conn, conn.getresponse(), connect_ip


def fetch_limited(url, protocol, max_bytes, robots=None):
    current = policy_check(url, protocol); redirects = []
    for _ in range(6):
        if robots is not None and not robots.allowed(current):
            return {"ok": False, "kind": "robots_denied", "url": current, "redirects": redirects}
        conn = None
        try:
            conn, resp, connect_ip = open_pinned(current, protocol)
            status = resp.status; headers = {k: v for k, v in resp.getheaders()}
            if status in (301, 302, 303, 307, 308):
                loc = headers.get("Location")
                if not loc: return {"ok": False, "kind": "redirect_without_location", "status": status, "url": current, "redirects": redirects}
                nxt = policy_check(urllib.parse.urljoin(current, loc), protocol)
                redirects.append({"from": current, "to": nxt, "status": status}); current = nxt; conn.close(); continue
            if status >= 400:
                return {"ok": False, "kind": "restricted" if status in (401,403,429) else "http_error", "status": status, "url": current, "headers": headers, "redirects": redirects}
        except Exception as e:
            return {"ok": False, "kind": "network_error", "url": current, "error": type(e).__name__ + ": " + str(e), "redirects": redirects}
        length = headers.get("Content-Length")
        if length and length.isdigit() and int(length) > max_bytes:
            conn.close(); return {"ok": False, "kind": "oversize", "status": status, "url": current, "headers": headers, "redirects": redirects}
        data = bytearray()
        while True:
            chunk = resp.read(min(65536, max_bytes + 1 - len(data)))
            if not chunk: break
            data.extend(chunk)
            if len(data) > max_bytes:
                conn.close(); return {"ok": False, "kind": "oversize", "status": status, "url": current, "headers": headers, "redirects": redirects}
        conn.close()
        return {"ok": True, "status": status, "url": current, "headers": headers, "body": bytes(data), "redirects": redirects, "peer_validation": {"mode":"pinned_prevalidated_ip","connect_ip":connect_ip}}
    return {"ok": False, "kind": "too_many_redirects", "url": current, "redirects": redirects}


class Robots:
    def __init__(self, protocol): self.p = protocol; self.cache = {}; self.last = {}
    def _load(self, url):
        origin = urllib.parse.urlunsplit((*urllib.parse.urlsplit(url)[:2], "/robots.txt", "", ""))
        if origin in self.cache: return self.cache[origin]
        r = fetch_limited(origin, self.p, min(262144, self.p["budgets"]["max_bytes_per_url"]), robots=None)
        rp = RobotFileParser(); rp.set_url(origin)
        if r.get("ok"):
            text = decode_body(r["body"], r.get("headers", {})); rp.parse(text.splitlines()); state = (rp, sha256_bytes(r["body"]), None)
        elif r.get("status") == 404:
            rp.parse([]); state = (rp, None, None)
        else:
            state = (None, None, r.get("kind", "unavailable"))
        self.cache[origin] = state; return state
    def allowed(self, url):
        if not self.p["policy"]["respect_robots"]: return True
        rp, _, err = self._load(url)
        if err: return not self.p["policy"]["robots_fail_closed"]
        return rp.can_fetch(self.p["user_agent"], url)
    def delay(self, url):
        rp, _, _ = self._load(url)
        d = rp.crawl_delay(self.p["user_agent"]) if rp else None
        return max(float(d or 0), self.p["budgets"]["host_delay_seconds"])


def decode_body(data, headers):
    ctype = headers.get("Content-Type", headers.get("content-type", ""))
    m = re.search(r"charset=([\w.:-]+)", ctype, re.I)
    enc = m.group(1) if m else "utf-8"
    try: return data.decode(enc, errors="replace")
    except LookupError: return data.decode("utf-8", errors="replace")


class PageParser(HTMLParser):
    SKIP = {"script", "style", "iframe", "noscript", "svg", "canvas", "template"}
    BLOCK = {"p", "div", "section", "article", "header", "footer", "main", "aside", "blockquote", "pre", "tr"}
    def __init__(self):
        super().__init__(convert_charrefs=True); self.skip=0; self.title=[]; self.in_title=False; self.lines=[]; self.buf=[]; self.links=[]; self.feed_links=[]; self.script_count=0
    def flush(self, prefix=""):
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip(); self.buf=[]
        if text: self.lines.append(prefix + text)
    def handle_starttag(self, tag, attrs):
        tag=tag.lower(); a=dict(attrs)
        if tag=="script": self.script_count += 1
        if tag in self.SKIP: self.skip += 1; return
        if self.skip: return
        if tag=="title": self.in_title=True
        if tag in self.BLOCK or tag in {"h1","h2","h3","h4","h5","h6","li","br"}: self.flush()
        if tag=="a" and a.get("href"): self.links.append((a["href"], "link"))
        if tag=="link" and a.get("href") and ("alternate" in a.get("rel", "").lower()) and ("rss" in a.get("type", "").lower() or "atom" in a.get("type", "").lower()): self.feed_links.append(a["href"])
    def handle_endtag(self, tag):
        tag=tag.lower()
        if tag in self.SKIP:
            self.skip=max(0,self.skip-1); return
        if self.skip: return
        if tag=="title": self.in_title=False
        prefix = ""
        if tag in {"h1","h2","h3","h4","h5","h6"}: prefix = "#"*int(tag[1]) + " "
        elif tag=="li": prefix="- "
        if tag in self.BLOCK or tag in {"h1","h2","h3","h4","h5","h6","li"}: self.flush(prefix)
    def handle_data(self, data):
        if self.skip: return
        if self.in_title: self.title.append(data)
        self.buf.append(data)
    def result(self):
        self.flush(); clean=[]
        for x in self.lines:
            x=html.unescape(x).strip()
            if x and (not clean or x != clean[-1]): clean.append(x)
        title=re.sub(r"\s+", " ", "".join(self.title)).strip()
        return title, "\n\n".join(clean).strip()+("\n" if clean else ""), self.links, self.feed_links, self.script_count


def parse_document(text, ctype, url):
    if "html" in ctype or "xhtml" in ctype or re.search(r"<html|<!doctype", text[:1000], re.I):
        p=PageParser(); p.feed(text); title, markdown, links, feeds, scripts=p.result()
        return title, markdown, re.sub(r"^#+\s+", "", markdown, flags=re.M), links, feeds, scripts
    # XML/RSS/sitemap: conservative loc/link extraction, no DTD/entity processing.
    if "xml" in ctype or url.lower().endswith((".xml", ".rss", ".atom")):
        if re.search(r"<!DOCTYPE|<!ENTITY", text[:4096], re.I): raise ValueError("DTD/entity XML denied")
        vals=re.findall(r"<(?:loc|link)(?:\s[^>]*)?>(.*?)</(?:loc|link)>", text, re.I|re.S)
        links=[(re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", "", x))), "xml") for x in vals]
        plain=re.sub(r"<[^>]+>", " ", text); plain=re.sub(r"\s+", " ", html.unescape(plain)).strip()
        return "", plain+"\n", plain+"\n", links, [], 0
    plain=text.replace("\x00", ""); return "", plain, plain, [], [], 0


def flags_for(text): return [k for k,p in INJECTION_PATTERNS.items() if p.search(text[:100000])]
def access_flag(text):
    return next((k for k,p in ACCESS_PATTERNS.items() if p.search(text[:100000])), None)
def url_score(url, query):
    if not query: return 0.0
    hay=urllib.parse.unquote(url).lower(); terms=set(re.findall(r"[\w\u4e00-\u9fff]+", query.lower()))
    return sum(1 for t in terms if t in hay) / max(1,len(terms))


class Run:
    def __init__(self, root, protocol, resume=False):
        self.root=Path(root).resolve(); self.p=protocol; self.events=self.root/"events.jsonl"; self.seq=0; self.head="0"*64; self.urls={}; self.frontier=[]; self.counter=0; self.bytes=0; self.pages=0; self.last_host={}; self.robots=Robots(protocol)
        if resume: self.load()
    def event(self, typ, payload=None, url_id=None):
        self.seq+=1; e={"seq":self.seq,"ts":now(),"run_id":self.p["run_id"],"event_type":typ,"url_id":url_id,"payload":payload or {},"actor":"pwr/http","tool_version":VERSION,"prev_event_hash":self.head}
        e["event_hash"]=sha256_bytes(canon_json(e).encode()); append_jsonl(self.events,e); self.head=e["event_hash"]; return e
    def checkpoint(self, completed=False):
        self.event("checkpoint.saved", {"completed":completed,"pages":self.pages,"bytes":self.bytes})
        obj={"schema_version":"1","run_id":self.p["run_id"],"last_event_seq":self.seq,"last_event_hash":self.head,"frontier":[x[-1] for x in self.frontier],"urls":self.urls,"budget_used":{"pages":self.pages,"bytes":self.bytes},"updated_at":now(),"completed":completed}
        atomic_json(self.root/"checkpoint.json",obj); self.write_urls()
    def write_urls(self):
        path=self.root/"urls.jsonl"; tmp=path.with_suffix(".tmp")
        with open(tmp,"w",encoding="utf-8") as f:
            for x in sorted(self.urls.values(),key=lambda v:v["url_id"]): f.write(canon_json(x)+"\n")
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    def add(self,url,depth,parent=None,method="link"):
        try: u=canonicalize(url); policy_check(u,self.p)
        except Exception as e:
            self.event("url.denied",{"url":url,"reason":str(e)}); return
        uid=sha256_bytes(u.encode())
        if uid in self.urls: return
        if depth>self.p["budgets"]["max_depth"]: return
        item={"url_id":uid,"requested_url":url,"canonical_url":u,"parent_url_id":parent,"depth":depth,"discovery_method":method,"status":"queued","attempts":0,"priority":url_score(u,self.p.get("query",""))}
        self.urls[uid]=item; self.counter+=1
        key=-item["priority"] if self.p["mode"]=="best-first" else depth
        heapq.heappush(self.frontier,(key,self.counter,item)); self.event("url.discovered",{"url":u,"depth":depth,"method":method},uid)
    def load(self):
        with open(self.root/"checkpoint.json",encoding="utf-8") as f: cp=json.load(f)
        ok,head,seq=validate_events(self.events)
        if not ok or head!=cp["last_event_hash"] or seq!=cp["last_event_seq"]: raise RuntimeError("event/checkpoint integrity mismatch")
        self.seq=seq; self.head=head; self.urls=cp["urls"]; self.pages=cp["budget_used"]["pages"]; self.bytes=cp["budget_used"]["bytes"]
        for item in cp["frontier"]:
            if self.urls.get(item["url_id"],{}).get("status") not in ("parsed","restricted","denied","failed","oversize","budget_skipped"):
                self.counter+=1; key=-item.get("priority",0) if self.p["mode"]=="best-first" else item["depth"]; heapq.heappush(self.frontier,(key,self.counter,item))
    def throttle(self,url):
        host=urllib.parse.urlsplit(url).hostname; delay=self.robots.delay(url); wait=delay-(time.monotonic()-self.last_host.get(host,0))
        if wait>0: time.sleep(wait)
        self.last_host[host]=time.monotonic()
    def crawl(self):
        while self.frontier and self.pages < self.p["budgets"]["max_pages"] and self.bytes < self.p["budgets"]["max_bytes_total"]:
            _,_,item=heapq.heappop(self.frontier); uid=item["url_id"]; state=self.urls[uid]
            if state["status"] in ("parsed","restricted","denied","failed","oversize"): continue
            remain=self.p["budgets"]["max_bytes_total"]-self.bytes
            if remain<=0: break
            self.throttle(item["canonical_url"]); state["status"]="fetching"; state["attempts"]+=1; self.event("url.fetch_started",{"url":item["canonical_url"]},uid)
            r=fetch_limited(item["canonical_url"],self.p,min(remain,self.p["budgets"]["max_bytes_per_url"]),self.robots)
            for red in r.get("redirects",[]): self.event("url.redirected",red,uid)
            if not r.get("ok"):
                kind=r.get("kind","failed"); state["status"]="denied" if kind=="robots_denied" else kind
                state["error_code"]=kind; state["http_status"]=r.get("status"); self.event("url.robots_denied" if kind=="robots_denied" else "url.failed",r,uid); self.checkpoint(); continue
            body=r["body"]; headers=r["headers"]; ctype=headers.get("Content-Type",headers.get("content-type","")).split(";",1)[0].lower()
            if ctype and not any(x in ctype for x in ("html","xhtml","xml","rss","atom","text/plain")):
                state.update(status="unsupported_content",http_status=r["status"],content_type=ctype); self.event("url.failed",{"kind":"unsupported_content","content_type":ctype},uid); self.checkpoint(); continue
            rawhash=sha256_bytes(body); raw=safe_child(self.root,"raw",uid+".bin"); raw.parent.mkdir(parents=True,exist_ok=True)
            if raw.exists() and sha256_bytes(raw.read_bytes())!=rawhash: raise RuntimeError("immutable raw artifact collision")
            if not raw.exists(): raw.write_bytes(body)
            atomic_json(safe_child(self.root,"raw",uid+".headers.json"),{"url":r["url"],"status":r["status"],"headers":headers,"captured_at":now(),"sha256":rawhash,"bytes":len(body)})
            self.bytes+=len(body); self.pages+=1; self.event("url.fetched",{"status":r["status"],"final_url":r["url"],"raw_sha256":rawhash,"bytes":len(body)},uid)
            text=decode_body(body,headers)
            af=access_flag(text)
            if af:
                state.update(status="restricted",http_status=r["status"],final_url=r["url"],raw_sha256=rawhash,error_code=af); self.event("url.failed",{"kind":"access_restriction","marker":af},uid); self.checkpoint(); continue
            try: title,md,plain,links,feeds,scripts=parse_document(text,ctype,r["url"])
            except Exception as e:
                state.update(status="failed",error_code="parse_error"); self.event("url.failed",{"kind":"parse_error","error":str(e)},uid); self.checkpoint(); continue
            mdhash=sha256_bytes(md.encode()); txthash=sha256_bytes(plain.encode())
            mp=safe_child(self.root,"derived","markdown",uid+".md"); tp=safe_child(self.root,"derived","text",uid+".txt"); mp.parent.mkdir(parents=True,exist_ok=True); tp.parent.mkdir(parents=True,exist_ok=True); mp.write_text(md,encoding="utf-8"); tp.write_text(plain,encoding="utf-8")
            sec=flags_for(plain); shell=(len(plain.strip())<200 and scripts>=2)
            state.update(status="parsed",final_url=r["url"],http_status=r["status"],content_type=ctype,raw_sha256=rawhash,bytes=len(body),title=title,markdown_sha256=mdhash,text_sha256=txthash,security_flags=sec,escalation_required=shell)
            self.event("artifact.created",{"raw_sha256":rawhash,"markdown_sha256":mdhash,"text_sha256":txthash,"input_sha256":rawhash},uid)
            self.event("url.parsed",{"title":title,"links":len(links),"security_flags":sec,"escalation_required":shell},uid)
            cand={"candidate_id":"candidate:"+uid,"artifact_id":"artifact:"+rawhash,"canonical_url":item["canonical_url"],"final_url":r["url"],"title":title,"captured_at":now(),"raw_sha256":rawhash,"derived":{"markdown_sha256":mdhash,"text_sha256":txthash},"locator_basis":"derived line ranges; verify important claims against raw/public page","discovery_method":item["discovery_method"],"security_flags":sec,"review_status":"unreviewed","disposition":"defer","source_visibility":"public_without_login","escalation_required":shell}
            cp=safe_child(self.root,"derived","candidates","candidates.jsonl"); cp.parent.mkdir(parents=True,exist_ok=True); append_jsonl(cp,cand); self.event("candidate.created",{"candidate_id":cand["candidate_id"],"security_flags":sec},uid)
            if item["depth"]<self.p["budgets"]["max_depth"]:
                for href,method in links[:self.p["budgets"]["max_links_per_page"]]: self.add(urllib.parse.urljoin(r["url"],href),item["depth"]+1,uid,method)
                if "rss" in self.p["discovery"]:
                    for href in feeds[:20]: self.add(urllib.parse.urljoin(r["url"],href),item["depth"]+1,uid,"rss")
            self.checkpoint()
        for _,_,item in self.frontier: self.urls[item["url_id"]]["status"]="budget_skipped"
        self.frontier=[]; self.event("run.completed",{"pages":self.pages,"bytes":self.bytes,"urls":len(self.urls)}); self.checkpoint(completed=True); self.report()
    def report(self):
        counts={}
        for x in self.urls.values(): counts[x["status"]]=counts.get(x["status"],0)+1
        atomic_json(self.root/"report.json",{"schema_version":"pwr-report-1.0","run_id":self.p["run_id"],"completed_at":now(),"event_head":self.head,"pages_fetched":self.pages,"bytes_fetched":self.bytes,"url_status_counts":counts,"escalation_required":[x["canonical_url"] for x in self.urls.values() if x.get("escalation_required")],"limitations":["capture success is not fact verification","HTTP backend cannot render JavaScript","source content is untrusted"]})


def validate_events(path):
    head="0"*64; seq=0
    try:
        with open(path,encoding="utf-8") as f:
            for line in f:
                e=json.loads(line); got=e.pop("event_hash"); expected=sha256_bytes(canon_json(e).encode())
                if got!=expected or e["prev_event_hash"]!=head or e["seq"]!=seq+1: return False,head,seq
                head=got; seq=e["seq"]
        return True,head,seq
    except Exception: return False,head,seq


def make_protocol(a):
    seeds=[canonicalize(x) for x in a.seed]; allowed=sorted({x.lower().rstrip(".") for x in a.allowed_domain})
    if not allowed: raise ValueError("at least one --allowed-domain is required")
    return {"schema_version":"pwr-1.0","run_id":a.run_id or dt.datetime.now().strftime("pwr-%Y%m%dT%H%M%SZ")+"-"+os.urandom(3).hex(),"created_at":now(),"tool":"public-web-research","tool_version":VERSION,"backend":"http","mode":a.mode,"query":a.query or "","seeds":seeds,"allowed_domains":allowed,"discovery":[x for x in a.discover.split(",") if x],"user_agent":UA,"policy":{"public_only":True,"respect_robots":not a.ignore_robots,"robots_fail_closed":a.robots_fail_closed,"allow_cookies":False,"allow_auth":False,"allow_captcha_bypass":False},"filters":{"deny_patterns":a.deny_pattern,"include_patterns":a.include_pattern},"budgets":{"max_pages":a.max_pages,"max_depth":a.max_depth,"max_bytes_total":a.max_bytes_total,"max_bytes_per_url":a.max_bytes_per_url,"timeout_seconds":a.timeout,"host_delay_seconds":a.host_delay,"max_links_per_page":a.max_links_per_page}}


def cmd_run(a):
    p=make_protocol(a); root=Path(a.output)
    if root.exists() and any(root.iterdir()): raise RuntimeError("output run directory already exists and is non-empty")
    for d in ("raw","derived/markdown","derived/text","derived/candidates"): (root/d).mkdir(parents=True,exist_ok=True)
    atomic_json(root/"protocol.json",p); run=Run(root,p); run.event("run.created",{"protocol_sha256":sha256_bytes((root/"protocol.json").read_bytes())})
    for s in p["seeds"]:
        run.add(s,0,None,"seed")
        origin=urllib.parse.urlunsplit((*urllib.parse.urlsplit(s)[:2],"/sitemap.xml","",""))
        if "sitemap" in p["discovery"]: run.add(origin,0,None,"sitemap")
    run.checkpoint(); run.crawl()
    with open(root/"report.json",encoding="utf-8") as f: report=json.load(f)
    print(json.dumps(report,ensure_ascii=False,indent=2))
def cmd_resume(a):
    root=Path(a.run)
    with open(root/"protocol.json",encoding="utf-8") as f: p=json.load(f)
    run=Run(root,p,resume=True)
    with open(root/"checkpoint.json",encoding="utf-8") as f: completed=json.load(f)["completed"]
    if completed: print("run already completed"); return
    run.event("run.resumed",{}); run.crawl()
def cmd_validate(a):
    root=Path(a.run)
    with open(root/"checkpoint.json",encoding="utf-8") as f: cp=json.load(f)
    ok,head,seq=validate_events(root/"events.jsonl"); errors=[]
    if not ok or head!=cp["last_event_hash"] or seq!=cp["last_event_seq"]: errors.append("event/checkpoint chain mismatch")
    for x in cp["urls"].values():
        if x.get("raw_sha256"):
            f=root/"raw"/(x["url_id"]+".bin")
            if not f.exists() or sha256_bytes(f.read_bytes())!=x["raw_sha256"]: errors.append("raw hash mismatch: "+x["url_id"])
    print(json.dumps({"valid":not errors,"events":seq,"head":head,"errors":errors},indent=2)); return 0 if not errors else 5
def cmd_inspect(a):
    root=Path(a.run); print((root/"report.json").read_text() if (root/"report.json").exists() else (root/"checkpoint.json").read_text())
def cmd_probe(_):
    try:
        import crawl4ai
        c4={"available":True,"version":getattr(crawl4ai,"__version__","unknown")}
    except Exception as e: c4={"available":False,"reason":type(e).__name__}
    print(json.dumps({"http_backend":True,"crawl4ai":c4,"browser_fallback":"use Minis browser_use separately"},ensure_ascii=False,indent=2))


def parser():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest="cmd",required=True)
    r=sub.add_parser("run"); r.add_argument("--seed",action="append",required=True); r.add_argument("--allowed-domain",action="append",required=True); r.add_argument("--output",required=True); r.add_argument("--run-id"); r.add_argument("--mode",choices=("bfs","best-first"),default="bfs"); r.add_argument("--query"); r.add_argument("--max-depth",type=int,default=1); r.add_argument("--max-pages",type=int,default=20); r.add_argument("--max-bytes-total",type=int,default=20*1024*1024); r.add_argument("--max-bytes-per-url",type=int,default=2*1024*1024); r.add_argument("--max-links-per-page",type=int,default=200); r.add_argument("--timeout",type=int,default=20); r.add_argument("--host-delay",type=float,default=1.0); r.add_argument("--discover",default="links"); r.add_argument("--deny-pattern",action="append",default=[]); r.add_argument("--include-pattern",action="append",default=[]); r.add_argument("--ignore-robots",action="store_true",help="only use when user has authority; recorded in protocol"); r.add_argument("--robots-fail-closed",action=argparse.BooleanOptionalAction,default=True); r.set_defaults(func=cmd_run)
    for name,func in (("resume",cmd_resume),("inspect",cmd_inspect),("validate",cmd_validate)):
        x=sub.add_parser(name); x.add_argument("--run",required=True); x.set_defaults(func=func)
    x=sub.add_parser("probe"); x.set_defaults(func=cmd_probe); return p

def main():
    a=parser().parse_args()
    try: return a.func(a) or 0
    except (ValueError,RuntimeError) as e: print(f"error: {e}",file=sys.stderr); return 4
    except KeyboardInterrupt: print("interrupted; resume with the run directory",file=sys.stderr); return 3
if __name__=="__main__": raise SystemExit(main())
