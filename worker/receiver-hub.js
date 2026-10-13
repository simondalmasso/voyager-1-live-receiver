const JSON_HEADERS={'content-type':'application/json; charset=utf-8','cache-control':'no-store'};
function json(value,status=200){return new Response(JSON.stringify(value),{status,headers:JSON_HEADERS})}
function noSource(reason='No verified receiver product has been accepted.'){return {schemaVersion:1,sourceMode:'NO_SOURCE',analysis:{state:'NO_SOURCE',confidence:0},spectrum:{valuesDb:[]},provenance:{truthClass:'UNAVAILABLE',sourceId:'verified-receiver-hub',fetchedAt:new Date().toISOString(),fallbackReason:reason},generatedAt:new Date().toISOString()}}
function lost(last,reason='Verified receiver heartbeat expired.'){return {schemaVersion:1,sourceMode:'LOST',analysis:{...(last?.analysis||{}),state:'LOST',confidence:0},spectrum:{valuesDb:[]},provenance:{truthClass:'LOST',sourceId:'verified-receiver-hub',fetchedAt:new Date().toISOString(),fallbackReason:reason},generatedAt:new Date().toISOString()}}
export class ReceiverHub {
  constructor(ctx,env){
    this.ctx=ctx;this.env=env;this.sql=ctx.storage.sql;
    this.sql.exec('CREATE TABLE IF NOT EXISTS station_seq (station_id TEXT PRIMARY KEY, sequence INTEGER NOT NULL, updated_at INTEGER NOT NULL)');
    this.sql.exec('CREATE TABLE IF NOT EXISTS nonces (station_id TEXT NOT NULL, nonce TEXT NOT NULL, seen_at INTEGER NOT NULL, PRIMARY KEY(station_id, nonce))');
    this.sql.exec('CREATE TABLE IF NOT EXISTS latest (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, station_id TEXT NOT NULL, sequence INTEGER NOT NULL, accepted_at INTEGER NOT NULL, expires_at INTEGER NOT NULL)');
  }
  current(){
    const row=this.sql.exec('SELECT payload, expires_at FROM latest WHERE id=1').toArray()[0];
    if(!row)return noSource();
    let payload;try{payload=JSON.parse(row.payload)}catch{return noSource('Stored receiver product is unreadable.')}
    if(Number(row.expires_at)<=Date.now())return lost(payload);
    return payload;
  }
  ingest(envelope){
    const now=Date.now(),stationId=String(envelope.stationId||''),sequence=Number(envelope.sequence),nonce=String(envelope.nonce||'');
    if(!stationId||!Number.isSafeInteger(sequence)||sequence<1||nonce.length<12)return {ok:false,status:400,code:'CONTRACT_INVALID'};
    try{
      const accepted=this.ctx.storage.transactionSync(()=>{
        const prior=this.sql.exec('SELECT sequence FROM station_seq WHERE station_id=?',stationId).toArray()[0];
        if(prior&&sequence<=Number(prior.sequence))throw new Error('REPLAY_SEQUENCE');
        if(this.sql.exec('SELECT nonce FROM nonces WHERE station_id=? AND nonce=?',stationId,nonce).toArray().length)throw new Error('REPLAY_NONCE');
        this.sql.exec('INSERT INTO nonces(station_id,nonce,seen_at) VALUES(?,?,?)',stationId,nonce,now);
        this.sql.exec('INSERT INTO station_seq(station_id,sequence,updated_at) VALUES(?,?,?) ON CONFLICT(station_id) DO UPDATE SET sequence=excluded.sequence, updated_at=excluded.updated_at',stationId,sequence,now);
        const payload={...envelope.snapshot,relay:{stationId,stationName:envelope.stationName||stationId,sequence,softwareSha:envelope.softwareSha,verifiedAt:envelope.verifiedAt||new Date(now).toISOString()}};
        this.sql.exec('INSERT INTO latest(id,payload,station_id,sequence,accepted_at,expires_at) VALUES(1,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,station_id=excluded.station_id,sequence=excluded.sequence,accepted_at=excluded.accepted_at,expires_at=excluded.expires_at',JSON.stringify(payload),stationId,sequence,now,now+30000);
        this.sql.exec('DELETE FROM nonces WHERE seen_at < ?',now-600000);
        return payload;
      });
      for(const ws of this.ctx.getWebSockets()){try{ws.send(JSON.stringify(accepted))}catch{}}
      return {ok:true,status:202,payload:accepted};
    }catch(error){const code=String(error?.message||error);return {ok:false,status:code.startsWith('REPLAY_')?409:400,code}}
  }
  async fetch(request){
    const url=new URL(request.url);
    if(request.method==='GET'&&url.pathname==='/snapshot')return json(this.current());
    if(request.method==='POST'&&url.pathname==='/ingest'){
      const text=await request.text();if(text.length>270000)return json({accepted:false,error:'PAYLOAD_TOO_LARGE'},413);
      let body;try{body=JSON.parse(text)}catch{return json({accepted:false,error:'INVALID_JSON'},400)}
      const result=this.ingest(body);return result.ok?json({schemaVersion:1,accepted:true,expiresInSeconds:30,stationId:body.stationId,sequence:body.sequence},202):json({schemaVersion:1,accepted:false,error:result.code},result.status);
    }
    if(request.method==='GET'&&url.pathname==='/live'){
      if((request.headers.get('Upgrade')||'').toLowerCase()!=='websocket')return json({error:'WEBSOCKET_REQUIRED'},426);
      const pair=new WebSocketPair(),[client,server]=Object.values(pair);this.ctx.acceptWebSocket(server);server.serializeAttachment({connectedAt:Date.now()});server.send(JSON.stringify(this.current()));return new Response(null,{status:101,webSocket:client});
    }
    return json({error:'NOT_FOUND'},404);
  }
  webSocketMessage(ws,message){if(message==='ping')ws.send('pong')}
  webSocketClose(ws,code,reason){try{ws.close(code,reason)}catch{}}
  webSocketError(ws){try{ws.close(1011,'receiver hub error')}catch{}}
}
export {noSource,lost};
