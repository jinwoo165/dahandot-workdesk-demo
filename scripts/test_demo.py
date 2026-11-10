from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from functools import partial
from threading import Thread
from datetime import datetime,timedelta,timezone
import json,re,hashlib
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
out=root/'qa';out.mkdir(exist_ok=True)
html=(root/'index.html').read_text()
checks=[]
def check(label,condition):
    if not condition: raise AssertionError(label)
    checks.append(label)
for pattern in [r'supabase\.co',r'createClient',r'localStorage',r'sessionStorage',r'document\.cookie',r'serviceWorker',r'sk-proj-',r'@hdc-',r'@gmail\.',r'<input[^>]*password']:
    check('static absence: '+pattern,not re.search(pattern,html,re.I))
check('CSP weather-only connections',"connect-src https://api.open-meteo.com;" in html)
check('no production URL navigation','https://jinwoo165.github.io/dahandot-workdesk/' not in html)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)))
Thread(target=server.serve_forever,daemon=True).start()
url='http://127.0.0.1:'+str(server.server_port)+'/index.html'
errors=[];requests=[]
try:
 with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1000},timezone_id='Asia/Seoul',accept_downloads=True)
    context.add_init_script("""window.__storageAudit=[];for(const name of ['localStorage','sessionStorage']){const d=Object.getOwnPropertyDescriptor(window,name);if(d&&d.get)Object.defineProperty(window,name,{get(){window.__storageAudit.push(name);return d.get.call(window)}})}""")
    today=datetime.now(timezone(timedelta(hours=9))).date()
    dates=[str(today),str(today+timedelta(days=1))]
    def weather(route):
        route.fulfill(json={'timezone':'Asia/Seoul','daily':{'time':dates,'weather_code':[1,2],'temperature_2m_min':[5,6],'temperature_2m_max':[16,17],'precipitation_probability_max':[0,10]},'current':{'time':dates[0]+'T09:00','temperature_2m':12,'weather_code':1,'is_day':1}})
    context.route('https://api.open-meteo.com/**',weather)
    page=context.new_page();page.set_default_timeout(12000)
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:requests.append({'url':r.url,'method':r.method}))
    page.goto(url,wait_until='networkidle');page.wait_for_timeout(400)
    check('initial work view',page.locator('h1').count()==1)
    check('three briefing entries',page.locator('.briefing li').count()==3)
    check('task detail accessible',page.locator('[data-task]').count()>0)
    check('no login form',page.locator('#loginForm').count()==0)
    check('no placeholder wording','예시' not in page.locator('body').inner_text())
    page.screenshot(path=str(out/'desktop.png'))
    reference={k:page.locator(k).bounding_box() for k in ['.scenic-banner','#weatherWidget','.shared-files']}
    for v in ['calendar','links','archived','conversation','work']:
        page.locator('.nav [data-view="'+v+'"]').click();page.wait_for_timeout(200)
        for k,expected in reference.items():
            actual=page.locator(k).bounding_box()
            check('fixed region '+v+' '+k,all(abs(actual[x]-expected[x])<2 for x in ['x','y','width','height']))
    page.locator('[data-task-filter="all"]').click();page.wait_for_timeout(250)
    check('all task count', '12' in page.locator('.task-filters').inner_text())
    page.locator('#search').fill('CAD');page.wait_for_timeout(400)
    check('search task', 'CAD' in page.locator('#viewBody').inner_text())
    page.locator('#search').fill('');page.wait_for_timeout(300)
    page.locator('[data-task]').first.click()
    check('task modal opens',page.locator('#detail').evaluate('(e)=>e.open'))
    page.locator('.previous-records summary').click()
    check('task history populated',page.locator('#detailHistory [data-history]').count()==3)
    page.locator('#closeConversation').click()
    page.locator('[data-info^="file-summary:"]').first.click()
    check('report summary opens',page.locator('#historyDetail').evaluate('(e)=>e.open'))
    check('report content nontrivial',len(page.locator('#historyDetail .info-body').inner_text())>200)
    page.locator('#closeHistory').click()
    page.locator('.nav [data-view="calendar"]').click();page.wait_for_timeout(200)
    check('42 calendar cells',page.locator('[data-day]').count()==42)
    page.locator('.calendar-scope [data-calendar-scope="history"]').click();page.wait_for_timeout(250)
    check('month history entries',page.locator('[data-history]').count()>0)
    page.locator('[data-history]').first.click()
    check('history snapshot accessible',page.locator('#historyDetail .snapshot').count()==1)
    page.locator('#closeHistory').click()
    page.screenshot(path=str(out/'calendar.png'))
    page.locator('#prevMonth').click();page.wait_for_timeout(150)
    check('month navigation',page.locator('#calendarMonth').input_value()!=str(today)[:7])
    page.locator('#calendarToday').click()
    page.locator('.nav [data-view="links"]').click();page.wait_for_timeout(250)
    links=[]
    for i in range(12):
        links.extend(page.locator('.link-card').evaluate_all('(ns)=>ns.map(n=>({url:n.href,target:n.target,rel:n.rel}))'))
        nxt=page.locator('[data-page="links"]').last
        if nxt.is_disabled():break
        nxt.click();page.wait_for_timeout(80)
    check('eight business links',len(links)==8)
    check('safe link attributes',all(x['url'].startswith('https://') and x['target']=='_blank' and 'noopener' in x['rel'] and 'noreferrer' in x['rel'] for x in links))
    page.locator('[data-link-remove]').first.click();page.locator('#showRemovedLinks').click();page.wait_for_timeout(120)
    check('link removal is local',page.locator('[data-link-restore]').count()==1)
    page.locator('[data-link-restore]').click();page.locator('#showRemovedLinks').click()
    page.locator('.sidebar-compose').click()
    probe='DEMO_MEMORY_ONLY <img src=x onerror=window.__xss=1>'
    page.locator('#conversationText').fill(probe);before=len(requests)
    page.locator('#sendConversation').click();page.wait_for_timeout(250)
    check('memory dialogue stored',probe in page.locator('#conversationThread').inner_text())
    check('no dialogue network transmission',len(requests)==before)
    check('dialogue escaped',page.locator('#conversationThread img').count()==0)
    page.locator('#closeConversation').click()
    page.locator('[data-help]').last.click()
    with page.expect_download() as d:page.locator('#guideBackup').click()
    download=d.value;download.save_as(str(out/'export.json'))
    payload=json.loads((out/'export.json').read_text())
    check('16 exported tasks',len(payload['tasks'])==16)
    check('20 events',len(payload['events'])==20)
    check('48 history records',len(payload['history'])==48)
    check('five existing and one entered dialogue',len(payload['messages'])==6)
    check('no browser storage accessed',page.evaluate('window.__storageAudit.length')==0)
    page.locator('#closeGuide').click()
    page.locator('[data-logout]').last.click();page.wait_for_load_state('networkidle')
    page.locator('.sidebar-compose').click()
    check('reload clears entered dialogue',probe not in page.locator('#conversationThread').inner_text())
    page.locator('#closeConversation').click()
    theme=page.locator('html').get_attribute('data-theme');page.locator('#themeToggle').click()
    check('theme switch',page.locator('html').get_attribute('data-theme')!=theme)
    page.locator('#themeToggle').click()
    page.locator('#sourceStatusButton').click()
    check('disconnected account notice',page.locator('#sourcePopover').evaluate('(e)=>e.matches(":popover-open")'))
    page.keyboard.press('Escape')
    page.set_viewport_size({'width':360,'height':800});page.wait_for_timeout(400)
    check('mobile no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
    page.screenshot(path=str(out/'mobile.png'))
    page.locator('#mobileView').select_option('calendar');page.wait_for_timeout(250)
    check('mobile calendar renders',page.locator('[data-day]').count()==42)
    page.locator('[data-mobile-panel="files"]').click();page.wait_for_timeout(150)
    check('mobile recent files visible',page.locator('.shared-files').is_visible())
    page.screenshot(path=str(out/'mobile-reports.png'))
    check('mobile final no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
    check('only local document and public weather requests',all(x['url'].startswith(url) or x['url'].startswith('https://api.open-meteo.com/') for x in requests))
    check('no POST or writes',all(x['method']=='GET' for x in requests))
    check('zero uncaught browser errors',not errors)
    browser.close()
finally:
 server.shutdown()
 result={'passed':len(checks),'checks':checks,'uncaught_errors':errors,'requests':requests,'sha256':hashlib.sha256(html.encode()).hexdigest(),'scope':'Chromium desktop 1440x1000 and mobile 360x800. Weather responses mocked for UI tests, not a live forecast verification. No real phones or production login tested.'}
 (out/'test-report.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(result,indent=2))
