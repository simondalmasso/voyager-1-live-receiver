export const ALBUM = Object.freeze({
  videoId:'kr9-QrMhfzY',
  defaultTrack:3,
  defaultTrackTitle:'Microscopic',
  startSeconds:1036,
  timingBasis:'Indexed YouTube full-album chapter metadata for Gas 0095: Microscopic 17:16; target video metadata is revalidated at runtime when player is available.',
  targetUrl:'https://youtu.be/kr9-QrMhfzY'
});

export class AlbumPlayer {
  constructor({mount,status,play,mute}){this.mount=mount;this.status=status;this.playButton=play;this.muteButton=mute;this.player=null;this.playing=false;this.muted=false;this.started=false;this.bind()}
  bind(){this.playButton?.addEventListener('click',()=>this.togglePlay());this.muteButton?.addEventListener('click',()=>this.toggleMute())}
  init(){if(!this.mount)return;const ready=()=>this.create();if(globalThis.YT?.Player)return ready();const prior=globalThis.onYouTubeIframeAPIReady;globalThis.onYouTubeIframeAPIReady=()=>{prior?.();ready()};if(!document.querySelector('script[data-youtube-api]')){const script=document.createElement('script');script.src='https://www.youtube.com/iframe_api';script.async=true;script.dataset.youtubeApi='1';script.referrerPolicy='no-referrer';script.onerror=()=>this.setStatus('MUSIC UNAVAILABLE');document.head.append(script)}setTimeout(()=>{if(!this.player)this.setStatus('MUSIC READY ON TAP')},5000)}
  create(){if(this.player||!globalThis.YT?.Player)return;this.player=new globalThis.YT.Player(this.mount,{width:'1',height:'1',videoId:ALBUM.videoId,playerVars:{autoplay:1,controls:0,disablekb:1,playsinline:1,rel:0,start:ALBUM.startSeconds,origin:location.origin},events:{onReady:event=>{event.target.seekTo(ALBUM.startSeconds,true);event.target.playVideo();this.started=true;this.setStatus(`TRACK 3 · ${ALBUM.defaultTrackTitle.toUpperCase()}`)},onStateChange:event=>{this.playing=event.data===globalThis.YT.PlayerState.PLAYING;this.sync()},onAutoplayBlocked:()=>{this.player?.mute();this.muted=true;this.player?.seekTo(ALBUM.startSeconds,true);this.player?.playVideo();this.setStatus('TRACK 3 · AUTOPLAY MUTED');this.sync()},onError:()=>this.setStatus('MUSIC UNAVAILABLE')}})}
  togglePlay(){if(!this.player){this.init();return}if(this.playing)this.player.pauseVideo();else this.player.playVideo()}
  toggleMute(){if(!this.player){this.init();return}if(this.muted){this.player.unMute();this.muted=false}else{this.player.mute();this.muted=true}this.sync()}
  sync(){if(this.playButton)this.playButton.textContent=this.playing?'PAUSE':'PLAY';if(this.muteButton)this.muteButton.textContent=this.muted?'UNMUTE':'MUTE'}
  setStatus(value){if(this.status)this.status.textContent=value}
}
