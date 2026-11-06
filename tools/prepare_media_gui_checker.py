"""Add actual media preview checks to the existing independent GUI workflow."""
from pathlib import Path
import ast,hashlib,json
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
old=R/'consumer-revisions/media-integrity-v4.py'
new=R/'consumer-revisions/media-gui-v5.py'
source=old.read_text(encoding='utf8')
helper='''
def assert_media_preview(page, expected_image_hash, expected_video_hash):
    images = page.locator('img:visible')
    videos = page.locator('video:visible')
    require(images.count() > 0 and videos.count() > 0, 'Actual image and video preview elements required')
    def content_matches(elements, expected, video=False):
        for element in elements.all():
            if video and not element.evaluate('(e) => e.controls'):
                continue
            src = element.evaluate('(e) => e.currentSrc || e.src || (e.querySelector("source") || {}).src || ""')
            if not src.startswith(('http://127.0.0.1:', 'http://localhost:')):
                continue
            response = page.request.get(src)
            if not response.ok or hashlib.sha256(response.body()).hexdigest() != expected:
                continue
            if not video and not element.evaluate('(e) => e.complete && e.naturalWidth > 0'):
                continue
            return True
        return False
    require(content_matches(images, expected_image_hash), 'Image preview must display the imported bytes')
    require(content_matches(videos, expected_video_hash, True), 'Video preview must have controls and serve imported bytes')

'''
source=source.replace('def browser_probe(entry,full):',helper+'def browser_probe(entry,full):',1)
needle="                workflow_button(page,'Review').first.click()"
insert="""                if stage == 'M11':
                    attached_image = http_action(url,'M11','media.import',project_id=pid,path=str(scratch/'pixel.png'),kind='image')
                    attached_video = http_action(url,'M11','media.import',project_id=pid,path=str(scratch/'clip.mp4'),kind='video')
                    contents = http_action(url,'M5','content.list',project_id=pid)['items']
                    require(len(contents) == 1, 'Browser workflow lost its content identity')
                    http_action(url,'M5','content.edit',project_id=pid,content_id=contents[0]['id'],
                                text='Offline workflows are supported.',media_ids=[attached_image['id'],attached_video['id']])
                    page.reload(wait_until='networkidle')
                    page.get_by_text('Content',exact=True).first.click()
                    deadline=time.monotonic()+5
                    while time.monotonic()<deadline:
                        if page.locator('img:visible').count() and page.locator('video:visible').count():break
                        page.wait_for_timeout(100)
                    assert_media_preview(page,attached_image['sha256'],attached_video['sha256'])
"""
assert source.count(needle)==1;source=source.replace(needle,insert+needle)
needle="    with Platform() as platform:invalid(lambda:call('M7','publish.send',project_id=pid,content_id=cid,platform_url=platform.url,idempotency_key='broken'))"
assert source.count(needle)==1
source=source.replace(needle,needle+"\n    browser_probe('early_main.py',full=False)",1)
ast.parse(source)
with new.open('x',encoding='utf8') as f:f.write(source)
print(json.dumps({'path':str(new),'sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'activated':False,'scope':'M11 only; adds actual HTTP media dispatch and visible imported image/video bytes to original browser review/approve/publish workflow. GUI attachment controls still require final M12 manual/browser validation.'}))
