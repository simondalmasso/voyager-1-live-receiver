function csvRows(text){
  const source=String(text||'').replace(/^\uFEFF/,'');
  const rows=[];let row=[],cell='',quoted=false;
  for(let i=0;i<source.length;i++){
    const ch=source[i];
    if(quoted){if(ch==='"'){if(source[i+1]==='"'){cell+='"';i++}else quoted=false}else cell+=ch;continue}
    if(ch==='"'&&cell.length===0){quoted=true;continue}
    if(ch===','){row.push(cell);cell='';continue}
    if(ch==='\r'||ch==='\n'){row.push(cell);cell='';if(row.some(v=>String(v).trim()!==''))rows.push(row);row=[];if(ch==='\r'&&source[i+1]==='\n')i++;continue}
    cell+=ch;
  }
  if(quoted)throw new Error('CSV_QUOTE_UNCLOSED');
  if(cell.length||row.length){row.push(cell);if(row.some(v=>String(v).trim()!==''))rows.push(row)}
  return rows;
}
function numericCell(value){const s=String(value??'').trim();if(!s||!/^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/.test(s))return null;const n=Number(s);return Number.isFinite(n)?n:null}
function median(values){const s=[...values].sort((a,b)=>a-b),m=Math.floor(s.length/2);return s.length?(s.length%2?s[m]:(s[m-1]+s[m])/2):null}
export function analyzePwsCsv(text){
  const parsed=csvRows(text);
  if(parsed.length<2)throw new Error('CSV_NEEDS_HEADER_AND_DATA_ROWS');
  if(parsed.length>500001)throw new Error('CSV_TOO_MANY_ROWS');
  const columns=parsed[0].map((v,i)=>String(v).trim()||('column_'+(i+1)));
  const rows=parsed.slice(1).filter(r=>r.some(v=>String(v).trim()!=='')).map(r=>columns.map((_,i)=>String(r[i]??'').trim()));
  if(!rows.length)throw new Error('CSV_NO_DATA_ROWS');
  const headerText=columns.join(' ').toLowerCase();
  const inventory=/(lidvid|file_ref|product_id|logical_identifier|collection_member|file_name)/.test(headerText)&&!/(density|frequency|electron|spectral|wave)/.test(headerText);
  const timeIndex=columns.findIndex(c=>/(time|date|epoch|scet|utc|timestamp|datetime)/i.test(c));
  let timeRange=null;
  if(timeIndex>=0){
    const times=rows.map(r=>Date.parse(r[timeIndex])).filter(Number.isFinite).sort((a,b)=>a-b);
    if(times.length)timeRange={start:new Date(times[0]).toISOString(),end:new Date(times[times.length-1]).toISOString(),validRows:times.length};
  }
  const numericSummaries=[];
  for(let i=0;i<columns.length;i++){
    if(numericSummaries.length>=8)break;
    if(i===timeIndex||/(time|date|epoch|scet|utc|timestamp|datetime)/i.test(columns[i]))continue;
    const values=rows.map(r=>numericCell(r[i])).filter(v=>v!==null);
    if(!values.length)continue;
    const sum=values.reduce((a,b)=>a+b,0);
    numericSummaries.push({name:columns[i],count:values.length,min:values.reduce((a,b)=>Math.min(a,b),Infinity),median:median(values),max:values.reduce((a,b)=>Math.max(a,b),-Infinity),mean:sum/values.length});
  }
  return {classification:inventory?'PDS_COLLECTION_INVENTORY':'MEASUREMENT_TABLE',rowCount:rows.length,columns,timeRange,numericSummaries,fillValuesMasked:false};
}
function fmtTime(value){if(!value)return'not supplied by source';const d=new Date(value);return Number.isFinite(d.getTime())?d.toLocaleString():String(value)}
function fmtNum(value){if(value===null||value===undefined||value===''||!Number.isFinite(Number(value)))return'—';return Number(value).toLocaleString(undefined,{maximumSignificantDigits:7})}
function setText(root,id,value){const el=root.querySelector('#'+id);if(el)el.textContent=String(value??'Unavailable')}
async function getJson(path){const r=await fetch(path,{cache:'no-store',headers:{accept:'application/json'}});if(!r.ok)throw new Error('HTTP_'+r.status);return r.json()}

