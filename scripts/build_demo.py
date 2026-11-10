from pathlib import Path
from urllib.request import urlopen, Request
import base64, hashlib, json, re, subprocess

ROOT = Path(__file__).resolve().parents[1]
REV = '4fa95d1672a7baf6c1834df661c0e69260e57954'
SOURCE = ROOT / '.ui-cache'
FILES = ['src/app.js','src/style.css','src/model.js','src/conversations.js','src/widgets.js','src/source-health.js','src/file-summaries.js','src/task-filters.js','src/history.js','src/assets/city-panorama-ai.webp','public/images/chatgpt.svg','public/images/clovanote.svg','public/icon.svg']
for name in FILES:
    p = SOURCE / name
    if not p.exists():
        url = f'https://raw.githubusercontent.com/jinwoo165/dahandot-workdesk/{REV}/{name}'
        with urlopen(Request(url, headers={'User-Agent':'dahandot-independent-demo-build'}), timeout=30) as r:
            data = r.read()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
assert hashlib.sha256((SOURCE/'src/app.js').read_bytes()).hexdigest() == '7d8790c625fd6f0f9fe3c9a02462aac2bd2dd371cba96bcf71b37d1f24c314fd'
assert hashlib.sha256((SOURCE/'src/style.css').read_bytes()).hexdigest() == 'b68cd4abcc9e31bd5d1e7716a31fabfdbd5c1939666b27c2d02dac2d60ac7c7f'
C = json.loads((ROOT/'demo-content.json').read_text())
s = (SOURCE/'src/app.js').read_text()
init = s.split('if(demo){const date=day();',1)[1].split('refresh(true);}else{db.auth.onAuthStateChange',1)[0]
s = s.split('if(demo){const date=day();',1)[0]
s = re.sub(r"^import .*?(?:@supabase|config\.js|sceneryURL|style\.css).*?\n", '', s, flags=re.M)
s = re.sub(r"^const db=.*?\n", '', s, flags=re.M)
s = s.replace("const demo=new URLSearchParams(location.search).get('demo')==='1';", "const demo=true;")
s = s.replace("const APP_VERSION='2.7.0';", "const APP_VERSION='1.0.0';")
s = re.sub(r'try\{[^{}]*localStorage[^{}]*\}catch\{\}', '', s)

def span(start, end, replacement):
    global s
    a=s.index(start); b=s.index(end,a)
    s=s[:a]+replacement+'\n'+s[b:]

