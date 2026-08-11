#!/usr/bin/env python3
"""ERL-compatible public-source research adapter.

Reads ACTIVE trajectories and append-only acquisition requests, searches only configured
public sources, emits lead-only candidates and receipts, and never promotes conclusions.
Candidate packets conform to the ERL intake contract. GitHub credentials have no research
or evaluation authority; applicable credential authority remains TV/TVC.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,pathlib,re,urllib.request
from datetime import datetime,timezone
from html.parser import HTMLParser
from urllib.parse import urljoin

REPOSITORY="StegVerse-Labs/Administrations"
UA="StegVerse-ERL-Research/1.1"

def now(): return datetime.now(timezone.utc).isoformat()
def sid(*parts): return hashlib.sha256("|".join(map(str,parts)).encode()).hexdigest()[:24]
def append_jsonl(path,obj,dry=False):
    if dry:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as f:f.write(json.dumps(obj,sort_keys=True)+"\n")
def load_json(path): return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
def load_jsonl(path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()] if path.exists() else []
def whitelist(path):
    if not path.exists():return []
    with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.href=None;self.txt=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":self.href=dict(attrs).get("href");self.txt=[]
    def handle_data(self,data):
        if self.href is not None:self.txt.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:self.links.append((" ".join(self.txt).strip(),self.href));self.href=None;self.txt=[]
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=15) as r:return r.read(2_000_000),r.headers.get("Content-Type","")
def terms(text):return [x.lower() for x in re.findall(r"[A-Za-z0-9][A-Za-z0-9._-]{2,}",text or "")][:12]
def active_requests(base):
    out=load_jsonl(base/"research/acquisition_requests.jsonl");frontier=load_json(base/"research/frontier.json")
    for trajectory in frontier.get("trajectories",[]):
        if trajectory.get("state") in {"OPEN","ACTIVE"}:
            for query in trajectory.get("acquisition_queries",[]):
                out.append({"request_id":"frontier-"+sid(trajectory.get("trajectory_id"),query),"trajectory_ids":[trajectory.get("trajectory_id")],"query":query,"state":"ACTIVE"})
    return [r for r in out if r.get("state","ACTIVE") in {"OPEN","ACTIVE","RETRY"}]
def candidate(req,src,title,link):
    return {"schema":"stegverse.erl.research_source_candidate.v1","candidate_id":"SRC-"+sid(req.get("request_id"),link),"repository":REPOSITORY,"trajectory_ids":req.get("trajectory_ids",[]),"acquisition_request_id":req.get("request_id"),"query":req.get("query",""),"source_url":link,"source_title":title,"retrieved_at":now(),"source_class":src.get("authority_class") or src.get("type") or "unknown","authority_proximity":"unknown","content_sha256":None,"custody_pointer":None,"verification_state":"UNVERIFIED","evidence_role":"lead-only","discovered_by":"scripts/search_agent.py","native_records_mutated":False,"evaluation_changed":False,"transport":{"source_repository":REPOSITORY,"destination_repository":"StegVerse-Labs/Executive_Rhetoric_Ledger","authority_effect":"NONE","credential_authority":"TV/TVC","github_token_authority":"NONE"}}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--base",default=".");ap.add_argument("--dry-run",action="store_true");args=ap.parse_args();base=pathlib.Path(args.base).resolve();sources=whitelist(base/"data/sources/sources_whitelist.csv");requests=active_requests(base);seen=set();emitted=0
    for req in requests:
        qterms=terms(req.get("query",""))
        for src in sources:
            url=(src.get("url") or "").strip()
            if not url:continue
            try:
                data,ct=fetch(url);digest=hashlib.sha256(data).hexdigest();parser=Links();parser.feed(data.decode("utf-8",errors="ignore"));hits=[]
                for title,href in parser.links:
                    hay=(title+" "+href).lower()
                    if qterms and not all(t in hay for t in qterms):continue
                    link=urljoin(url,href);key=sid(link)
                    if key in seen:continue
                    seen.add(key);hits.append((title,link))
                for title,link in hits[:10]:append_jsonl(base/"research/source_candidates.jsonl",candidate(req,src,title,link),args.dry_run);emitted+=1
                append_jsonl(base/"research/research_receipts.jsonl",{"receipt_id":"RSRCH-"+sid(req.get("request_id"),url,digest),"request_id":req.get("request_id"),"trajectory_ids":req.get("trajectory_ids",[]),"source_scanned":url,"retrieved_at":now(),"response_hash":digest,"content_type":ct,"hits":len(hits),"result":"NO_UPDATE" if not hits else "CANDIDATES_EMITTED","evaluation_changed":False},args.dry_run)
            except Exception as exc:append_jsonl(base/"research/research_receipts.jsonl",{"receipt_id":"RSRCH-"+sid(req.get("request_id"),url,now()),"request_id":req.get("request_id"),"trajectory_ids":req.get("trajectory_ids",[]),"source_scanned":url,"retrieved_at":now(),"result":"FAILED","error":type(exc).__name__,"evaluation_changed":False},args.dry_run)
    print(json.dumps({"repository":REPOSITORY,"requests":len(requests),"sources":len(sources),"candidates":emitted,"dry_run":args.dry_run,"candidate_schema":"stegverse.erl.research_source_candidate.v1","credential_authority":"TV/TVC","github_token_authority":"NONE"},sort_keys=True))
if __name__=="__main__":main()