const PANEL=[
'<section id="os-voyager-panel" class="osv-panel" hidden aria-labelledby="osv-title">',
' <header class="osv-header"><div><p class="eyebrow">MISSION SYSTEMS · READ-ONLY</p><h2 id="osv-title">OS VOYAGER</h2></div><button id="osv-close" type="button" aria-label="Close OS Voyager">×</button></header>',
' <p class="osv-boundary"><strong>TRUTH BOUNDARY</strong> Public DSN status and JPL geometry are not spacecraft telemetry. This console cannot send commands.</p>',
' <div class="osv-grid">',
'  <article class="osv-card"><div class="osv-card-head"><small>PUBLIC LIVE STATUS · 5 S POLL</small><span id="osv-dsn-truth" class="osv-tag">CHECKING</span></div><h3>NASA/JPL DSN Now</h3><strong id="osv-dsn-state">Checking public feed…</strong><p id="osv-dsn-detail">No result yet.</p><p class="osv-meta" id="osv-dsn-time">Source time unavailable.</p><a href="https://eyes.nasa.gov/apps/dsn-now/dsn.html" target="_blank" rel="noopener noreferrer">Open NASA DSN Now</a></article>',
'  <article class="osv-card"><div class="osv-card-head"><small>DERIVED GEOMETRY</small><span id="osv-geometry-truth" class="osv-tag">CHECKING</span></div><h3>JPL Horizons</h3><strong id="osv-geometry-state">Loading geometric state…</strong><p id="osv-geometry-detail">Distance and one-way light time are geometric calculations, not telemetry.</p><p class="osv-meta" id="osv-geometry-time">Epoch unavailable.</p></article>',
'  <article class="osv-card"><div class="osv-card-head"><small>PHYSICAL RECEIVE-ONLY STATION</small><span id="osv-receiver-truth" class="osv-tag">CHECKING</span></div><h3>Receiver pipeline</h3><strong id="osv-receiver-state">NO_SOURCE</strong><p id="osv-receiver-detail">No verified station product accepted.</p><p class="osv-meta" id="osv-receiver-time">No verified receiver timestamp.</p></article>',
'  <article class="osv-card"><div class="osv-card-head"><small>OFFICIAL PUBLISHED SNAPSHOT</small><span id="osv-mission-truth" class="osv-tag">NOT LIVE</span></div><h3>Mission & instruments</h3><strong id="osv-mission-state">NASA snapshot</strong><p id="osv-mission-detail">Instrument states are published snapshots, not live telemetry.</p><p class="osv-meta" id="osv-mission-time">Source update date unavailable.</p><a href="https://science.nasa.gov/mission/voyager/where-are-voyager-1-and-voyager-2-now/" target="_blank" rel="noopener noreferrer">Open NASA mission status</a></article>',
'  <article class="osv-card osv-wide" id="osv-pws-archive"><div class="osv-card-head"><small>PWS ARCHIVED SCIENCE · NOT LIVE</small><span id="osv-pws-truth" class="osv-tag">PWS_ARCHIVED_SCIENCE</span></div><h3>Plasma Wave Science archive</h3><p>The PDS VLISM electron-density bundle is derived science data. Bundle metadata covers 2012-10-22 through 2025-09-01; the linked data-collection page lists a different stop date, 2025-04-14. This metadata discrepancy is retained rather than silently reconciled.</p><p id="osv-pws-source">Checking the catalog adapter…</p><div class="osv-links"><a href="https://pds.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=urn%3Anasa%3Apds%3Avoyager-pws-vlism-density" target="_blank" rel="noopener noreferrer">Open PDS bundle</a><a href="https://pds.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=urn%3Anasa%3Apds%3Avoyager-pws-vlism-density%3Adata" target="_blank" rel="noopener noreferrer">Open PDS data collection</a></div><label class="osv-file-label" for="osv-pws-file">Analyze a downloaded PDS measurement CSV (local browser only)</label><input id="osv-pws-file" type="file" accept=".csv,text/csv"><p class="osv-meta">Choose a measurement-product CSV, not collection_data.csv inventory metadata. Files up to 20 MB are processed locally; nothing is uploaded. Numeric summaries include parseable values without fill-value masking.</p><pre id="osv-pws-analysis" class="osv-output" aria-live="polite">No local CSV loaded.</pre></article>',
'  <article class="osv-card osv-wide"><div class="osv-card-head"><small>SIMULATED OPERATIONS</small><span class="osv-tag">NO RF</span></div><h3>Diagnostic rehearsal</h3><p>This runs a local checklist against a selected scenario. It does not diagnose the spacecraft or construct command frames.</p><label class="osv-file-label" for="osv-scenario">Scenario</label><select id="osv-scenario"><option value="NO_SOURCE">No verified receiver source</option><option value="DSN_MISMATCH">Public DSN and local receiver disagree</option><option value="PWS_ARCHIVE">Review archived PWS science</option><option value="IMAGING_REVIEW">Review imaging-system recovery feasibility</option></select><button id="osv-sim-run" type="button">Run simulated diagnostics</button><pre id="osv-sim-result" class="osv-output" aria-live="polite">Simulation not run. No commands are queued.</pre></article>',
'  <article class="osv-card osv-wide osv-uplink"><div class="osv-card-head"><small>FUTURE INTEGRATION GATE</small><span class="osv-tag">BLOCKED</span></div><h3>Real uplink</h3><strong id="osv-uplink-state">DISABLED — NO AUTHORIZED CHANNEL</strong><p>No command transport, frame builder, DSN control endpoint, or spacecraft mutation path is implemented. Future work requires documented NASA/JPL/operator authorization, an official interface, a test environment, security review, dual approval and immutable audit logs.</p></article>',
' </div><footer class="osv-footer"><span id="osv-health">Worker status: checking…</span><span id="osv-last-poll">UI poll not yet completed.</span></footer>',
'</section>'
].join('\n');

