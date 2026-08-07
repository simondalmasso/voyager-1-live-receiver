import {publicNoSource,validateBrowserSnapshot} from '/contracts.js';
export class SignalView{
  constructor(canvas,onSnapshot){this.canvas=canvas;this.ctx=canvas.getContext('2d');this.onSnapshot=onSnapshot;this.mode='none';this.timer=null;this.sequence=0;this.rows=[];this.phase=0;this.socket=null;this.pollTimer=null;this.publish(publicNoSource('NO VERIFIED LIVE SOURCE'));}
  start(mode='none'){this.stop();this.mode=mode;if(mode==='synthetic')this.startSynthetic();else if(mode==='live')this.connectLive();else if(mode==='recorded')this.replayRecorded();else this.publishNoSource();}
  stop(){clearInterval(this.timer);clearInterval(this.pollTimer);this.timer=null;this.pollTimer=null;if(this.socket){this.socket.close();this.socket=null;}}
  publish(snapshot){this.onSnapshot(validateBrowserSnapshot(snapshot));}
  startSynthetic(){this.synthetic();this.timer=setInterval(()=>this.synthetic(),180);}
  synthetic(){
    this.sequence++;this.phase+=.11;const bins=320,center=160+Math.sin(this.phase*.22)*7,values=[];
    for(let index=0;index<bins;index++){const pseudo=Math.sin(index*12.9898+this.sequence*7.233)*43758.5453;const noise=-78+(pseudo-Math.floor(pseudo))*8;const peak=38*Math.exp(-((index-center)**2)/3.2);values.push(noise+peak);}
    this.rows.unshift({values,at:Date.now()});this.rows=this.rows.slice(0,110);this.draw();
    this.publish({schemaVersion:2,truthState:'SYNTHETIC_TEST',stationId:'browser-fixture',streamId:'explicit-synthetic-demo',sequence:this.sequence,observedAt:new Date().toISOString(),receivedAt:new Date().toISOString(),ageSeconds:0,spectrum:{encoding:'float32-db-json',valuesDb:values,binWidthHz:.25,firstBinFrequencyHz:8_420_429_960},spectrumSha256:'not-applicable-synthetic',signature:{algorithm:'none',keyId:'none',verified:false},software:{version:'browser-fixture',commitSha:'not-applicable'},prediction:{modelId:'synthetic-sine',sha256:'not-applicable',expectedFrequencyHz:8_420_430_000},analysis:{observedFrequencyHz:8_420_430_000+(center-160)*.25,snrDb:15.8,confidence:.94,state:'CANDIDATE',residualHz:(center-160)*.25},offTargetComparison:{performed:true,onTargetSnrDb:15.8,offTargetSnrDb:0,stationaryRfiRejected:true},degradationReason:'Explicit deterministic demonstration; never telescope live.'});
  }
  connectLive(){
    this.publishNoSource('Connecting to verified ReceiverHub');
    const protocol=location.protocol==='https:'?'wss:':'ws:',url=`${protocol}//${location.host}/api/v1/receiver/ws`;
    try{
      this.socket=new WebSocket(url);
      this.socket.onmessage=event=>this.acceptRemote(event.data);
      this.socket.onerror=()=>this.startPolling();
      this.socket.onclose=()=>this.startPolling();
    }catch{this.startPolling();}
  }
  startPolling(){if(this.pollTimer)return;this.poll();this.pollTimer=setInterval(()=>this.poll(),5000);}
  async poll(){try{const response=await fetch('/api/v1/receiver/live',{cache:'no-store'});if(!response.ok)throw new Error(`HTTP ${response.status}`);this.acceptRemote(await response.text());}catch(error){this.publishNoSource(`ReceiverHub unavailable: ${String(error.message||error)}`);}}
  acceptRemote(raw){
    try{const snapshot=validateBrowserSnapshot(JSON.parse(raw));this.publish(snapshot);if(snapshot.truthState==='TELESCOPE_LIVE_VERIFIED'&&snapshot.spectrum?.valuesDb){this.rows.unshift({values:snapshot.spectrum.valuesDb,at:Date.now()});this.rows=this.rows.slice(0,110);this.draw();}}
    catch(error){this.publish({schemaVersion:2,truthState:'UNVERIFIED_SOURCE',receivedAt:new Date().toISOString(),degradationReason:`Browser rejected receiver payload: ${String(error.message||error)}`});}
  }
  async replayRecorded(){
    try{const response=await fetch('/data/fixtures/recorded-authentic-manifest.json',{cache:'no-store'});const manifest=await response.json();if(manifest.available!==true||manifest.snapshot?.truthState!=='RECORDED_AUTHENTIC_VERIFIED')throw new Error(manifest.reason||'No verified authentic capture bundled');this.publish(manifest.snapshot);}
    catch(error){this.publishNoSource(String(error.message||error));}
  }
  publishNoSource(reason='NO VERIFIED LIVE SOURCE'){this.rows=[];this.draw();this.publish(publicNoSource(reason));}
  draw(){const {ctx,canvas}=this;if(!ctx)return;const width=canvas.width,height=canvas.height;ctx.fillStyle='#020409';ctx.fillRect(0,0,width,height);const rowHeight=Math.max(2,height/110),bins=this.rows[0]?.values.length||320,binWidth=width/bins;this.rows.forEach((row,y)=>row.values.forEach((value,x)=>{const t=Math.max(0,Math.min(1,(value+82)/48)),hue=220-175*t;ctx.fillStyle=`hsl(${hue} ${55+40*t}% ${4+58*t}%)`;ctx.fillRect(x*binWidth,y*rowHeight,binWidth+1,rowHeight+1);}));ctx.strokeStyle='rgba(244,214,147,.65)';ctx.beginPath();ctx.moveTo(width/2,0);ctx.lineTo(width/2,height);ctx.stroke();}
}