span('async function loadFiles()', 'function weatherWidget()', '')
span('async function loadFileSummaries()', 'function fileEntry(', '')
span('async function rows(', 'function taskCard(', '''async function loadHistory(){state.historyMonth=state.month;state.historyError='';}
async function refresh(silent=false){if(!state.workspace||state.loading)return;state.loading=true;try{state.synced=new Date().toISOString();render();refreshConversation();void updateWeather();if(!silent)toast(CONTENT.notice);}finally{state.loading=false;}}
const syncLabel=()=>`<i class="sync-dot"></i>${esc(CONTENT.notice.split(' · ').at(-1))}<br><small>${esc(CONTENT.guides[3][0])}</small>`;
''')
span('function guideSections()', 'function openGuide()', 'function guideSections(){return CONTENT.guides;}')
span('async function setLinkRemoved(', 'function bodyView()', '''async function setLinkRemoved(id,removed){state.links=state.links.map(l=>l.id===id?{...l,removed_at:removed?new Date().toISOString():null}:l);render();}''')
span('function sourceIndicator()', 'function bindSourcePopup(', '''function sourceIndicator(){return `<button id="sourceStatusButton" class="source-status-button" popovertarget="sourcePopover" aria-expanded="false"><i class="source-dot not_checked"></i><span>${esc(CONTENT.notice.split(' · ').at(-1))}</span><span>⌄</span></button><section id="sourcePopover" class="source-popover" popover="auto"></section>`;}
function paintSourcePopup(){const popup=$('#sourcePopover');if(!popup)return;popup.innerHTML=`<div class="source-popup-head"><strong>${esc(CONTENT.notice.split(' · ')[0])}</strong><button class="source-close" popovertarget="sourcePopover" popovertargetaction="hide">×</button></div><p class="source-popup-hint">${esc(CONTENT.guides[0][1])}</p><p class="source-popup-foot">${esc(CONTENT.guides[5][1])}</p>`;}
''')
span('let versionCheckedAt=0;', 'async function manualRefresh()', 'async function checkForUpdate(){return null;}\nfunction applyUpdate(){location.reload();}')
s = re.sub(r"detailHistory=demo\?state\.history\.filter\(h=>h\.task_id===id\):await rows\('task_history'.*?;if\(conversationTarget", "detailHistory=state.history.filter(h=>h.task_id===id);if(conversationTarget",s)
span('async function sendConversation(', 'function showHistory(', '''async function sendConversation(e){e.preventDefault();const input=$('#conversationText'),target={...conversationTarget};try{const body=validateMessage(input.value);state.messages.push({id:crypto.randomUUID(),...target,body,created_at:new Date().toISOString(),resolution_status:'pending',reply:'',changes:[]});drafts.delete(targetKey(target));input.value='';threadPage=messagesForTarget(state.messages,target).length-1;render();refreshConversation();toast(CONTENT.guides[3][0]);}catch(error){$('#conversationError').textContent=errorMessage(error);}}
''')
span('async function exportBackup()', 'let resizeTimer;', '''async function exportBackup(){const payload={type:'dahandot.public-demo',version:1,exported_at:new Date().toISOString(),tasks:state.tasks,events:state.events,history:state.history,messages:state.messages,links:state.links};const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='dahandot-demo-'+day()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function logout(){location.reload();}
''')
span('function fileEntry(', 'function toast(', '''function fileEntry(f){const row=state.fileSummaries.find(r=>r.item_id===f.item_id);return `<article class="file-card"><div class="file-entry"><span class="file-icon ${fileKind(f.name).toLowerCase()}">${fileKind(f.name)}</span><span class="file-info"><strong title="${esc(f.name)}">${esc(f.name)}</strong><span class="file-meta">${esc(CONTENT.labels.report)}</span><span class="file-summary has-summary">${esc(row.summary)}</span></span></div>${infoButton('file-summary:'+f.item_id,f.name,row.summary+'\\n\\n'+row.detail,CONTENT.labels.fullSummary)}</article>`;}
function filesWidget(){return `<section class="panel files-panel paged-panel" aria-label="${esc(CONTENT.labels.recentFiles)}"><div class="panel-head"><div><h2>${esc(CONTENT.labels.recentFiles)}</h2><small>${esc(CONTENT.labels.report)} · ${state.files.length}</small></div><span class="cloud-mark">☁</span></div>${pageList(state.files,'files',fileEntry,180)}<div class="file-check">${infoButton('file-scope',CONTENT.guides[2][0],CONTENT.guides[2][1],CONTENT.labels.scope)}</div></section>`;}
''')
s=s.replace('예시','체험').replace('로그아웃','체험 초기화')
s=re.sub(r'<div class="notice demo-notice">.*?</div>', '<div class="notice demo-notice">'+C['notice']+'</div>',s)
s=re.sub(r'<details class="conversation-timing">.*?</details>', '<details class="conversation-timing"><summary>${esc(CONTENT.guides[3][0])}</summary><p>${esc(CONTENT.guides[3][1])}</p></details>',s)
s=re.sub(r'<p class="conversation-page-note">.*?</p>', '<p class="conversation-page-note">${esc(CONTENT.guides[3][1].split(".")[0])}.</p>',s)
s=s.replace("${latest?'원본 조회 '+kstTime(latest.generated_at):''}", '${esc(CONTENT.notice.split(" · ")[0])}')
s=re.sub(r'<div class="notice offline">.*?</div>', '<div class="notice offline">Offline · ${esc(CONTENT.guides[3][0])}</div>',s)
s=re.sub(r'<small>현재 반영된.*?</small>', '<small>${esc(CONTENT.guides[3][1].split(".")[0])}.</small>',s)
C['labels']={'report':'업무 보고자료 · 공개 요약','fullSummary':'요약 전체','recentFiles':'OneDrive 최근 자료','scope':'범위','plan':'업무 계획 · 일정 미확정','history':'업무 흐름 정리','initial':'검토 착수','review':'검토 내용 정리','next':'후속 업무 정리'}
init += '''
const stamp=new Date().toISOString();
for(const [i,t] of state.tasks.entries()){t.created_at=stamp;if(t.status==='done'){t.next_review_on=null;t.remaining_action='';t.next_action='';}}
CONTENT.extraTasks.forEach((t,i)=>state.tasks.push({...t,id:'demo:extra-'+i,priority:'normal',due_date:addDays(date,t.offset),next_review_on:t.status==='done'?null:addDays(date,t.offset),remaining_action:t.next_action,pinned:false,revision:1,source_refs:[],created_at:stamp}));
state.links=CONTENT.links.map(([label,url,description],i)=>({id:'demo:link-'+i,label,url,description}));
state.files=CONTENT.reports.map((f,i)=>({drive_id:'public-demo',item_id:'report-'+i,name:f.name,folder_path:'DX AX',web_url:'',change_kind:'created',changed_at:stamp,modified_at_source:stamp}));
state.fileSummaries=CONTENT.reports.map((f,i)=>({drive_id:'public-demo',item_id:'report-'+i,source_modified_at:stamp,summary:f.summary,status:'ok',detail:f.detail,checked_at:stamp}));
state.events=state.tasks.filter(t=>t.status!=='done').map((t,i)=>({id:'demo:plan-'+i,title:t.title,start_at:t.due_date+'T00:00:00+09:00',end_at:addDays(t.due_date,1)+'T00:00:00+09:00',all_day:true,status:'tentative',url:'',note:CONTENT.labels.plan+'\\n'+t.note+'\\n'+t.next_action}));
state.events.push(...CONTENT.historicEvents.map(([d,title,note],i)=>({id:'demo:record-'+i,title,start_at:d+'T00:00:00+09:00',end_at:addDays(d,1)+'T00:00:00+09:00',all_day:true,status:'confirmed',url:'',note})));
state.history=state.tasks.flatMap((t,i)=>[0,1,2].map(j=>{const d=addDays(date,-(i%7)-3+j);return {id:'demo:history-'+i+'-'+j,task_id:t.id,occurred_at:d+'T16:00:00+09:00',actor:CONTENT.labels.history,action:[CONTENT.labels.initial,CONTENT.labels.review,CONTENT.labels.next][j],before_data:j?{...t,status:j===1?'todo':'doing'}:null,after_data:{...t,status:j===0?'todo':j===1?'doing':t.status,note:j===0?t.project+' / '+t.title:j===1?t.note:t.note+'\\n'+(t.remaining_action||t.next_action||'')}};})).sort((a,b)=>b.occurred_at.localeCompare(a.occurred_at));
state.messages.push(...state.tasks.slice(3,7).map((t,i)=>({id:'demo:discussion-'+i,task_id:t.id,body:t.note,created_at:addDays(date,-i-1)+'T10:00:00+09:00',resolution_status:'applied',reply:t.remaining_action,resolved_at:addDays(date,-i-1)+'T10:05:00+09:00',changes:[]})));
state.runs=[{summary:CONTENT.briefing.join('\\n'),generated_at:stamp,sources:[]}];
state.fileRuns=[];
'''
s += '\nfunction initDemo(){const date=day();\n'+init+'\n}\ninitDemo();refresh(true);\n'
for pattern in [r'\bdb\.',r'\brows\(',r'createClient',r'SUPABASE_',r'LOGIN_CONFIGURED',r'localStorage',r'sessionStorage',r'document\.cookie',r'serviceWorker',r'config\.js']:
    assert not re.search(pattern,s), f'Unsafe residual: {pattern}'
