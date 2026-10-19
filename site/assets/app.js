(function(){
"use strict";
var DK=window.DitherKitLite, B=window.BENCH;
var RM=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;
var INK=[205,205,200], SIG=[232,166,74], DIM=[96,96,102];
if(DK){DK.PALETTE.ink={fill:INK,line:[235,235,230]};DK.PALETTE.sig={fill:SIG,line:[250,200,130]};DK.PALETTE.dim={fill:DIM,line:[140,140,146]};}
// Bayer 4x4, identical to DitherKit's chart matrix (assets/vendor/bayer-matrices.json)
var BAY=[[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]].map(function(r){return r.map(function(v){return (v+.5)/16})});
function bay(x,y){return BAY[y&3][x&3]}
function rgba(c,a){return "rgba("+c[0]+","+c[1]+","+c[2]+","+a+")"}
function fitCanvas(cv,cell){var r=cv.getBoundingClientRect(),w=Math.max(1,Math.round(r.width)),h=Math.max(1,Math.round(r.height)),d=Math.min(window.devicePixelRatio||1,2);cv.width=Math.round(w*d);cv.height=Math.round(h*d);var c=cv.getContext("2d");c.setTransform(d,0,0,d,0,0);return {c:c,w:w,h:h,cols:Math.ceil(w/cell),rows:Math.ceil(h/cell)}}
function off(cols,rows){var o=document.createElement("canvas");o.width=cols;o.height=rows;return o}

/* animation helpers: one rAF per element, throttled, paused offscreen and when the tab is hidden */
function loop(el,fps,draw){if(RM){draw(0,1);return}var vis=false,raf=0,last=0,t0=0,iv=1000/fps;
  function tick(n){raf=requestAnimationFrame(tick);if(!vis||document.hidden)return;if(!t0)t0=n;if(n-last<iv)return;last=n;draw((n-t0)/1000,0)}
  if("IntersectionObserver"in window)new IntersectionObserver(function(e){vis=e[0].isIntersecting;if(vis&&!raf)raf=requestAnimationFrame(tick)},{rootMargin:"80px"}).observe(el);else{vis=true;raf=requestAnimationFrame(tick)}}
function onReveal(el,fn){if(RM||!("IntersectionObserver"in window)){fn();return}var io=new IntersectionObserver(function(e){if(e[0].isIntersecting){io.disconnect();fn()}},{threshold:.15});io.observe(el)}
function ease(t){return 1-Math.pow(1-t,3)}
/* scroll reveals */
function reveals(){if(RM)return;document.querySelectorAll(".sec,.phead").forEach(function(s){var r=s.getBoundingClientRect();if(r.top<innerHeight)return;s.classList.add("rv");onReveal(s,function(){s.classList.add("in")})})}
/* nav */
var tg=document.querySelector(".navtoggle"),nav=document.getElementById("nav");
if(tg)tg.addEventListener("click",function(){var o=nav.classList.toggle("open");tg.setAttribute("aria-expanded",o)});

/* DitherKit bar charts: HTML rows (exact values, real fonts) + DitherKit meters as bars */
function bars(){document.querySelectorAll("[data-bars]").forEach(function(el){
  if(el.getAttribute("data-ok"))return;
  var d=JSON.parse(el.getAttribute("data-bars")),mx=+el.getAttribute("data-max")||Math.max.apply(null,d.map(function(x){return x.value}));
  var unit=el.getAttribute("data-unit")||"",dec=el.getAttribute("data-dec");
  el.innerHTML=d.map(function(x){var v=(Math.round(x.value*10)/10);return '<div class="br"><span class="bl">'+esc(x.label)+'</span><span class="meter bm" data-meter="'+x.value+'" data-max="'+mx+'" data-hl="'+(x.hl?1:0)+'"></span><span class="bv">'+(dec?(+x.value).toFixed(+dec):(v%1?v.toFixed(1):v))+unit+'</span></div>'}).join("");
  el.setAttribute("data-ok","1");
})}
/* DitherKit meters */
function meters(root){(root||document).querySelectorAll("[data-meter]").forEach(function(el){
  if(el.getAttribute("data-none")==="1"){el.style.background="repeating-linear-gradient(135deg,#2a2a2e 0 1px,transparent 1px 4px)";return}
  var v=+el.getAttribute("data-meter"),mx=+el.getAttribute("data-max"),col=el.getAttribute("data-hl")==="1"?"sig":"ink";
  function paint(p,ph){DK.renderDitherMeter(el,{progress:v*p,max:mx,color:col,bloom:"soft",phase:ph||0})}
  if(RM||el._filled){paint(1);return}
  paint(0.001);onReveal(el,function(){var s=performance.now(),d=700+Math.random()*500;(function f(n){var t=Math.min(1,(n-s)/d);paint(ease(t),t*3);if(t<1)requestAnimationFrame(f);else el._filled=1})(s)});
  var host=el.closest(".br,.pod,.crit li,.cscore>a,.cmp tr")||el;
  if(!RM&&!host._hov){host._hov=1;host.addEventListener("mouseenter",function(){host.querySelectorAll("[data-meter]").forEach(function(m){if(m._filled)DK.startMeterDitherLoop(m,{bloom:"soft"})})});
    host.addEventListener("mouseleave",function(){host.querySelectorAll("[data-meter]").forEach(function(m){DK.stopMeterDitherLoop(m)})})}
})}

/* Heatmap: custom Bayer cells */
function paintCell(cv,v,hl,ph){ph=ph||0;var f=cv._f&&cv._f.w===Math.round(cv.getBoundingClientRect().width)?cv._f:(cv._f=fitCanvas(cv,2)),o=off(f.cols,f.rows),c=o.getContext("2d"),ox=Math.floor(ph*2)&3,oy=Math.floor(ph*1.3)&3;
  for(var y=0;y<f.rows;y++)for(var x=0;x<f.cols;x++){
    if(v==null){if(((x+y+ox)&3)===0){c.fillStyle=rgba(DIM,.55);c.fillRect(x,y,1,1)}continue}
    var dens=v/5*.92*(0.94+.06*Math.sin(ph*1.4+x*.5+y*.3));if(dens>bay(x+ox,y+oy)){c.fillStyle=rgba(hl?SIG:INK,.35+.6*dens);c.fillRect(x,y,1,1)}}
  f.c.imageSmoothingEnabled=false;f.c.clearRect(0,0,f.w,f.h);f.c.drawImage(o,0,0,f.cols*2,f.rows*2)}
function heat(){var el=document.querySelector("[data-heat]");if(!el||!B)return;
  if(!el.childElementCount){var h='<div class="hd" role="columnheader">Tool</div>';
    B.criteria.forEach(function(c){h+='<div class="hd" role="columnheader" title="'+c.label+' (weight '+c.w+')">'+c.k+'</div>'});
    h+='<div class="hd" role="columnheader">Score</div>';
    B.tools.forEach(function(t){h+='<div class="nm" role="rowheader"><a href="tools/'+t.id+'.html">'+t.short+'</a></div>';
      B.criteria.forEach(function(c){var v=t.crit[c.k];h+='<div class="cell" role="cell" aria-label="'+c.label+': '+(v==null?"no evidence":v+" of 5")+'"><canvas data-v="'+(v==null?"":v)+'"></canvas><span aria-hidden="true">'+(v==null?"·":v)+'</span></div>'});
      h+='<div class="tot" role="cell">'+t.score.toFixed(1)+'</div>'});
    el.innerHTML=h}
  var cvs=[].slice.call(el.querySelectorAll("canvas"));function draw(ph){cvs.forEach(function(cv,i){var v=cv.getAttribute("data-v");paintCell(cv,v===""?null:+v,false,ph+i*.07)})}
  draw(0);if(!el._loop){el._loop=1;loop(el,6,function(t){draw(t)})}}

/* Radar: custom Bayer polygon fill */
function radar(cv,series,k,ph){k=k==null?1:k;ph=ph||0;var f=fitCanvas(cv,2),W=f.w,H=f.h,cx=W/2,cy=H/2,R=Math.min(W,H)/2-(W<360?40:76),n=B.criteria.length;
  function pt(i,r){var a=-Math.PI/2+i*2*Math.PI/n;return [cx+Math.cos(a)*r,cy+Math.sin(a)*r]}
  var ctx=f.c;ctx.clearRect(0,0,W,H);ctx.strokeStyle="#2a2a2e";ctx.lineWidth=1;
  for(var g=1;g<=5;g++){ctx.beginPath();for(var i=0;i<n;i++){var p=pt(i,R*g/5);i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1])}ctx.closePath();ctx.stroke()}
  for(i=0;i<n;i++){var p2=pt(i,R);ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(p2[0],p2[1]);ctx.stroke()}
  var o=off(f.cols,f.rows),oc=o.getContext("2d");
  series.forEach(function(s,si){var path=new Path2D();B.criteria.forEach(function(c,i){var v=s.t.crit[c.k];var p=pt(i,R*k*(v==null?2.5:v)/5);i?path.lineTo(p[0]/2,p[1]/2):path.moveTo(p[0]/2,p[1]/2)});path.closePath();
    for(var y=0;y<f.rows;y++)for(var x=0;x<f.cols;x++){if(!oc.isPointInPath(path,x+.5,y+.5))continue;var d=Math.hypot(x*2-cx,y*2-cy)/R;var dens=(si?.2:.18)+.38*d;
      var sh=Math.floor(ph*1.5)&3;var th=si?bay(x+2+sh,y+1):bay(x+sh,y+(sh>>1));if(dens>th){oc.fillStyle=rgba(s.c,si?.6:.75);oc.fillRect(x,y,1,1)}}
    s.path=path});
  ctx.imageSmoothingEnabled=false;ctx.drawImage(o,0,0,f.cols*2,f.rows*2);
  series.forEach(function(s){ctx.save();ctx.scale(2,2);ctx.strokeStyle=rgba(s.c,.95);ctx.lineWidth=.5;ctx.stroke(s.path);ctx.restore()});
  ctx.font='500 '+(W<360?10:11)+'px GM, ui-monospace, monospace';ctx.textBaseline="middle";
  B.criteria.forEach(function(c,i){var p=pt(i,R+(W<360?16:22));ctx.textAlign=Math.abs(p[0]-cx)<8?"center":p[0]<cx?"right":"left";ctx.fillStyle="#a6a6a8";
    var lab=W<360?c.k:c.k+" "+c.label.split(" ")[0];ctx.fillText(lab,p[0],p[1]);
    series.forEach(function(s,si){var v=s.t.crit[c.k];ctx.fillStyle=rgba(s.c,1);ctx.fillText(v==null?"·":String(v),p[0]+(ctx.textAlign==="right"?-si*16:ctx.textAlign==="left"?si*16:(si-.5*(series.length-1))*16)+(ctx.textAlign==="center"?0:0),p[1]+13)})})}