const SCENARIOS={
  NO_SOURCE:['INPUT: receiver hub reports no accepted physical station product.','CHECK: verify local capture, station clock, frequency/band metadata, signature, nonce and sequence continuity.','INTERPRETATION: NO_SOURCE is a local pipeline state; it is not evidence that Voyager 1 has failed.','RESULT: diagnostic checklist only; no command frames created; NO RF TRANSMITTED.'],
  DSN_MISMATCH:['INPUT: public DSN status and local receive-only station disagree.','CHECK: compare timestamps, antenna/dish identifiers, downSignal/upSignal direction and station provenance.','INTERPRETATION: DSN Now can misidentify a spacecraft in off-nominal conditions; independent RF evidence is required.','RESULT: discrepancy report only; no command frames created; NO RF TRANSMITTED.'],
  PWS_ARCHIVE:['INPUT: PWS VLISM density archive selected.','CHECK: preserve product label, observation-time coverage, units, fill-value policy and source hashes.','INTERPRETATION: archived derived density is not current X-band downlink telemetry.','RESULT: archive review only; no command frames created; NO RF TRANSMITTED.'],
  IMAGING_REVIEW:['INPUT: imaging-system recovery feasibility selected.','CHECK: consult NASA-published instrument status, power constraints, engineering telemetry and mission-team assessment.','CONTEXT: NASA says the cameras were turned off in 1990, the camera-control software was removed, and the original ground computers no longer exist; reactivation feasibility is uncertain.','RESULT: evidence checklist only; no command frames created; NO RF TRANSMITTED.']
};