def data_uri(name,mime):
    return 'data:'+mime+';base64,'+base64.b64encode((SOURCE/name).read_bytes()).decode()
s="const CONTENT="+json.dumps(C,ensure_ascii=False)+";\nconst sceneryURL="+json.dumps(data_uri('src/assets/city-panorama-ai.webp','image/webp'))+";\n"+s
for icon in ['chatgpt','clovanote']:
    s=s.replace('./images/'+icon+'.svg',data_uri('public/images/'+icon+'.svg','image/svg+xml'))

def module_code(name,text):
    exports=re.findall(r'^export (?:async )?(?:function|const|let|class) (\w+)',text,re.M)
    text=re.sub(r"import \{([^}]+)\} from ['\"]\./([^'\"]+)['\"];",lambda m:'const {'+re.sub(r'\bas\b',':',m[1])+"}=M['"+m[2]+"'];",text)
    text=re.sub(r'^export ', '', text, flags=re.M)
    return "M['"+name+"']=(()=>{\n"+text+'\nreturn {'+','.join(exports)+'};\n})();\n'
js='(()=>{\nconst M={};\n'
for name in ['model.js','conversations.js','widgets.js','source-health.js','file-summaries.js','task-filters.js','history.js']:
    t=(SOURCE/'src'/name).read_text()
    if name=='conversations.js':
        t=t.replace('다한닷 확인 대기','화면에 보관').replace('반영 완료','기록된 정리')
    js+=module_code(name,t)
js+=module_code('app.js',s)+'})();'
assert '</script' not in js.lower()
css=(SOURCE/'src/style.css').read_text()
assert not re.search(r'@import|https?://',css)
css+='\n.demo-notice{padding:7px 12px;font-size:11px;margin-bottom:10px}.file-summary{line-height:1.65}.info-body{line-height:1.85}.source-popup-hint{white-space:normal}\n'
script_hash=base64.b64encode(hashlib.sha256(js.encode()).digest()).decode()
csp="default-src 'none'; script-src 'sha256-"+script_hash+"'; style-src 'unsafe-inline'; img-src data:; connect-src https://api.open-meteo.com; base-uri 'none'; form-action 'none'; object-src 'none'; frame-src 'none'; worker-src 'none'"
html='<!doctype html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="'+csp+'"><meta name="robots" content="noindex,nofollow"><link rel="icon" href="'+data_uri('public/icon.svg','image/svg+xml')+'"><title>다한닷 · DX AX 업무보드</title><style>'+css+'</style></head><body><div id="app"></div><dialog id="detail"></dialog><dialog id="historyDetail"></dialog><div id="toast" role="status" aria-live="polite"></div><script>'+js+'</script></body></html>'
(ROOT/'index.html').write_text(html)
(ROOT/'.nojekyll').write_text('')
(ROOT/'build.js').write_text(js)
subprocess.run(['node','--check',str(ROOT/'build.js')],check=True)
report={'version':C['version'],'production_revision_read_only':REV,'bytes':len(html.encode()),'sha256':hashlib.sha256(html.encode()).hexdigest(),'app_code_has_backend':False,'browser_storage_used':False,'outbound_allowlist':['https://api.open-meteo.com'],'report_count':len(C['reports']),'task_count':10+len(C['extraTasks']),'security_scope':'Static build checks; browser tests are reported separately. Same github.io account is not a separate browser origin.'}
(ROOT/'build-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
