#!/usr/bin/env python3
"""ERL-compatible public-source research adapter.

Reads ACTIVE trajectories and append-only acquisition requests, searches only configured
public sources, emits lead-only candidates and receipts, and never promotes conclusions.
No GitHub credential is used or treated as research/evaluation authority.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,pathlib,re,urllib.request
from datetime import datetime,timezone
from html.parser import HTMLParser
from urllib.parse import urljoin

UA="StegVerse-ERL-Research/1.0"

def now(): return datetime.now(timezone.utc).isoformat()
def sid(*parts): return hashlib.sha256("|".join(map(str,parts)).encode()).hexdigest()[:24]
def append_jsonl(path,obj,dry=False):
    if dry: return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as f: f.write(json.dumps(obj,sort_keys=True)+"\n")

def load_json(path): return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
def load_jsonl(path):
    if not path.exists(): return []
    out=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip(): out.append(json.loads(line))
    return out

def whitelist(path):
    if not path.exists(): return []
    with path.open(newline="",encoding="utf-8") as f: return list(csv.DictReader(f))

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self._href=None; self._txt=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a": self._href=dict(attrs).get("href"); self._txt=[]
    def handle_data(self,data):
        if self._href is not None: self._txt.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self._href is not None:
            self.links.append((" ".join(self._txt).strip(),self._href)); self._href=None; self._txt=[]

def fetch(url,timeout=15):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        ct=r.headers.get("Content-Type","")
        data=r.read(2_000_000)
    return data,ct

def terms(text): return [t.lower() for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9._-]{2,}",text or "")][:12]

def active_requests(base):
    frontier=load_json(base/"research/frontier.json")
    reqs=load_jsonl(base/"research/acquisition_requests.jsonl")
    for t in frontier.get("trajectories",[]):
        if t.get("state") in {"OPEN","ACTIVE"}:
            for q in t.get("acquisition_queries",[]):
                reqs.append({"request_id":"frontier-"+sid(t.get("trajectory_id"),q),"trajectory_ids":[t.get("trajectory_id")],"query":q,"state":"ACTIVE"})
    return [r for r in reqs if r.get("state","ACTIVE") in {"OPEN","ACTIVE","RETRY"}]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--base",default="."); ap.add_argument("--dry-run",action="store_true"); args=ap.parse_args()
    base=pathlib.Path(args.base).resolve(); sources=whitelist(base/"data/sources/sources_whitelist.csv"); requests=active_requests(base)
    seen=set(); emitted=0
    for req in requests:
        qterms=terms(req.get("query", ""))
        for src in sources:
            url=(src.get("url") or "").strip()
            if not url: continue
            try:
                data,ct=fetch(url); digest=hashlib.sha256(data).hexdigest(); text=data.decode("utf-8",errors="ignore")
                parser=Links(); parser.feed(text)
                hits=[]
                for title,href in parser.links:
                    hay=(title+" "+href).lower()
                    if qterms and not all(t in hay for t in qterms): continue
                    link=urljoin(url,href); key=sid(link)
                    if key in seen: continue
                    seen.add(key); hits.append((title,link))
                for title,link in hits[:10]:
                    candidate={"candidate_id":"SRC-"+sid(req.get("request_id"),link),"repository":base.name,"trajectory_ids":req.get("trajectory_ids",[]),"acquisition_request_id":req.get("request_id"),"query":req.get("query",""),"source_url":link,"source_title":title,"retrieved_at":now(),"source_class":src.get("authority_class") or "unknown","institutional_proximity":"unknown","content_hash":None,"custody_pointer":None,"verification_state":"unverified","evidence_role":"lead-only","discovered_by":"scripts/search_agent.py","notes":"Candidate only; ERL review required."}
                    append_jsonl(base/"research/source_candidates.jsonl",candidate,args.dry_run); emitted+=1
                receipt={"receipt_id":"RSRCH-"+sid(req.get("request_id"),url,digest),"request_id":req.get("request_id"),"trajectory_ids":req.get("trajectory_ids",[]),"source_scanned":url,"retrieved_at":now(),"response_hash":digest,"content_type":ct,"hits":len(hits),"result":"NO_UPDATE" if not hits else "CANDIDATES_EMITTED"}
                append_jsonl(base/"research/research_receipts.jsonl",receipt,args.dry_run)
            except Exception as e:
                append_jsonl(base/"research/research_receipts.jsonl",{"receipt_id":"RSRCH-"+sid(req.get("request_id"),url,now()),"request_id":req.get("request_id"),"trajectory_ids":req.get("trajectory_ids",[]),"source_scanned":url,"retrieved_at":now(),"result":"FAILED","error":type(e).__name__},args.dry_run)
    print(json.dumps({"requests":len(requests),"sources":len(sources),"candidates":emitted,"dry_run":args.dry_run},sort_keys=True))
if __name__=="__main__": main()