function animRadar(cv,series){cv._series=series;if(RM){radar(cv,series);return}
  if(!cv._anim){cv._anim=1;cv._k=0;onReveal(cv,function(){var s=performance.now();(function f(n){var t=Math.min(1,(n-s)/900);cv._k=ease(t);radar(cv,cv._series,cv._k,0);if(t<1)requestAnimationFrame(f);else loop(cv,8,function(tt){radar(cv,cv._series,1,tt)})})(s)})}
  radar(cv,series,cv._k==null?1:cv._k,0)}
function toolRadars(){document.querySelectorAll("[data-radar]").forEach(function(cv){var t=B.tools.find(function(x){return x.id===cv.getAttribute("data-radar")});animRadar(cv,[{t:t,c:SIG}])})}

/* Hero art: 6 worktree lanes fan out from one prompt and merge; 5 clean, 1 designed conflict */
function hero(){var cv=document.getElementById("heroArt");if(!cv)return;var CELL=3,f,o,oc,ph=0,raf=0,last=0,vis=true;
  function setup(){f=fitCanvas(cv,CELL);o=off(f.cols,f.rows);oc=o.getContext("2d")}
  function lane(k,u){return .5+(k-2.5)*.135*Math.sin(Math.PI*u)}
  function draw(){var C=f.cols,Rr=f.rows,img=oc.createImageData(C,Rr),D=img.data;var x0=.08,x1=.92;
    for(var y=0;y<Rr;y++){var ny=y/Rr;for(var x=0;x<C;x++){var nx=x/C,u=(nx-x0)/(x1-x0),dens=0,hot=0;
      if(u>=0&&u<=1){for(var k=0;k<6;k++){if(k===5&&u>.84)continue;var dy=(ny-lane(k,u))*Rr/C*1.7;var g=Math.exp(-dy*dy*2600);var pulse=Math.exp(-Math.pow(((u-ph*.55-k*.11)%1+1)%1-.5,2)*90);
        var dd=g*(.38+.62*pulse);if(k===5&&u>.62)hot=Math.max(hot,g*1.6*(u-.62)/.22);dens=Math.max(dens,dd)}}
      var node=Math.max(Math.exp(-(Math.pow((nx-x0)*C/Rr,2)+Math.pow(ny-.5,2))*900),Math.exp(-(Math.pow((nx-x1)*C/Rr,2)+Math.pow(ny-.5,2))*900));dens=Math.max(dens,node);
      dens=Math.max(dens,.045);
      var t=bay(x,y),i=(y*C+x)*4;if(dens>t){var c=hot>.35?SIG:INK,a=Math.min(1,.35+dens*.8);D[i]=c[0];D[i+1]=c[1];D[i+2]=c[2];D[i+3]=a*255}}}
    oc.putImageData(img,0,0);f.c.imageSmoothingEnabled=false;f.c.clearRect(0,0,f.w,f.h);f.c.drawImage(o,0,0,C*CELL,Rr*CELL)}
  function tick(now){raf=requestAnimationFrame(tick);if(!vis||now-last<66)return;last=now;ph+=.012;draw()}
  setup();draw();loop(cv,15,function(t){ph=t*.18;draw()})
  window.addEventListener("resize",function(){setup();draw()})}