export function mountOsVoyager({onClose}={}){
  document.body.insertAdjacentHTML('beforeend',PANEL);
  const panel=document.getElementById('os-voyager-panel'),timers=[];
  let visible=false;
  function renderDsn(d){
    const p=d?.provenance||{};
    setText(panel,'osv-dsn-truth',p.truthClass||'UNAVAILABLE');
    if(!d||p.truthClass==='UNAVAILABLE'&&!d.feedAvailable){setText(panel,'osv-dsn-state','DSN NOW FEED UNAVAILABLE');setText(panel,'osv-dsn-detail',p.fallbackReason||'The public feed could not be read. No live status is asserted.')}
    else if(!d.available){setText(panel,'osv-dsn-state','NO EXPLICIT VOYAGER 1 TARGET IN SNAPSHOT');setText(panel,'osv-dsn-detail','The feed snapshot contains no explicit Voyager 1 target match. This is not proof of no contact.')}
    else{
      const stations=Array.isArray(d.stations)?d.stations:[],down=stations.filter(s=>s.downlinkActive),up=stations.filter(s=>s.uplinkActive);
      const label=down.length&&up.length?'DSN REPORTS ACTIVE UPLINK + DOWNLINK':down.length?'DSN REPORTS ACTIVE DOWNLINK':up.length?'DSN REPORTS ACTIVE UPLINK':'VOYAGER 1 TARGET LISTED · DIRECTION UNCONFIRMED';
      setText(panel,'osv-dsn-state',label);
      setText(panel,'osv-dsn-detail',stations.map(s=>[s.dish,s.complex,s.band?(s.band+' band'):null,s.downlinkActive?'downlink active':null,s.uplinkActive?'uplink active':null,s.dataRate?'rate field '+s.dataRate:null].filter(Boolean).join(' · ')).join(' | ')||'No dish details returned.');
    }
    setText(panel,'osv-dsn-time','Fetched: '+fmtTime(p.fetchedAt)+' · source timestamp: '+(d?.sourceTimestamp||'not supplied'));
  }
  function renderGeometry(s){
    const p=s?.provenance||{},truth=p.truthClass||'UNAVAILABLE';
    setText(panel,'osv-geometry-truth',truth);
    if(!s||!Number.isFinite(Number(s.distanceKm))){setText(panel,'osv-geometry-state',truth==='STALE'?'STALE GEOMETRY':'GEOMETRY UNAVAILABLE');setText(panel,'osv-geometry-detail',p.fallbackReason||'No usable JPL Horizons vector.')}
    else{setText(panel,'osv-geometry-state',fmtNum(s.distanceKm)+' km from Earth');setText(panel,'osv-geometry-detail','One-way light time: '+fmtNum(s.oneWayLightTimeSeconds)+' s · radial rate: '+fmtNum(s.rangeRateKmS)+' km/s. Derived geometry only.')}
    setText(panel,'osv-geometry-time','Epoch: '+fmtTime(s?.observedAt||p.fetchedAt)+' · source: '+(p.sourceId||'not supplied'));
  }
  function renderReceiver(s){
    const mode=s?.sourceMode||'NO_SOURCE',p=s?.provenance||{},relay=s?.relay||{};
    setText(panel,'osv-receiver-truth',p.truthClass||'UNAVAILABLE');setText(panel,'osv-receiver-state',mode);
    setText(panel,'osv-receiver-detail',mode==='TELESCOPE_LIVE_VERIFIED'?'Registered station product passed the receiver transport/provenance gates; spacecraft attribution still requires independent signal evidence.':p.fallbackReason||'No verified physical receiver product is currently accepted.');
    setText(panel,'osv-receiver-time','Station: '+(relay.stationName||relay.stationId||'none')+' · verified: '+fmtTime(relay.verifiedAt||p.fetchedAt));
  }
  function renderMission(m){
    const p=m?.provenance||{},items=Array.isArray(m?.instruments)?m.instruments:[];
    setText(panel,'osv-mission-truth',p.truthClass||'MISSION_STATUS_OFFICIAL_SNAPSHOT');setText(panel,'osv-mission-state',items.length+' published instrument records');
    setText(panel,'osv-mission-detail',items.map(i=>i.id+': '+i.state+(i.effectiveAt?' since '+i.effectiveAt:'')).join(' · ')||'Official instrument snapshot unavailable.');
    setText(panel,'osv-mission-time','NASA source updated: '+(m?.sourceUpdatedAt||'not supplied')+' · snapshot fetched: '+fmtTime(p.fetchedAt)+' · NOT LIVE TELEMETRY');
  }
  function renderScience(c){
    const p=c?.provenance||{};setText(panel,'osv-pws-truth',p.truthClass||'PWS_ARCHIVED_SCIENCE');
    setText(panel,'osv-pws-source',c&&Array.isArray(c.products)&&c.products.length?'Catalog adapter returned '+c.products.length+' products. Verify each product label and observation coverage.':'Worker catalog adapter does not ingest PWS measurement rows; use the linked NASA PDS collection and analyze a downloaded product CSV locally.');
  }
  async function refreshOne(path,render){
    try{render(await getJson(path))}
    catch(e){render({sourceMode:'NO_SOURCE',available:false,feedAvailable:false,analysis:{state:'NO_SOURCE',confidence:0},provenance:{truthClass:'UNAVAILABLE',sourceId:path,fetchedAt:new Date().toISOString(),fallbackReason:String(e?.message||e)}})}
  }
  async function refreshFast(){await Promise.allSettled([refreshOne('/api/v1/dsn/voyager-1',renderDsn),refreshOne('/api/v1/receiver/snapshot',renderReceiver)])}
  async function refreshSlow(){await Promise.allSettled([refreshOne('/api/v1/voyager/state',renderGeometry),refreshOne('/api/v1/mission/status',renderMission),refreshOne('/api/v1/science/pws/catalog',renderScience),refreshOne('/api/v1/health',h=>setText(panel,'osv-health','Worker: '+(h.status||'unavailable')+' · build '+String(h.buildSha||'unreported').slice(0,12)+' · DSN '+(h.dsn||'unknown')))])}
  function refreshAll(){setText(panel,'osv-last-poll','UI poll: '+new Date().toLocaleString());return Promise.allSettled([refreshFast(),refreshSlow()])}
  function runSimulation(){const scenario=panel.querySelector('#osv-scenario').value;setText(panel,'osv-sim-result',(SCENARIOS[scenario]||SCENARIOS.NO_SOURCE).join('\n'))}
  async function analyzeFile(file){
    const out=panel.querySelector('#osv-pws-analysis');
    if(!file){out.textContent='No local CSV loaded.';return}
    if(file.size>20_000_000){out.textContent='Rejected: file exceeds the 20 MB local analysis limit.';return}
    out.textContent='Reading file locally…';
    try{
      const result=analyzePwsCsv(await file.text());
      const lines=['CLASSIFICATION: '+result.classification,'ROWS: '+result.rowCount,'COLUMNS: '+result.columns.join(' | '),'TIME RANGE: '+(result.timeRange?result.timeRange.start+' — '+result.timeRange.end+' ('+result.timeRange.validRows+' parseable timestamps)':'No parseable timestamp column detected.'),'FILL VALUES MASKED: NO'];
      if(result.classification==='PDS_COLLECTION_INVENTORY')lines.push('This looks like collection inventory metadata, not measurement rows. Select an actual science-product CSV from the PDS collection.');
      lines.push('NUMERIC SUMMARIES (descriptive only):');
      for(const s of result.numericSummaries)lines.push(s.name+': n='+s.count+', min='+fmtNum(s.min)+', median='+fmtNum(s.median)+', max='+fmtNum(s.max)+', mean='+fmtNum(s.mean));
      lines.push('Processed in this browser only; no file was uploaded.');
      out.textContent=lines.join('\n');
    }catch(e){out.textContent='CSV analysis failed: '+String(e?.message||e)}
  }
  function show(){visible=true;panel.hidden=false;refreshAll();if(!timers.length){timers.push(setInterval(refreshFast,5000),setInterval(refreshSlow,60000))}}
  function hide(){visible=false;panel.hidden=true;while(timers.length)clearInterval(timers.pop())}
  panel.querySelector('#osv-close').addEventListener('click',()=>{hide();if(onClose)onClose()});
  panel.querySelector('#osv-sim-run').addEventListener('click',runSimulation);
  panel.querySelector('#osv-pws-file').addEventListener('change',e=>analyzeFile(e.currentTarget.files?.[0]));
  document.addEventListener('visibilitychange',()=>{if(!visible)return;if(document.hidden){while(timers.length)clearInterval(timers.pop())}else if(!timers.length){timers.push(setInterval(refreshFast,5000),setInterval(refreshSlow,60000));refreshAll()}});
  return {show,hide,destroy(){hide();panel.remove()}};
}
