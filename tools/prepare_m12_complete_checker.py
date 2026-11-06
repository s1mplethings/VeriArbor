from pathlib import Path
import ast, hashlib, json
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
source=R/'consumer-revisions/final-gui-integrity-v6.py'
text=source.read_text(encoding='utf8')
def replace(old,new):
    global text
    assert text.count(old)==1,(old[:80],text.count(old))
    text=text.replace(old,new)
idle='''def final_gui_idle_connection_probe():
    import importlib.util
    spec=importlib.util.spec_from_file_location('final_idle_probe',workspace/'main.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    folder=scratch/'idle-gui';folder.mkdir()
    server=module.ThreadedHTTPServer('127.0.0.1',0,str(folder))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    idle=socket.create_connection(('127.0.0.1',server.server_port),timeout=2)
    try:
        time.sleep(.1)
        try:
            with urllib.request.urlopen('http://127.0.0.1:'+str(server.server_port)+'/health',timeout=2) as response:
                require(json.load(response).get('status')=='ok','Concurrent health response invalid')
        except TimeoutError:
            raise AssertionError('Normal browser idle connection blocks GUI requests; server is serial')
    finally:
        idle.close();server.shutdown();server.server_close();thread.join(3)


'''
replace('def milestone12():\n',idle+'def milestone12():\n    final_gui_idle_connection_probe()\n')
needle="                text='Offline workflows are supported. Edited.'"
extra='''                with Platform() as platform:
                    page.get_by_label('Platform URL',exact=True).fill(platform.url)
                    page.get_by_role('button',name='Schedule/Publish',exact=True).click()
                    import datetime
                    when=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=1)).isoformat()
                    page.get_by_label('When (ISO8601)',exact=True).fill(when)
                    scheduled=click_action(page.get_by_role('button',name='Schedule',exact=True),'schedule.create')
                    require(scheduled.ok,'GUI schedule failed');sid=scheduled.json()['id']
                    later=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=2)).isoformat()
                    page.get_by_label('When (ISO8601)',exact=True).fill(later)
                    moved=click_action(page.get_by_role('button',name='Reschedule',exact=True),'schedule.reschedule')
                    require(moved.ok and moved.json()['id']==sid and moved.json()['when']==later,'GUI reschedule failed')
                    canceled=click_action(page.get_by_role('button',name='Cancel',exact=True),'schedule.cancel')
                    require(canceled.ok and canceled.json()['id']==sid and canceled.json()['status']=='CANCELLED','GUI cancel failed')
                    page.get_by_role('button',name='Content',exact=True).click()
                    published=click_action(workflow_button(page,'Publish').first,'publish.send')
                    require(published.ok,'GUI publish failed');receipt=published.json()
                    require(receipt['status']=='PUBLISHED' and receipt['content_id']==cid and receipt['revision']==before[0]['revision'],'GUI receipt binding invalid')
                    history=http_action(url,'M5','content.revisions',project_id=pid,content_id=cid)['items']
                    revision=next((r for r in history if r['revision']==receipt['revision']),None)
                    require(revision is not None and record['id'] in revision['media_ids'],'Receipt revision lost media binding')
                    duplicate=http_action(url,'M7','publish.send',project_id=pid,content_id=cid,platform_url=platform.url,idempotency_key=receipt['idempotency_key'])
                    require(duplicate['id']==receipt['id'] and len(platform.posts)==1,'Duplicate GUI receipt caused another POST')
                    stored=pathlib.Path(record['path']);original=stored.read_bytes()
                    for mode in ('changed','missing'):
                        if mode=='changed':stored.write_bytes(original+b'changed')
                        else:stored.unlink()
                        try:
                            rejected=page.request.post(url+'/api/action',data={'milestone':'M7','op':'publish.send','project_id':pid,'content_id':cid,'platform_url':platform.url,'idempotency_key':mode})
                            require(rejected.status==400 and len(platform.posts)==1,'Invalid media reached external POST')
                        finally:stored.write_bytes(original)
                    http_action(url,'M11','media.get',project_id=pid,media_id=record['id'])
'''
replace(needle,extra+needle)
needle2="                page.screenshot(path=str(pathlib.Path.cwd()/'gui-final-integrity.png'),full_page=True)"
extra2='''                restored=http_action(url,'M7','publish.list',project_id=pid)['items']
                require(any(r['id']==receipt['id'] and r['revision']==receipt['revision'] for r in restored),'Receipt lost on actual restart')
                page.get_by_role('button',name='Content',exact=True).click()
                require(page.get_by_label('Content text',exact=True).input_value()==text,'Selected content edit form did not restore persisted text')
                require(page.get_by_label('Media',exact=True).input_value()==record['id'],'Selected content media not restored')
                import re
                new_button=page.get_by_role('button',name=re.compile(r'^(new content|create new content|new draft)$',re.I))
                if new_button.count():new_button.first.click()
                else:
                    selection=page.get_by_label('Select content',exact=True)
                    require(selection.locator('option[value=""]').count()>0,'GUI has no way to create a second content item')
                    selection.select_option('')
                page.get_by_label('Content text',exact=True).fill('A second content item')
                second=click_action(page.get_by_role('button',name='Save content',exact=True),'content.create')
                require(second.ok,'Second content creation failed')
                final_rows=http_action(url,'M5','content.list',project_id=pid)['items']
                require(len(final_rows)==2 and any(r['id']==cid and r['text']==text for r in final_rows),'New content overwrote previous content')
'''
replace(needle2,extra2+needle2)
ast.parse(text)
target=R/'consumer-revisions/final-gui-complete-v7.py'
with target.open('x',encoding='utf8') as f:f.write(text)
old=json.loads((M/'M12_GUI_V6_QUALIFICATION.json').read_text(encoding='utf8'))
idle_result=json.loads((M/'m12-idle-connection-5f467864/receipt.json').read_text(encoding='utf8'))
actual,control=idle_result['observations']
assert actual['result']['responded'] is False and control['result']['responded'] is True
controls=old['controls']+[
 {'kind':'negative','name':'actual_serial_server_idle_connection','passed':not actual['result']['responded']},
 {'kind':'positive','name':'independent_threaded_server_same_handler','passed':control['result']['responded']},
]
report={'kind':'CompleteGuiObserverQualification','status':'PASS','controls':controls,
 'checker_hash':hashlib.sha256(target.read_bytes()).hexdigest(),'previous_checker_hash':hashlib.sha256(source.read_bytes()).hexdigest(),
 'scope':['M12'],'product_acceptance_granted':False,'qualification_only':True,
 'control_scope':'Prior upload/edit/state predicate controls plus real idle-connection negative and independent threaded same-handler positive. New full workflow driver is not claimed positive on current product.',
 'actual_negative_evidence':str(M/'m12-idle-connection-5f467864/receipt.json'),
 'actual_browser_evidence':str(M/'m12-final-product-143a2-selection-corrected/receipt.json'),
 'preserved_assertions':'Every v6 assertion retained. Adds ordinary idle socket responsiveness, actual scheduling, publish/media-bound revision/idempotency, changed/missing-media rejection before POST, receipt restart, edit-form hydration and second content creation. No simultaneous multi-select assumption.'}
with (M/'M12_GUI_V7_QUALIFICATION.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
print(json.dumps({'checker_hash':report['checker_hash'],'controls':len(controls),'product_acceptance_granted':False}))