/* Hero background: drifting, flowing Bayer field */
function heroField(){var cv=document.getElementById("heroField");if(!cv)return;var CELL=4,f,o,oc;
  function setup(){f=fitCanvas(cv,CELL);o=off(f.cols,f.rows);oc=o.getContext("2d")}
  function draw(t){var C=f.cols,Rr=f.rows,img=oc.createImageData(C,Rr),D=img.data,dx=Math.floor(t*3)&3;
    for(var y=0;y<Rr;y++)for(var x=0;x<C;x++){var nx=x/C,ny=y/Rr;
      var d=.5+.5*Math.sin(nx*7+t*.35+Math.sin(ny*5-t*.25)*1.6)*Math.cos(ny*4-t*.2);d=d*Math.max(0,(nx-.3)/.7)*.42;
      if(d>bay(x+dx,y)){var i=(y*C+x)*4;D[i]=INK[0];D[i+1]=INK[1];D[i+2]=INK[2];D[i+3]=34+90*d}}
    oc.putImageData(img,0,0);f.c.imageSmoothingEnabled=false;f.c.clearRect(0,0,f.w,f.h);f.c.drawImage(o,0,0,C*CELL,Rr*CELL)}
  setup();draw(0);loop(cv,12,function(t){draw(t)});window.addEventListener("resize",function(){setup();draw(0)})}
