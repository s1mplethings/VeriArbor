"""Preserve existing consumer and add the uncovered frozen M12 integration edges."""
from pathlib import Path
import ast, hashlib, json
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
old=R/'consumer-revisions/media-gui-v5.py'
new=R/'consumer-revisions/final-gui-integrity-v6.py'
helper=r'''
def assert_final_upload(status, record, expected_hash):
    require(status == 200 and record.get('id') and record.get('status') == 'VALID'
            and record.get('sha256') == expected_hash, 'GUI file upload must persist valid original bytes')

def assert_final_edit(before, after, approval, expected_text):
    require(len(before) == len(after) == 1, 'Saving selected content must edit rather than duplicate')
    require(after[0]['id'] == before[0]['id'] and after[0]['revision'] > before[0]['revision']
            and after[0]['text'] == expected_text, 'GUI semantic edit must preserve identity and advance revision')
    require(approval['content_id'] == after[0]['id'] and approval['revision'] == after[0]['revision']
            and approval['status'] == 'DRAFT', 'GUI semantic edit must invalidate current approval')

def assert_final_state(actual, expected):
    for key, rows in expected.items():
        require(key in actual and {x['id'] for x in actual[key]} == {x['id'] for x in rows},
                'Project-scoped state does not match persisted '+key)

def final_gui_integrity_probe():
    import base64
    from playwright.sync_api import sync_playwright
    image=scratch/'final-upload.png'
    image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a4gAAAABJRU5ErkJggg=='))
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    gui_data=scratch/'gui-integrity';url='http://127.0.0.1:'+str(port)
    argv=[sys.executable,'-X','utf8',str(workspace/'main.py'),'--serve','--port',str(port),'--data',str(gui_data)]
    def launch():
        proc=subprocess.Popen(argv,cwd=workspace,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(80):
            try:urllib.request.urlopen(url+'/health',timeout=.2).close();return proc
            except OSError:time.sleep(.1)
        proc.terminate();proc.wait(timeout=4);raise AssertionError('Final GUI startup failed')
    def stop(proc):
        proc.terminate()
        try:proc.wait(timeout=4)
        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=3)
    process=launch()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='msedge',headless=True)
            try:
                page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(url,wait_until='networkidle')
                def click_action(button,op):
                    with page.expect_response(lambda r:r.url.endswith('/api/action') and op in (r.request.post_data or '')) as result:
                        button.click()
                    page.wait_for_timeout(150)
                    return result.value
                page.get_by_label('Project name',exact=True).fill('Final integrity project')
                click_action(page.get_by_role('button',name='Create project',exact=True),'project.create')
                pid=http_action(url,'M1','project.list')['items'][0]['id']
                page.get_by_role('button',name='Media',exact=True).click()
                page.get_by_label('Media file',exact=True).set_input_files(str(image))
                upload=click_action(page.get_by_role('button',name='Import media',exact=True),'media.import')
                record=upload.json();assert_final_upload(upload.status,record,hashlib.sha256(image.read_bytes()).hexdigest())
                asset=page.request.get(url+'/media/'+record['id'],params={'project_id':pid})
                require(asset.ok and asset.body()==image.read_bytes(),'Imported media endpoint returned incorrect bytes')
                page.get_by_role('button',name='Campaigns',exact=True).click()
                page.get_by_label('Campaign name',exact=True).fill('Final integrity campaign')
                page.get_by_label('Audience',exact=True).fill('Developers')
                page.get_by_label('Channels',exact=True).fill('alpha,beta')
                click_action(page.get_by_role('button',name='Create campaign',exact=True),'campaign.create')
                source=scratch/'integrity-evidence';source.mkdir();(source/'README.md').write_text('Offline workflows are supported.',encoding='utf8')
                evidence=http_action(url,'M2','evidence.import',project_id=pid,path=str(source))
                claim=http_action(url,'M3','claim.create',project_id=pid,text='Offline workflows are supported.',evidence_ids=[evidence['id']])
                page.get_by_role('button',name='Content',exact=True).click()
                page.get_by_label('Content text',exact=True).fill('Offline workflows are supported.')
                page.get_by_label('Channel',exact=True).select_option('alpha')
                page.get_by_label('Claims',exact=True).select_option(label=claim['text'])
                page.get_by_label('Media',exact=True).select_option(record['id'])
                created=click_action(page.get_by_role('button',name='Save content',exact=True),'content.')
                require(created.ok,'GUI could not save attached content')
                before=http_action(url,'M5','content.list',project_id=pid)['items'];cid=before[0]['id']
                require(record['id'] in before[0]['media_ids'],'GUI did not attach selected media')
                page.locator('img:visible').first.wait_for(timeout=5000)
                require(page.locator('img:visible').first.evaluate('(e)=>e.complete && e.naturalWidth>0'),'Attached image not decoded')
                click_action(workflow_button(page,'Review').first,'approval.review')
                click_action(workflow_button(page,'Approve').first,'approval.approve')
                text='Offline workflows are supported. Edited.'
                page.get_by_label('Content text',exact=True).fill(text)
                edited=click_action(page.get_by_role('button',name='Save content',exact=True),'content.')
                require(edited.ok,'GUI could not edit current content')
                after=http_action(url,'M5','content.list',project_id=pid)['items']
                assert_final_edit(before,after,http_action(url,'M6','approval.status',project_id=pid,content_id=cid),text)
                expected={'campaigns':http_action(url,'M4','campaign.list',project_id=pid)['items'],
                          'contents':after,'receipts':http_action(url,'M7','publish.list',project_id=pid)['items'],
                          'schedules':http_action(url,'M8','schedule.list',project_id=pid)['items']}
                response=page.request.get(url+'/api/state',params={'project_id':pid})
                require(response.ok,'Project-scoped state endpoint failed');assert_final_state(response.json(),expected)
                foreign=http_action(url,'M1','project.create',name='Other project')['id']
                response=page.request.get(url+'/api/state',params={'project_id':foreign})
                require(response.ok,'Other project state failed');assert_final_state(response.json(),{k:[] for k in expected})
                require(page.request.get(url+'/media/'+record['id'],params={'project_id':foreign}).status in (400,404),'Foreign media leaked')
                require(page.request.get(url+'/api/state',params={'project_id':'unknown-project'}).status==400,'Unknown project must be rejected')
                require(not errors,'GUI initialization/action JavaScript errors: '+repr(errors))
                stop(process);process=launch();page.reload(wait_until='networkidle')
                require(http_action(url,'M5','content.list',project_id=pid)['items']==after,'Content changed across actual process restart')
                response=page.request.get(url+'/media/'+record['id'],params={'project_id':pid})
                require(response.ok and response.body()==image.read_bytes(),'Media bytes lost across process restart')
                page.screenshot(path=str(pathlib.Path.cwd()/'gui-final-integrity.png'),full_page=True)
            finally:browser.close()
    finally:stop(process)

'''
source=old.read_text(encoding='utf8')
needle='def milestone12():';assert source.count(needle)==1
source=source.replace(needle,helper+needle,1)
needle="    browser_probe('main.py',full=True)";assert source.count(needle)==1
source=source.replace(needle,needle+'\n    final_gui_integrity_probe()',1)
ast.parse(source)
with new.open('x',encoding='utf8') as out:out.write(source)
print(json.dumps({'path':str(new),'sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'activated':False,'scope':['M12'],'prior_assertions_preserved':True}))
