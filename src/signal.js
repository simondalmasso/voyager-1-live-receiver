export class SignalView {
  constructor(canvas,onSnapshot){
    this.canvas=canvas;this.ctx=canvas.getContext('2d');this.onSnapshot=onSnapshot;this.mode='synthetic';this.timer=null;this.sequence=0;this.rows=[];this.phase=0;this.eventSource=null;
  }
  start(mode='synthetic') { this.stop(); this.mode=mode; if(mode==='synthetic') this.timer=setInterval(()=>this.synthetic(),160); else if(mode==='live') this.connectLive(); else if(mode==='recorded') this.replayRecorded(); else this.publishNoSource(); }
  stop(){clearInterval(this.timer);this.timer=null;this.eventSource?.close();this.eventSource=null;}
  synthetic(){
    this.sequence++; this.phase+=.11;
    const bins=320,center=160+Math.sin(this.phase*.22)*7,values=[];
    for(let i=0;i<bins;i++){const noise=-78+(Math.sin(i*12.9898+this.sequence*7.233)*43758.5453%1)*8;const peak=38*Math.exp(-((i-center)**2)/3.2);const side=12*Math.exp(-((i-(center+28))**2)/8);values.push(noise+peak+side)}
    const row={values,at:Date.now()};this.rows.unshift(row);this.rows=this.rows.slice(0,110);this.draw();
    const observed=8_420_430_000+(center-160)*.25;
    this.onSnapshot({sourceMode:'SYNTHETIC_TEST',sequence:this.sequence,analysis:{expectedFrequencyHz:8_420_430_000,observedFrequencyHz:observed,driftHzPerSecond:.018+Math.sin(this.phase)*.004,snrDb:15.8+Math.sin(this.phase*.7),confidence:.94,state:'DETECTED',integrationSeconds:120},provenance:{truthClass:'SIMULATED',sourceId:'browser-deterministic-fixture',fetchedAt:new Date().toISOString()}});
  }
  draw(){
    const {ctx,canvas}=this;if(!ctx)return;const w=canvas.width,h=canvas.height;ctx.fillStyle='#020409';ctx.fillRect(0,0,w,h);const rowH=Math.max(2,h/110),binW=w/320;
    this.rows.forEach((row,y)=>row.values.forEach((v,x)=>{const t=Math.max(0,Math.min(1,(v+82)/48));const hue=220-175*t;ctx.fillStyle=`hsl(${hue} ${55+40*t}% ${4+58*t}%)`;ctx.fillRect(x*binW,y*rowH,binW+1,rowH+1)}));
    ctx.strokeStyle='rgba(244,214,147,.65)';ctx.beginPath();ctx.moveTo(w/2,0);ctx.lineTo(w/2,h);ctx.stroke();
  }
  connectLive(){
    const base=localStorage.getItem('listenerUrl')||'http://127.0.0.1:8765';
    try{this.eventSource=new EventSource(`${base}/events`);this.eventSource.onmessage=e=>{const snap=JSON.parse(e.data);this.onSnapshot(snap);if(snap.spectrum?.valuesDb){this.rows.unshift({values:snap.spectrum.valuesDb,at:Date.now()});this.rows=this.rows.slice(0,110);this.draw()}};this.eventSource.onerror=()=>this.onSnapshot({sourceMode:'NO_SOURCE',analysis:{state:'LOST',confidence:0},provenance:{truthClass:'UNAVAILABLE',sourceId:'listener-sse',fetchedAt:new Date().toISOString(),fallbackReason:'No listener heartbeat'}})}catch{this.publishNoSource()}
  }
  async replayRecorded(){
    try{const response=await fetch('/data/fixtures/recorded-authentic-manifest.json');const manifest=await response.json();if(manifest.available!==true)throw new Error(manifest.reason||'No authentic capture bundled');this.onSnapshot(manifest.snapshot)}catch(error){this.onSnapshot({sourceMode:'NO_SOURCE',analysis:{state:'NO_SOURCE',confidence:0},provenance:{truthClass:'UNAVAILABLE',sourceId:'recorded-authentic-manifest',fetchedAt:new Date().toISOString(),fallbackReason:String(error.message||error)}})}
  }
  publishNoSource(){this.rows=[];this.draw();this.onSnapshot({sourceMode:'NO_SOURCE',analysis:{state:'NO_SOURCE',confidence:0},provenance:{truthClass:'UNAVAILABLE',sourceId:'none',fetchedAt:new Date().toISOString()}})}
}