/* Tier bands: dithered strips, denser for higher tiers, slowly flowing */
function tierBands(){document.querySelectorAll("canvas.tband").forEach(function(cv){var i=+cv.getAttribute("data-tier"),base=[.62,.5,.4,.3,.2][i],col=i===0?SIG:INK;
  function draw(t){var f=fitCanvas(cv,2),o=off(f.cols,f.rows),c=o.getContext("2d"),sh=Math.floor(t*2)&3;
    for(var y=0;y<f.rows;y++)for(var x=0;x<f.cols;x++){var d=base*(1-x/f.cols*.55)*(.9+.1*Math.sin(t*1.2+y*.4+x*.15));if(d>bay(x+sh,y)){c.fillStyle=rgba(col,.25+.5*d);c.fillRect(x,y,1,1)}}
    f.c.imageSmoothingEnabled=false;f.c.clearRect(0,0,f.w,f.h);f.c.drawImage(o,0,0,f.cols*2,f.rows*2)}
  draw(0);loop(cv,8,draw)})}
/* Sortable leaderboard */
function sortable(){var tb=document.getElementById("lb");if(!tb)return;var body=tb.tBodies[0];
  tb.querySelectorAll("thead button").forEach(function(b){b.addEventListener("click",function(){var th=b.parentNode,k=b.getAttribute("data-k"),num=b.getAttribute("data-type")==="n";
    var cur=th.getAttribute("aria-sort"),dir=cur==="descending"?"ascending":cur==="ascending"?"descending":(num&&k!=="rank"?"descending":"ascending");
    tb.querySelectorAll("thead th").forEach(function(x){x.setAttribute("aria-sort","none")});th.setAttribute("aria-sort",dir);
    var rows=[].slice.call(body.rows);rows.sort(function(a,c){var x=a.dataset[k.toLowerCase()],y=c.dataset[k.toLowerCase()];var r=num?(+x)-(+y):x.localeCompare(y);if(r===0)r=(+a.dataset.rank)-(+c.dataset.rank);return dir==="ascending"?r:-r});
    rows.forEach(function(r){body.appendChild(r)})})})}

