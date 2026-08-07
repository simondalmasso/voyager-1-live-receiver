from __future__ import annotations
import hashlib,json,re,zipfile
from pathlib import Path
from typing import Any
FIXED=(2026,1,1,0,0,0)
SECRET_RE=re.compile(r"(sk-[A-Za-z0-9_-]{20,}|CLOUDFLARE_API_TOKEN\s*[:=]\s*[^\s]+|BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY)")

def canonical_json(value:Any)->bytes:return (json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def _payload(files:dict[str,Any])->dict[str,bytes]:
    payload:dict[str,bytes]={}
    for name,value in files.items():
        if name.startswith("/") or ".." in Path(name).parts:raise ValueError("unsafe evidence path")
        data=value if isinstance(value,bytes) else canonical_json(value)
        if SECRET_RE.search(data.decode("utf-8","ignore")):raise ValueError(f"secret-like material in {name}")
        payload[name]=data
    return payload
def build_manifest(files:dict[str,Any],observation_id:str,truth_class:str,software:dict|None=None)->dict:
    if not observation_id or ".." in observation_id:raise ValueError("invalid observation id")
    payload=_payload(files)
    manifest={"schemaVersion":1,"observationId":observation_id,"truthClass":truth_class,"signatureStatus":"UNSIGNED_HASH_VERIFIED","software":software or {},"files":{name:{"sha256":sha(data),"bytes":len(data)} for name,data in sorted(payload.items())}}
    return {"manifest":manifest,"manifestSha256":sha(canonical_json(manifest)),"payload":payload}
def create_bundle(path:str|Path,files:dict[str,Any],observation_id:str,truth_class:str,software:dict|None=None)->dict:
    built=build_manifest(files,observation_id,truth_class,software);manifest=built["manifest"];payload=dict(built["payload"]);payload["manifest.json"]=canonical_json(manifest);out=Path(path);out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(payload.items()):
            info=zipfile.ZipInfo(name,FIXED);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,data)
    return {"path":str(out),"sha256":sha(out.read_bytes()),"manifest":manifest,"manifestSha256":built["manifestSha256"],"bytes":out.stat().st_size}
def verify_bundle(path:str|Path)->dict:
    raw=Path(path).read_bytes()
    with zipfile.ZipFile(path,"r") as z:
        manifest=json.loads(z.read("manifest.json"));bad=[]
        for name,meta in manifest["files"].items():
            try:data=z.read(name)
            except KeyError:bad.append(name);continue
            if sha(data)!=meta["sha256"]:bad.append(name)
        extras=set(z.namelist())-set(manifest["files"])-{"manifest.json"}
    return {"valid":not bad and not extras,"tampered":bool(bad or extras),"badFiles":bad,"unexpectedFiles":sorted(extras),"bundleSha256":sha(raw),"manifest":manifest,"manifestSha256":sha(canonical_json(manifest))}
