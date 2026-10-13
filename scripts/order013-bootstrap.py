#!/usr/bin/env python3
import hashlib, json, math, pathlib, struct, urllib.parse, urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/order013'; OUT.mkdir(parents=True,exist_ok=True)
DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
ASSETS=ROOT/'assets'
B_URL='https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/3D%20Models/Voyager%20Probe%20(B)/Voyager%20Probe%20(B).glb'
B_SOURCE='https://science.nasa.gov/3d-resources/voyager-probe-b/'
A_SOURCE='https://science.nasa.gov/3d-resources/voyager-probe-a/'
VTAD_SOURCE='https://science.nasa.gov/resource/voyager-3d-model/'
EPOCH='2026-08-07T21:00:00Z'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'voyager-link-order013/1.0'})
    with urllib.request.urlopen(req,timeout=60) as r: return r.read()

def glb_metrics(path, source, role):
    b=path.read_bytes(); magic,version,total=struct.unpack_from('<4sII',b,0)
    if magic!=b'glTF' or version!=2: raise RuntimeError(f'invalid glb {path}')
    off=12; doc=None
    while off+8<=len(b):
        n,t=struct.unpack_from('<II',b,off); off+=8; chunk=b[off:off+n]; off+=n
        if t==0x4E4F534A: doc=json.loads(chunk.rstrip(b' \t\r\n\x00').decode())
    if doc is None: raise RuntimeError('missing JSON chunk')
    access=doc.get('accessors',[]); tris=0
    for mesh in doc.get('meshes',[]):
        for prim in mesh.get('primitives',[]):
            mode=prim.get('mode',4)
            if mode==4:
                if 'indices' in prim: tris+=access[prim['indices']].get('count',0)//3
                elif 'POSITION' in prim.get('attributes',{}): tris+=access[prim['attributes']['POSITION']].get('count',0)//3
    mins=[math.inf]*3; maxs=[-math.inf]*3
    for a in access:
        if a.get('type')=='VEC3' and 'min' in a and 'max' in a:
            for i in range(3): mins[i]=min(mins[i],a['min'][i]); maxs[i]=max(maxs[i],a['max'][i])
    bounds=None if math.isinf(mins[0]) else {'min':mins,'max':maxs,'size':[maxs[i]-mins[i] for i in range(3)]}
    return {'candidate':role,'file':str(path.relative_to(ROOT)).replace('\\','/'),'source':source,'bytes':len(b),'sha256':sha(path),'nodes':len(doc.get('nodes',[])),'meshes':len(doc.get('meshes',[])),'primitives':sum(len(x.get('primitives',[])) for x in doc.get('meshes',[])),'triangles':tris,'materials':len(doc.get('materials',[])),'textures':len(doc.get('textures',[])),'images':len(doc.get('images',[])),'extensionsUsed':doc.get('extensionsUsed',[]),'extensionsRequired':doc.get('extensionsRequired',[]),'bounds':bounds}

def horizons(command):
    start='2026-08-07 21:00'; stop='2026-08-07 21:02'
    q={'format':'json','COMMAND':f"'{command}'",'EPHEM_TYPE':"'VECTORS'",'CENTER':"'500@10'",'START_TIME':f"'{start}'",'STOP_TIME':f"'{stop}'",'STEP_SIZE':"'1 m'",'REF_PLANE':"'ECLIPTIC'",'REF_SYSTEM':"'J2000'",'OUT_UNITS':"'KM-S'",'CSV_FORMAT':"'YES'",'VEC_TABLE':"'2'"}
    url='https://ssd.jpl.nasa.gov/api/horizons.api?'+urllib.parse.urlencode(q)
    obj=json.loads(fetch(url)); text=obj['result']; block=text.split('$$SOE',1)[1].split('$$EOE',1)[0]
    rows=[r.strip() for r in block.splitlines() if r.strip()]
    vals=[x.strip() for x in rows[0].split(',')]
    nums=[]
    for x in vals:
        try: nums.append(float(x))
        except: pass
    # CSV VECTORS table: JD, calendar, X,Y,Z,VX,VY,VZ ... ; numeric extraction drops calendar.
    if len(nums)<7: raise RuntimeError(f'cannot parse Horizons {command}: {rows[0]}')
    return {'positionKm':nums[1:4],'velocityKmS':nums[4:7],'query':url}

# Official NASA high-detail candidate.
bpath=ASSETS/'voyager-probe-b.glb'; bpath.write_bytes(fetch(B_URL))
a=glb_metrics(ASSETS/'voyager-probe-a.glb',A_SOURCE,'PROBE_A')
b=glb_metrics(bpath,B_SOURCE,'PROBE_B')
# VTAD is retained as a documented controlled candidate; production fetch is intentionally not guessed.
vtad={'candidate':'VTAD','source':VTAD_SOURCE,'availability':'SOURCE_PAGE_VERIFIED_DIRECT_BINARY_NOT_PINNED','selected':False}
score=lambda x:(x['triangles']*3+x['materials']*250+x['textures']*500)/max(1,x['bytes']/1024)
for x in (a,b): x['detailPerKiBScore']=round(score(x),3)
selected='PROBE_B' if (b['triangles']>a['triangles'] or b['materials']>a['materials'] or b['textures']>a['textures']) else 'PROBE_A'
comparison={'schema':'ORDER013_MODEL_COMPARISON_V1','policy':'CONTROLLED_GLTF_STRUCTURE_DETAIL_VS_BYTES','selectedHeroHigh':selected,'heroLow':'PROBE_A','proceduralFallback':'EMERGENCY_ONLY_TRUTH_LABELED','candidates':[a,b,vtad]}
(OUT/'model-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
(ASSETS/'voyager-probe-b.provenance.json').write_text(json.dumps({'sourceUrl':B_URL,'sourcePage':B_SOURCE,'agency':'NASA','credit':'Michael D. Carbajal','sourceSha256':b['sha256'],'productionSha256':b['sha256'],'role':'HERO_HIGH_CANDIDATE'},indent=2)+'\n')

ids={'Mercury':'199','Venus':'299','Earth':'399','Mars':'499','Jupiter':'599','Saturn':'699','Uranus':'799','Neptune':'899','Voyager 1':'-31'}
bodies={'Sun':{'positionKm':[0,0,0],'velocityKmS':[0,0,0],'source':'CENTER_500@10'}}
for name,cid in ids.items(): bodies[name]=horizons(cid)
eph={'schema':'ORDER013_EPHEMERIS_V1','epoch':EPOCH,'frame':'ECLIPJ2000','center':'SUN','units':'KM-S','truthClass':'DERIVED_GEOMETRY','source':'JPL_HORIZONS','orbitCurvesTruth':'ORBIT_APPROXIMATION','displayRadiusTruth':'DISPLAY_RADIUS_EXAGGERATED','bodies':bodies}
(DATA/'order013-ephemeris.json').write_text(json.dumps(eph,indent=2)+'\n')
print(json.dumps({'selected':selected,'probeA':a,'probeB':b,'epoch':EPOCH,'bodies':list(bodies)},indent=2))