/* Compare */
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function compare(){var sa=document.getElementById("ca"),sb=document.getElementById("cb");if(!sa)return;
  var q=new URLSearchParams(location.search),ids=B.tools.map(function(t){return t.id});
  sa.value=ids.indexOf(q.get("a"))>=0?q.get("a"):"orca";sb.value=ids.indexOf(q.get("b"))>=0?q.get("b"):"t3";
  function T(id){return B.tools.find(function(t){return t.id===id})}
  function render(){var a=T(sa.value),b=T(sb.value);history.replaceState(null,"","?a="+a.id+"&b="+b.id);
    document.getElementById("ka").textContent=a.name;document.getElementById("kb").textContent=b.name;
    document.getElementById("cscore").innerHTML=[a,b].map(function(t,i){return '<a href="tools/'+t.id+'.html"><span class="lab">#'+t.rank+' / range '+t.range[0]+' to '+t.range[1]+' / doc cov '+t.coverage+'% / '+t.validation+'</span><span class="podn" style="font-size:26px;letter-spacing:-.04em">'+esc(t.name)+'</span><b>'+t.score.toFixed(1)+'</b><span class="meter" data-meter="'+t.score+'" data-max="100" data-hl="'+(i?0:1)+'"></span><p>'+esc(t.why)+'</p></a>'}).join("");
    var h='<thead><tr><th scope="col">Criterion</th><th scope="col" class="wcol">Weight</th><th scope="col">'+esc(a.name)+'</th><th scope="col">'+esc(b.name)+'</th><th scope="col">Edge</th></tr></thead><tbody>';
    B.criteria.forEach(function(c){var va=a.crit[c.k],vb=b.crit[c.k];var e=(va==null||vb==null)?"n/a":va===vb?"even":(va>vb?a.short:b.short)+" +"+Math.abs(va-vb);
      function cell(v,hl){return '<td class="m"><span class="meter" data-meter="'+(v==null?0:v)+'" data-max="5" data-none="'+(v==null?1:0)+'" data-hl="'+hl+'"></span><span class="num" style="display:block;text-align:left;margin-top:4px">'+(v==null?"n/r, no evidence":v+" / 5")+'</span></td>'}
      h+='<tr><th scope="row">'+c.k+' '+esc(c.label)+'</th><td class="num wcol">'+c.w+'</td>'+cell(va,1)+cell(vb,0)+'<td>'+esc(e)+'</td></tr>'});
    document.getElementById("ctable").innerHTML=h+"</tbody>";
    var F=[["Hands-on status","status"],["License","license"],["Pricing","price"],["Stars","stars"],["Latest release","release"],["Who it is for","who"],["Strengths","pros"],["Weaknesses","cons"],["Hands-on evidence","hands_on"],["Platforms","f:platforms"],["Agents","f:agents"],["Isolation","f:isolation"],["Review and PR","f:review"],["Remote / mobile","f:remote"],["MCP","f:mcp"],["Setup","f:setup"]];
    function val(t,k){var v=k.indexOf("f:")===0?t.facts[k.slice(2)]:t[k];if(Array.isArray(v))return "<ul>"+v.map(function(x){return "<li>"+esc(x)+"</li>"}).join("")+"</ul>";return esc(v||"-")}
    document.getElementById("cfacts").innerHTML='<thead><tr><th scope="col"></th><th scope="col">'+esc(a.name)+'</th><th scope="col">'+esc(b.name)+'</th></tr></thead><tbody>'+F.map(function(r){return '<tr><th scope="row">'+r[0]+'</th><td>'+val(a,r[1])+'</td><td>'+val(b,r[1])+'</td></tr>'}).join("")+"</tbody>";
    animRadar(document.getElementById("cradar"),[{t:a,c:SIG},{t:b,c:INK}]);meters(document.querySelector("main"))}
  sa.addEventListener("change",render);sb.addEventListener("change",render);
  document.getElementById("swap").addEventListener("click",function(){var x=sa.value;sa.value=sb.value;sb.value=x;render()});
  render();window._cmp=render}

function all(){if(DK){bars();meters()}heat();if(B){toolRadars();if(window._cmp)window._cmp()}}
function init(){reveals();heroField();tierBands();hero();sortable();if(B)compare();all();var w=window.innerWidth,tm;window.addEventListener("resize",function(){if(window.innerWidth===w)return;w=window.innerWidth;clearTimeout(tm);tm=setTimeout(all,150)})}
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(init);else window.addEventListener("load",init);
})();
