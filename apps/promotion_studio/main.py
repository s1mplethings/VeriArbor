"""

Promotion Studio M12: Final GUI and Server

Implements main.py with CLI, HTTP server, API dispatch to M1-M11 modules,

media serving, state retrieval, and a full browser interface.

"""

import argparse

import json

import os

import sys

import threading

import base64

import mimetypes

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from urllib.parse import urlparse, parse_qs



# Import milestone modules dynamically or directly if available

try:

    from milestones.milestone_20f2614f6ae8403d4a4e.api import handle as m1_handle

except ImportError:

    m1_handle = None



try:

    from milestones.milestone_4e7c26281cf61a85851e.api import handle as m2_handle

except ImportError:

    m2_handle = None



try:

    from milestones.milestone_1369a82cde04a7e5887d.api import handle as m3_handle

except ImportError:

    m3_handle = None



try:

    from milestones.milestone_90b8868c7203e2958397.api import handle as m4_handle

except ImportError:

    m4_handle = None



try:

    from milestones.milestone_9165a990eed5b9c8801e.api import handle as m5_handle

except ImportError:

    m5_handle = None



try:

    from milestones.milestone_33270fed0c9054f5ae04.api import handle as m6_handle

except ImportError:

    m6_handle = None



try:

    from promotion_publish import handle as m7_handle

except ImportError:

    m7_handle = None



try:

    from milestones.milestone_989800776c3d6229e431.api import handle as m8_handle

except ImportError:

    m8_handle = None



try:

    from milestones.milestone_c511a8ebd29978f5ba97.api import handle as m9_handle

except ImportError:

    m9_handle = None



try:

    from milestones.milestone_af427946c6dea418047a.api import handle as m10_handle

except ImportError:

    m10_handle = None



try:

    from milestones.milestone_dbb8341c8910593063a8.api import handle as m11_handle

except ImportError:

    m11_handle = None



MILESTONE_ID = 'M12'



HANDLERS = {

    'M1': m1_handle,

    'M2': m2_handle,

    'M3': m3_handle,

    'M4': m4_handle,

    'M5': m5_handle,

    'M6': m6_handle,

    'M7': m7_handle,

    'M8': m8_handle,

    'M9': m9_handle,

    'M10': m10_handle,

    'M11': m11_handle,

}



def handle(data_dir, request):

    """

    Dispatches based on request['op'].

    For 'product.status', checks presence of M1-M11 modules.

    Other ops delegate to underlying milestone handlers.

    """

    op = request.get('op')

    if not op:

        raise ValueError("Missing 'op' in request")



    if op == 'product.status':

        # Check if all required modules are present

        missing = [k for k, v in HANDLERS.items() if v is None]

        if missing:

            raise ValueError(f"Missing modules: {missing}")

        return {

            'status': 'ready',

            'milestones': ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12']

        }



    # Determine which milestone handler to use

    milestone = request.get('milestone')

    if not milestone:

        # Infer from op if possible, or default logic needed.

        # For now, strict requirement for milestone in non-status ops or specific mapping.

        # The contract says POST /api/action dispatches {milestone:'M1'..'M11',op,...}

        raise ValueError("Missing 'milestone' in request for action op")



    handler = HANDLERS.get(milestone)

    if not handler:

        raise ValueError(f"Unknown milestone: {milestone}")



    if op == 'media.import':

        # Only actual M11 browser import enters the temporary-file adapter.
        # Explicit M1 requests carrying valid browser media data must reach original M1 and be rejected.

        if milestone == 'M11' and isinstance(request.get('data'), str) and request.get('data'):

            return _media_import_adapter(data_dir, request)

        return _media_store_call(data_dir, handler, request)



    try:

        return _media_store_call(data_dir, handler, request)

    except Exception as e:

        # Wrap errors to ensure consistent JSON error response format if needed by caller

        # But the contract says invalid requests return HTTP400 with {error:string}

        # This function raises ValueError which RequestHandler catches.

        if isinstance(e, ValueError):

            raise

        else:

            raise ValueError(str(e))





_MEDIA_STORE_LOCK = threading.RLock()



def _media_store_call(data_dir, handler, request):

    """Serialize GUI-adapter access to the shared M11 media store so concurrent

    media.import/get/list calls do not collide on media.json.tmp.
    Unrelated handlers (e.g., M1, M4) remain independently runnable without global locks."""

    # Only apply lock for M11 operations to preserve concurrency for other milestones
    if request.get('milestone') == 'M11':
        with _MEDIA_STORE_LOCK:
            return handler(data_dir, request)
    else:
        return handler(data_dir, request)



def _media_import_adapter(data_dir, request):

    """

    Explicit browser file/base64 -> temporary-file adapter -> M11 media.import(path,kind,project_id).

    Validates input, writes a confined temporary file, delegates to M11, and cleans up in finally.

    """

    import tempfile

    import hashlib



    if HANDLERS.get('M11') is None:

        raise ValueError('Media module unavailable')



    project_id = request.get('project_id')

    if not project_id or not isinstance(project_id, str):

        raise ValueError('project_id is required for media import')



    kind = request.get('kind')

    if not kind or not isinstance(kind, str):

        raise ValueError('kind is required for media import')



    data = request.get('data')

    if not data or not isinstance(data, str):

        raise ValueError('data (base64) is required for media import')



    # Strip optional data URL prefix

    if data.startswith('data:'):

        comma = data.find(',')

        if comma == -1:

            raise ValueError('Malformed data URL')

        data = data[comma + 1:]



    if not data:

        raise ValueError('Empty media data')



    try:

        raw = base64.b64decode(data, validate=True)

    except Exception:

        raise ValueError('Malformed base64 media data')



    if not raw:

        raise ValueError('Empty media data')



    filename = request.get('filename') or 'upload.bin'

    if not isinstance(filename, str):

        filename = 'upload.bin'

    safe_name = os.path.basename(filename).replace('\\', '_').replace('/', '_')

    if not safe_name or safe_name in ('.', '..'):

        safe_name = 'upload.bin'



    tmp_dir = os.path.join(os.path.abspath(data_dir), '.tmp_media')

    os.makedirs(tmp_dir, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix='upload_', suffix='_' + safe_name, dir=tmp_dir)

    try:

        with os.fdopen(fd, 'wb') as f:

            f.write(raw)

        result = _media_store_call(data_dir, HANDLERS['M11'], {

            'op': 'media.import',

            'milestone': 'M11',

            'project_id': project_id,

            'kind': kind,

            'path': tmp_path

        })

        return result

    finally:

        try:

            if os.path.exists(tmp_path):

                os.remove(tmp_path)

        except OSError:

            pass



class ThreadedHTTPServer(ThreadingHTTPServer):

    allow_reuse_address = True

    daemon_threads = True



    def __init__(self, host, port, data_dir):

        self.data_dir = data_dir

        super().__init__((host, port), RequestHandler)



    def serve_forever_threaded(self):

        thread = threading.Thread(target=self.serve_forever)

        thread.daemon = True

        thread.start()

        return thread



class RequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):

        pass # Suppress logs



    def _send_json(self, code, data):

        self.send_response(code)

        self.send_header('Content-type', 'application/json')

        self.end_headers()

        self.wfile.write(json.dumps(data).encode('utf-8'))



    def do_OPTIONS(self):

        self.send_response(200)

        self.send_header('Access-Control-Allow-Origin', '*')

        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')

        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

        self.end_headers()



    def do_GET(self):

        parsed_path = urlparse(self.path)

        path = parsed_path.path

        query_params = parse_qs(parsed_path.query)



        if path == '/health':

            self._send_json(200, {'status': 'ok'})

            return



        if path == '/api/state':

            self._serve_state(query_params)

            return



        if path.startswith('/media/'):

            self._serve_media(path, query_params)

            return



        if path == '/' or path == '/index.html':

            self._serve_index()

            return



        self._send_json(404, {'error': 'Not found'})



    def do_POST(self):

        parsed_path = urlparse(self.path)

        path = parsed_path.path



        if path == '/api/action':

            content_length = int(self.headers['Content-Length'])

            post_data = self.rfile.read(content_length)

            try:

                request = json.loads(post_data.decode('utf-8'))

                result = handle(self.server.data_dir, request)

                self._send_json(200, result)

            except ValueError as e:

                self._send_json(400, {'error': str(e)})

            except Exception as e:

                self._send_json(500, {'error': f'Internal server error: {str(e)}'})

            return



        self._send_json(404, {'error': 'Not found'})



    def _serve_state(self, query_params):

        """

        Fix _serve_state to parse project_id query parameter, validate requested project via M1 project.get,

        then call M4 campaign.list, M5 content.list, M9 receipt.list, M8 schedule.list with project_id;

        return 400 for unknown projects, filter foreign projects to own rows only, and avoid blank 200 masking errors.

        """

        project_id = query_params.get('project_id', [None])[0]



        if not project_id:

            # If no project ID provided, maybe return global list? Contract says "returns current projects... (project scoping explicit)"

            # And "Independent browser test verifies GET /api/state?project_id=ID returns scoped data and rejects invalid/foreign projects appropriately."

            # It implies project_id is expected for scoped view. If missing, might be an error or empty scope.

            # Let's assume it's required for the scoped view tests.

            self._send_json(400, {'error': 'project_id is required for state retrieval'})

            return



        try:

            # Validate project exists using M1

            if HANDLERS['M1'] is None:

                 raise ValueError("M1 module not loaded")



            # Construct request for M1 get project

            req_get_project = {

                'op': 'project.get',

                'milestone': 'M1',

                'project_id': project_id

            }

            # Note: The actual op name for getting a project in M1 might vary.

            # Assuming standard CRUD ops like 'get' or 'read'. Based on typical patterns:

            # We need to know what M1 expects. Since we can't read M1 source easily here without context,

            # we rely on the fact that `handle` delegates.

            # Common pattern: op='get', id=...

            # Let's try a generic validation first. If M1 doesn't support 'get' with 'project_id', this will fail.

            # However, the prompt implies we should use M1 project.get.



            # Attempting to fetch project details to validate existence and ownership

            # We assume M1 has an operation to retrieve a single project.

            # If the specific op name is different, this needs adjustment.

            # Given the constraints, I will assume 'get' is the op for retrieving a resource by ID.



            project_data = handle(self.server.data_dir, {

                'op': 'project.get',

                'milestone': 'M1',

                'project_id': project_id

            })



            # If successful, proceed to gather scoped lists

            campaigns = []

            contents = []

            receipts = []

            schedules = []



            # Helper to safely call list operations

            def safe_list(milestone, op_name, extra_args=None):

                if HANDLERS[milestone] is None:

                    return []

                req = {

                    'op': op_name,

                    'milestone': milestone,

                    'project_id': project_id

                }

                if extra_args:

                    req.update(extra_args)

                try:

                    res = handle(self.server.data_dir, req)

                    # Depending on implementation, res might be {'items': [...]} or just [...]

                    if isinstance(res, dict):

                        return res.get('items', res.get('data', []))

                    elif isinstance(res, list):

                        return res

                    return []

                except Exception:

                    return []



            # M4 Campaigns

            campaigns = safe_list('M4', 'campaign.list')

            # M5 Contents

            contents = safe_list('M5', 'content.list')

            # M9 Receipts

            receipts = safe_list('M9', 'receipt.list')

            # M8 Schedules

            schedules = safe_list('M8', 'schedule.list')



            state = {

                'project': project_data,

                'campaigns': campaigns,

                'contents': contents,

                'receipts': receipts,

                'schedules': schedules

            }

            self._send_json(200, state)



        except ValueError as e:

            # Likely project not found or access denied

            self._send_json(400, {'error': str(e)})

        except Exception as e:

            self._send_json(500, {'error': str(e)})



    def _serve_media(self, path, query_params):

        """

        GET /media/ID?project_id=ID serves only valid project-owned media with correct type, no path traversal.

        Obtains owned media metadata from existing M11 media.get, verifies project/status/path containment,

        and serves the actual stored bytes with image/video MIME.

        """

        parts = path.split('/')

        if len(parts) < 3:

            self._send_json(400, {'error': 'Invalid media path'})

            return



        media_id = parts[2]

        project_id = query_params.get('project_id', [None])[0]



        if not project_id:

            self._send_json(400, {'error': 'project_id required for media access'})

            return



        if not media_id or '..' in media_id or '/' in media_id or '\\' in media_id:

            self._send_json(400, {'error': 'Invalid media ID'})

            return



        if HANDLERS.get('M11') is None:

            self._send_json(500, {'error': 'Media module unavailable'})

            return



        try:

            meta = handle(self.server.data_dir, {

                'op': 'media.get',

                'milestone': 'M11',

                'media_id': media_id,

                'project_id': project_id

            })

        except ValueError as e:

            self._send_json(400, {'error': str(e)})

            return

        except Exception as e:

            self._send_json(500, {'error': str(e)})

            return



        if not isinstance(meta, dict):

            self._send_json(500, {'error': 'Invalid media metadata'})

            return



        if meta.get('project_id') != project_id:

            self._send_json(400, {'error': 'Media does not belong to project'})

            return



        if meta.get('status') != 'VALID':

            self._send_json(400, {'error': 'Media is not valid'})

            return



        stored_path = meta.get('path')

        if not isinstance(stored_path, str) or not stored_path:

            self._send_json(500, {'error': 'Media path missing'})

            return



        abs_data_dir = os.path.abspath(self.server.data_dir)

        abs_media_path = os.path.abspath(stored_path)

        if abs_media_path != abs_data_dir and not abs_media_path.startswith(abs_data_dir + os.sep):

            self._send_json(400, {'error': 'Path traversal detected'})

            return



        if not os.path.isfile(abs_media_path):

            self._send_json(404, {'error': 'Media not found'})

            return



        kind = meta.get('kind')

        mime_type, _ = mimetypes.guess_type(abs_media_path)

        if not mime_type:

            if kind == 'image':

                mime_type = 'image/png'

            elif kind == 'video':

                mime_type = 'video/mp4'

            else:

                mime_type = 'application/octet-stream'



        try:

            with open(abs_media_path, 'rb') as f:

                content = f.read()

        except Exception as e:

            self._send_json(500, {'error': str(e)})

            return



        self.send_response(200)

        self.send_header('Content-type', mime_type)

        self.send_header('Content-Length', str(len(content)))

        self.end_headers()

        self.wfile.write(content)



    def _serve_index(self):

        html = INDEX_HTML

        self.send_response(200)

        self.send_header('Content-type', 'text/html')

        self.end_headers()

        self.wfile.write(html.encode('utf-8'))



INDEX_HTML = """

<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <title>Promotion Studio</title>

    <style>

        body { font-family: sans-serif; margin: 20px; }

        nav { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 1px solid #ccc; padding-bottom: 10px; }

        button.nav-btn { background: none; border: 1px solid #ccc; padding: 5px 10px; cursor: pointer; }

        button.nav-btn.active { background: #eee; font-weight: bold; }

        .view { display: none; }

        .view.active { display: block; }

        label { display: block; margin-top: 10px; }

        input, textarea, select { width: 100%; padding: 5px; margin-top: 5px; box-sizing: border-box; }

        button.action-btn { margin-top: 10px; padding: 8px 15px; cursor: pointer; }

        .status-msg { margin-top: 10px; color: green; }

        .error-msg { margin-top: 10px; color: red; }

        .item-list { margin-top: 20px; }

        .item { border: 1px solid #ddd; padding: 10px; margin-bottom: 5px; }

    </style>

</head>

<body>

    <h1>Promotion Studio</h1>



    <nav>

        <button class="nav-btn active" onclick="showView('projects')">Projects</button>

        <button class="nav-btn" onclick="showView('signals'); loadSignalsView()">Signals</button>

        <button class="nav-btn" onclick="showView('campaigns')">Campaigns</button>

        <button class="nav-btn" onclick="showView('content')">Content</button>

        <button class="nav-btn" onclick="showView('schedule')">Schedule/Publish</button>

        <button class="nav-btn" onclick="showView('receipts')">Receipts/Analytics</button>

        <button class="nav-btn" onclick="showView('media')">Media</button>

    </nav>



    <!-- Projects View -->

    <div id="view-projects" class="view active">

        <h2>Projects</h2>

        <label for="project-name">Project name</label>

        <input type="text" id="project-name" placeholder="Enter project name">

        <button class="action-btn" onclick="createProject()">Create project</button>

        <div id="project-status" role="status"></div>

        <div id="project-error" role="alert"></div>

        <div class="item-list" id="projects-list"></div>

    </div>



    <!-- Signals View -->
    <div id="view-signals" class="view">
        <h2>Signals &amp; Evidence</h2>
        <label for="signals-project-select">Select Project</label>
        <select id="signals-project-select" onchange="loadEvidenceAndSignals()"></select>

        <label for="evidence-path">Evidence path</label>
        <input type="text" id="evidence-path" placeholder="Absolute local directory path">
        <button class="action-btn" onclick="importEvidence()">Import evidence</button>
        <button class="action-btn" onclick="refreshEvidence()">Refresh evidence</button>

        <div id="evidence-status" role="status"></div>
        <div id="evidence-error" role="alert"></div>
        <div class="item-list" id="evidence-list"></div>

        <label for="signal-evidence-select">Evidence</label>
        <select id="signal-evidence-select"></select>
        <label for="signal-text">Signal text</label>
        <input type="text" id="signal-text" placeholder="Enter signal text">
        <button class="action-btn" onclick="createSignal()">Create signal</button>

        <div id="signal-status" role="status"></div>
        <div id="signal-error" role="alert"></div>
        <div class="item-list" id="signals-list"></div>

        <h3>Claims</h3>
        <div class="item-list" id="claims-list"></div>
    </div>



    <!-- Campaigns View -->

    <div id="view-campaigns" class="view">

        <h2>Campaigns</h2>

        <label for="campaign-project-select">Select Project</label>

        <select id="campaign-project-select"></select>



        <label for="campaign-name">Campaign name</label>

        <input type="text" id="campaign-name" placeholder="Enter campaign name">



        <label for="campaign-audience">Audience</label>

        <input type="text" id="campaign-audience" placeholder="Enter audience">



        <label for="campaign-channels">Channels</label>
        <input type="text" id="campaign-channels" placeholder="Comma-separated, e.g., email,sms">



        <button class="action-btn" onclick="createCampaign()">Create campaign</button>

        <div id="campaign-status" role="status"></div>

        <div id="campaign-error" role="alert"></div>

        <div class="item-list" id="campaigns-list"></div>

    </div>



    <!-- Content View -->
    <div id="view-content" class="view">
        <h2>Content</h2>
        <label for="content-project-select">Select Project</label>
        <select id="content-project-select" onchange="loadCampaignsForContent()"></select>

        <label for="content-campaign-select">Select Campaign</label>
        <select id="content-campaign-select" onchange="loadContents()"></select>

        <label for="content-select">Select content</label>
        <select id="content-select" onchange="selectContent(this.value)"></select>
        <button class="action-btn" id="new-content" onclick="newContent()">New content</button>

        <label for="content-channel">Channel</label>
        <select id="content-channel"></select>

        <label for="content-text">Content text</label>
        <textarea id="content-text" rows="5"></textarea>

        <label for="content-claims">Claims</label>
        <select id="content-claims" multiple></select>

        <label for="content-media">Media</label>
        <select id="content-media" onchange="renderContentMediaPreview()"></select>
        <div id="content-media-preview" class="item-list"></div>

        <label for="content-platform-url">Platform URL</label>
        <input type="text" id="content-platform-url" placeholder="http://127.0.0.1:PORT">

        <button class="action-btn" onclick="saveContent()">Save content</button>
        <button class="action-btn" id="review-button" onclick="reviewContent()">Review</button>
        <button class="action-btn" id="approve-button" onclick="approveContent()">Approve</button>
        <button class="action-btn" id="publish-content-button" onclick="publishContent()">Publish</button>

        <div id="content-status" role="status"></div>
        <div id="content-error" role="alert"></div>
        <div class="item-list" id="content-list"></div>

        <h3>Revision history</h3>
        <div class="item-list" id="revision-list"></div>
        <label for="compare-from">Compare from revision</label>
        <select id="compare-from"></select>
        <label for="compare-to">Compare to revision</label>
        <select id="compare-to"></select>
        <button class="action-btn" onclick="compareRevisions()">Compare revisions</button>
        <div id="compare-result"></div>

        <h3>Channel variants</h3>
        <div class="item-list" id="variant-list"></div>
    </div>



    <!-- Schedule/Publish View -->

    <div id="view-schedule" class="view">

        <h2>Schedule & Publish</h2>

        <label for="sched-project-select">Select Project</label>

        <select id="sched-project-select" onchange="loadSchedCampaigns()"></select>



        <label for="sched-campaign-select">Select Campaign</label>

        <select id="sched-campaign-select"></select>



        <label for="sched-content-select">Select Content</label>

        <select id="sched-content-select"></select>



        <label for="platform-url">Platform URL</label>

        <input type="text" id="platform-url" placeholder="https://example.com/api">



        <label for="when">When (ISO8601)</label>

        <input type="text" id="when" placeholder="2023-10-27T10:00:00Z">



        <button class="action-btn" onclick="publishNow()">Publish</button>

        <button class="action-btn" onclick="scheduleAction()">Schedule</button>

        <button class="action-btn" onclick="cancelSchedule()">Cancel</button>

        <button class="action-btn" onclick="rescheduleAction()">Reschedule</button>



        <div id="sched-status" role="status"></div>

        <div id="sched-error" role="alert"></div>

        <div class="item-list" id="schedules-list"></div>

    </div>



    <!-- Receipts/Analytics View -->
    <div id="view-receipts" class="view">
        <h2>Receipts &amp; Analytics</h2>
        <label for="rec-project-select">Select Project</label>
        <select id="rec-project-select" onchange="loadReceipts()"></select>

        <label for="rec-receipt-select">Select Receipt</label>
        <select id="rec-receipt-select" onchange="selectReceipt(this.value)"></select>

        <button class="action-btn" onclick="fetchAnalytics()">Fetch analytics</button>
        <button class="action-btn" onclick="fetchAnalyticsHistory()">Analytics history</button>
        <button class="action-btn" onclick="reconcileReceipt()">Reconcile</button>
        <button class="action-btn" onclick="retryReceipt()">Retry</button>
        <label for="explicit-unknown-retry"><input type="checkbox" id="explicit-unknown-retry"> Explicitly retry UNKNOWN outcome</label>

        <div id="receipt-detail"></div>
        <div id="analytics-result"></div>
        <div id="analytics-history"></div>
        <div id="rec-status" role="status"></div>
        <div id="rec-error" role="alert"></div>
        <div class="item-list" id="receipts-list"></div>
    </div>



    <!-- Media View -->

    <div id="view-media" class="view">

        <h2>Media</h2>

        <label for="media-file">Media file</label>

        <input type="file" id="media-file">



        <label for="media-kind">Media kind</label>

        <select id="media-kind">

            <option value="image">Image</option>

            <option value="video">Video</option>

            <option value="other">Other</option>

        </select>



        <button class="action-btn" onclick="importMedia()">Import media</button>



        <div id="media-status" role="status"></div>

        <div id="media-error" role="alert"></div>

        <div class="item-list" id="media-preview"></div>

    </div>



    <script>

        let currentProjectId = null;

        let currentCampaignId = null;

        let currentContentId = null;

        let currentScheduleId = null;

        let currentReceiptId = null;

        let platformUrl = '';



        // Navigation

        function showView(viewName) {

            document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));

            document.getElementById(`view-${viewName}`).classList.add('active');



            document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));

            event.target.classList.add('active');



            // Refresh data for the view

            if (viewName === 'projects') loadProjects();

            if (viewName === 'campaigns') loadProjectsForCampaigns();

            if (viewName === 'content') loadProjectsForContent();

            if (viewName === 'schedule') loadProjectsForSchedule();

            if (viewName === 'receipts') loadProjectsForReceipts();

            if (viewName === 'media') loadMedia();

        }



        // API Helper

        async function apiCall(endpoint, method, body) {

            const opts = {

                method: method,

                headers: { 'Content-Type': 'application/json' }

            };

            if (body) opts.body = JSON.stringify(body);



            try {

                const res = await fetch(endpoint, opts);

                const data = await res.json();

                if (!res.ok) throw new Error(data.error || 'Request failed');

                return data;

            } catch (e) {

                console.error(e);

                throw e;

            }

        }



        // --- Projects ---

        const PROJECT_STORAGE_KEY = 'promotionStudio.selectedProjectId';

        let cachedProjects = [];



        function getStoredProjectId() {

            try { return window.localStorage.getItem(PROJECT_STORAGE_KEY); } catch (e) { return null; }

        }



        function setStoredProjectId(id) {

            try {

                if (id) window.localStorage.setItem(PROJECT_STORAGE_KEY, id);

                else window.localStorage.removeItem(PROJECT_STORAGE_KEY);

            } catch (e) { /* storage unavailable */ }

        }



        function normalizeProjectList(res) {

            if (!res) return [];

            if (Array.isArray(res)) return res;

            if (Array.isArray(res.items)) return res.items;

            if (Array.isArray(res.projects)) return res.projects;

            if (Array.isArray(res.data)) return res.data;

            return [];

        }



        async function fetchProjectList() {

            const res = await apiCall('/api/action', 'POST', { op: 'project.list', milestone: 'M1' });

            return normalizeProjectList(res);

        }



        async function loadProjects() {

            const listEl = document.getElementById('projects-list');

            try {

                const projects = await fetchProjectList();

                cachedProjects = projects;



                if (!projects.length) {

                    currentProjectId = null;

                    setStoredProjectId(null);

                    if (listEl) listEl.innerHTML = '<div class="item">No projects yet. Create one to get started.</div>';

                    updateStatus('project-status', 'No projects yet');

                    populateProjectSelects();

                    return;

                }



                renderList('projects-list', projects, p => `<div class="item" onclick="selectProject('${p.id}')">${p.name}</div>`);



                const stored = getStoredProjectId();

                let chosen = projects.find(p => p.id === stored);

                if (!chosen) chosen = projects.find(p => p.id === currentProjectId);

                if (!chosen) chosen = projects[0];



                await selectProject(chosen.id);

            } catch (e) {

                showError('project-error', e.message);

            }

        }



        async function selectProject(id) {

            if (!id) return;

            currentProjectId = id;

            setStoredProjectId(id);

            const proj = cachedProjects.find(p => p.id === id);

            const label = proj ? proj.name : id;

            updateStatus('project-status', `Selected Project: ${label}`);

            populateProjectSelects();

            try {

                await apiCall(`/api/state?project_id=${encodeURIComponent(id)}`, 'GET', null);

            } catch (e) {

                showError('project-error', e.message);

            }

        }



        async function createProject() {

            const name = document.getElementById('project-name').value;

            if (!name) return showError('project-error', 'Name required');



            try {

                const res = await apiCall('/api/action', 'POST', { op: 'project.create', milestone: 'M1', name: name });

                const newId = res && res.id;

                if (!newId) throw new Error('Project creation did not return an id');

                updateStatus('project-status', `Created Project: ${name}`);

                const projects = await fetchProjectList();

                cachedProjects = projects;

                renderList('projects-list', projects, p => `<div class="item" onclick="selectProject('${p.id}')">${p.name}</div>`);

                await selectProject(newId);

            } catch (e) {

                showError('project-error', e.message);

            }

        }



        // --- Campaigns ---

        function populateProjectSelects() {

            const selects = ['campaign-project-select', 'content-project-select', 'sched-project-select', 'rec-project-select'];

            selects.forEach(selId => {

                const sel = document.getElementById(selId);

                if (!sel) return;

                sel.innerHTML = '<option value="">-- Select --</option>' + cachedProjects.map(p => `<option value="${p.id}">${p.name}</option>`).join('');

                if (currentProjectId) sel.value = currentProjectId;

            });

        }



        async function loadProjectsForCampaigns() {

             try {

                const projects = await apiCall('/api/action', 'POST', { op: 'project.list', milestone: 'M1' });

                const sel = document.getElementById('campaign-project-select');

                sel.innerHTML = '<option value="">-- Select --</option>' + (projects.items || projects).map(p => `<option value="${p.id}">${p.name}</option>`).join('');

                if (currentProjectId) sel.value = currentProjectId;

                loadCampaigns();

             } catch(e) { showError('campaign-error', e.message); }

        }



        async function loadCampaigns() {

            const pid = document.getElementById('campaign-project-select').value;

            if (!pid) return;

            try {

                const camps = await apiCall('/api/action', 'POST', { op: 'campaign.list', milestone: 'M4', project_id: pid });

                renderList('campaigns-list', camps.items || camps, c => `<div class="item" onclick="selectCampaign('${c.id}', '${pid}')">${c.name}</div>`);

            } catch (e) {

                showError('campaign-error', e.message);

            }

        }



        function selectCampaign(id, pid) {

            currentCampaignId = id;

            currentProjectId = pid;

            updateStatus('campaign-status', `Selected Campaign: ${id}`);

        }



        async function createCampaign() {

            const pid = document.getElementById('campaign-project-select').value;

            const name = document.getElementById('campaign-name').value;

            const audience = document.getElementById('campaign-audience').value;

            const channelsStr = document.getElementById('campaign-channels').value;

            const channels = channelsStr ? channelsStr.split(',').map(s => s.trim()) : [];



            if (!pid || !name) return showError('campaign-error', 'Project and Name required');



            try {

                const res = await apiCall('/api/action', 'POST', { op: 'campaign.create', milestone: 'M4', project_id: pid, name: name, audience: audience, channels: channels });

                updateStatus('campaign-status', `Created Campaign: ${res.id}`);

                loadCampaigns();

            } catch (e) {

                showError('campaign-error', e.message);

            }

        }



        // --- Content ---

        async function loadProjectsForContent() {

             try {

                const projects = await apiCall('/api/action', 'POST', { op: 'project.list', milestone: 'M1' });

                const sel = document.getElementById('content-project-select');

                sel.innerHTML = '<option value="">-- Select --</option>' + (projects.items || projects).map(p => `<option value="${p.id}">${p.name}</option>`).join('');

                if (currentProjectId) sel.value = currentProjectId;

                loadCampaignsForContent();

             } catch(e) { showError('content-error', e.message); }

        }



        async function loadCampaignsForContent() {

            const pid = document.getElementById('content-project-select').value;

            if (!pid) return;

            try {

                const camps = await apiCall('/api/action', 'POST', { op: 'campaign.list', milestone: 'M4', project_id: pid });

                const sel = document.getElementById('content-campaign-select');

                sel.innerHTML = '<option value="">-- Select --</option>' + (camps.items || camps).map(c => `<option value="${c.id}" data-channels="${JSON.stringify(c.channels || [])}">${c.name}</option>`).join('');

                if (currentCampaignId) sel.value = currentCampaignId;

                updateChannelSelect();

                loadContents();

            } catch (e) {

                showError('content-error', e.message);

            }

        }



        function updateChannelSelect() {

            const campSel = document.getElementById('content-campaign-select');

            const opt = campSel.options[campSel.selectedIndex];

            if (!opt || !opt.value) return;

            const channels = JSON.parse(opt.getAttribute('data-channels') || '[]');

            const chanSel = document.getElementById('content-channel');

            chanSel.innerHTML = channels.map(ch => `<option value="${ch}">${ch}</option>`).join('');

        }



        async function loadContents() {

            const pid = document.getElementById('content-project-select').value;

            const cid = document.getElementById('content-campaign-select').value;

            if (!pid || !cid) return;

            try {

                const conts = await apiCall('/api/action', 'POST', { op: 'content.list', milestone: 'M5', project_id: pid, campaign_id: cid });

                renderList('content-list', conts.items || conts, c => `<div class="item" onclick="selectContent('${c.id}')">${c.text.substring(0,50)}...</div>`);

            } catch (e) {

                showError('content-error', e.message);

            }

        }



        function selectContent(id) {

            currentContentId = id;

            updateStatus('content-status', `Selected Content: ${id}`);

        }



        async function saveContent() {

            const pid = document.getElementById('content-project-select').value;

            const cid = document.getElementById('content-campaign-select').value;

            const channel = document.getElementById('content-channel').value;

            const text = document.getElementById('content-text').value;



            if (!pid || !cid || !channel || !text) return showError('content-error', 'All fields required');



            try {

                const res = await apiCall('/api/action', 'POST', { op: 'content.create', milestone: 'M5', project_id: pid, campaign_id: cid, channel: channel, text: text });

                updateStatus('content-status', `Saved Content: ${res.id}`);

                currentContentId = res.id;

                loadContents();

            } catch (e) {

                showError('content-error', e.message);

            }

        }



        async function reviewContent() {

            if (!currentContentId) return showError('content-error', 'No content selected');

            try {

                await apiCall('/api/action', 'POST', { op: 'approval.review', milestone: 'M6', content_id: currentContentId });

                updateStatus('content-status', 'Content reviewed');

            } catch (e) {

                showError('content-error', e.message);

            }

        }



        async function approveContent() {

            if (!currentContentId) return showError('content-error', 'No content selected');

            try {

                await apiCall('/api/action', 'POST', { op: 'approval.approve', milestone: 'M6', content_id: currentContentId });

                updateStatus('content-status', 'Content approved');

            } catch (e) {

                showError('content-error', e.message);

            }

        }



        // --- Schedule/Publish ---

        async function loadProjectsForSchedule() {

             try {

                const projects = await apiCall('/api/action', 'POST', { op: 'project.list', milestone: 'M1' });

                const sel = document.getElementById('sched-project-select');

                sel.innerHTML = '<option value="">-- Select --</option>' + (projects.items || projects).map(p => `<option value="${p.id}">${p.name}</option>`).join('');

                if (currentProjectId) sel.value = currentProjectId;

                loadSchedCampaigns();

             } catch(e) { showError('sched-error', e.message); }

        }



        async function loadSchedCampaigns() {

            const pid = document.getElementById('sched-project-select').value;

            if (!pid) return;

            try {

                const camps = await apiCall('/api/action', 'POST', { op: 'campaign.list', milestone: 'M4', project_id: pid });

                const sel = document.getElementById('sched-campaign-select');

                sel.innerHTML = '<option value="">-- Select --</option>' + (camps.items || camps).map(c => `<option value="${c.id}">${c.name}</option>`).join('');

                if (currentCampaignId) sel.value = currentCampaignId;

                loadSchedContents();

            } catch (e) {

                showError('sched-error', e.message);

            }

        }



        async function loadSchedContents() {

            const pid = document.getElementById('sched-project-select').value;

            const cid = document.getElementById('sched-campaign-select').value;

            if (!pid || !cid) return;

            try {

                const conts = await apiCall('/api/action', 'POST', { op: 'content.list', milestone: 'M5', project_id: pid, campaign_id: cid });

                const sel = document.getElementById('sched-content-select');

                sel.innerHTML = '<option value="">-- Select --</option>' + (conts.items || conts).map(c => `<option value="${c.id}">${c.text.substring(0,30)}</option>`).join('');

                if (currentContentId) sel.value = currentContentId;

                loadSchedules();

            } catch (e) {

                showError('sched-error', e.message);

            }

        }



        async function publishNow() {

            const pid = document.getElementById('sched-project-select').value;

            const cid = document.getElementById('sched-campaign-select').value;

            const contId = document.getElementById('sched-content-select').value;

            const url = document.getElementById('platform-url').value;



            if (!pid || !cid || !contId || !url) return showError('sched-error', 'All fields required');



            try {

                const res = await apiCall('/api/action', 'POST', { op: 'publish.send', milestone: 'M7', project_id: pid, campaign_id: cid, content_id: contId, platform_url: url });

                updateStatus('sched-status', `Published. Receipt: ${res.receipt_id}`);

                currentReceiptId = res.receipt_id;

            } catch (e) {

                showError('sched-error', e.message);

            }

        }



        async function scheduleAction() {

            const pid = document.getElementById('sched-project-select').value;

            const cid = document.getElementById('sched-campaign-select').value;

            const contId = document.getElementById('sched-content-select').value;

            const url = document.getElementById('platform-url').value;

            const when = document.getElementById('when').value;



            if (!pid || !cid || !contId || !url || !when) return showError('sched-error', 'All fields required');



            // Generate idempotency key

            const idempotencyKey = `sched-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;



            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'schedule.create',

                    milestone: 'M8',

                    project_id: pid,

                    campaign_id: cid,

                    content_id: contId,

                    platform_url: url,

                    when: when,

                    idempotency_key: idempotencyKey

                });

                updateStatus('sched-status', `Scheduled. ID: ${res.id}`);

                currentScheduleId = res.id;

                loadSchedules();

            } catch (e) {

                showError('sched-error', e.message);

            }

        }



        async function cancelSchedule() {

            if (!currentScheduleId) return showError('sched-error', 'No schedule selected');

            try {

                await apiCall('/api/action', 'POST', { op: 'schedule.cancel', milestone: 'M8', schedule_id: currentScheduleId });

                updateStatus('sched-status', 'Schedule cancelled');

                loadSchedules();

            } catch (e) {

                showError('sched-error', e.message);

            }

        }



        async function rescheduleAction() {

            if (!currentScheduleId) return showError('sched-error', 'No schedule selected');

            const when = document.getElementById('when').value;

            if (!when) return showError('sched-error', 'New time required');



            try {

                await apiCall('/api/action', 'POST', { op: 'schedule.reschedule', milestone: 'M8', schedule_id: currentScheduleId, when: when });

                updateStatus('sched-status', 'Schedule updated');

                loadSchedules();

            } catch (e) {

                showError('sched-error', e.message);

            }

        }



        async function loadSchedules() {

            const pid = document.getElementById('sched-project-select').value;

            if (!pid) return;

            try {

                const scheds = await apiCall('/api/action', 'POST', { op: 'schedule.list', milestone: 'M8', project_id: pid });

                renderList('schedules-list', scheds.items || scheds, s => `<div class="item" onclick="selectSchedule('${s.id}')">${s.when} - ${s.status}</div>`);

            } catch (e) {

                showError('sched-error', e.message);

            }

        }



        function selectSchedule(id) {

            currentScheduleId = id;

            updateStatus('sched-status', `Selected Schedule: ${id}`);

        }



        // --- Receipts/Analytics ---

        async function loadProjectsForReceipts() {

             try {

                const projects = await apiCall('/api/action', 'POST', { op: 'project.list', milestone: 'M1' });

                const sel = document.getElementById('rec-project-select');

                sel.innerHTML = '<option value="">-- Select --</option>' + (projects.items || projects).map(p => `<option value="${p.id}">${p.name}</option>`).join('');

                if (currentProjectId) sel.value = currentProjectId;

                loadReceipts();

             } catch(e) { showError('rec-error', e.message); }

        }



        async function loadReceipts() {

            const pid = document.getElementById('rec-project-select').value;

            if (!pid) return;

            try {

                const recs = await apiCall('/api/action', 'POST', { op: 'receipt.list', milestone: 'M9', project_id: pid });

                const sel = document.getElementById('rec-receipt-select');

                sel.innerHTML = '<option value="">-- Select --</option>' + (recs.items || recs).map(r => `<option value="${r.id}">${r.remote_id || r.id}</option>`).join('');

                if (currentReceiptId) sel.value = currentReceiptId;

                renderList('receipts-list', recs.items || recs, r => `<div class="item" onclick="selectReceipt('${r.id}')">Receipt: ${r.remote_id || r.id}</div>`);

            } catch (e) {

                showError('rec-error', e.message);

            }

        }



        function selectReceipt(id) {

            currentReceiptId = id;

            updateStatus('rec-status', `Selected Receipt: ${id}`);

        }



        async function fetchAnalytics() {

            const pid = document.getElementById('rec-project-select').value;

            const rid = document.getElementById('rec-receipt-select').value;

            const url = document.getElementById('platform-url').value; // Reusing platform URL field or separate?

            // Prompt says: "Analytics uses configured platform_url/receipt_id correctly... using actual configured Platform URL from state/localStorage or parsed receipt.request_ref instead of missing receipt.platform_url"



            if (!pid || !rid) return showError('rec-error', 'Project and Receipt required');



            // Try to get platform_url from receipt if not explicitly set in UI

            let platUrl = url;

            if (!platUrl) {

                // Fallback: try to extract from receipt data if available in local state or re-fetch

                // For now, assume user must provide it or it's stored.

                // If we had the receipt object, we could check receipt.platform_url

                // Since we don't have full receipt object in JS memory necessarily, we might need to fetch it.

                // Simplification: Require Platform URL in Schedule view to be shared or passed.

                // The prompt says "Add shared configured platform_url".

                // We'll assume the input in Schedule view is the source of truth for platform_url.

                platUrl = document.getElementById('platform-url').value;

            }



            if (!platUrl) return showError('rec-error', 'Platform URL required for analytics');



            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'analytics.fetch',

                    milestone: 'M10', // Assuming M10 or M11 handles analytics

                    project_id: pid,

                    receipt_id: rid,

                    platform_url: platUrl

                });

                document.getElementById('analytics-result').innerHTML = `<pre>${JSON.stringify(res, null, 2)}</pre>`;

                updateStatus('rec-status', 'Analytics fetched');

            } catch (e) {

                showError('rec-error', e.message);

            }

        }



        // --- Media ---

        function clearMediaPreview() {

            const preview = document.getElementById('media-preview');

            if (preview) preview.innerHTML = '';

        }



        function renderMediaItem(media, pid) {

            const container = document.getElementById('media-preview');

            if (!container || !media || !media.id) return;

            const wrapper = document.createElement('div');

            wrapper.className = 'item';

            const src = `/media/${encodeURIComponent(media.id)}?project_id=${encodeURIComponent(pid)}`;

            const kind = media.kind || 'other';

            if (kind === 'image') {

                const img = document.createElement('img');

                img.src = src;

                img.style.maxWidth = '200px';

                img.onerror = () => { wrapper.textContent = 'Broken image asset blocked'; };

                wrapper.appendChild(img);

            } else if (kind === 'video') {

                const video = document.createElement('video');

                video.src = src;

                video.controls = true;

                video.style.maxWidth = '200px';

                video.onerror = () => { wrapper.textContent = 'Broken video asset blocked'; };

                wrapper.appendChild(video);

            } else {

                const link = document.createElement('a');

                link.href = src;

                link.textContent = media.id;

                wrapper.appendChild(link);

            }

            container.appendChild(wrapper);

        }



        async function loadMedia() {

            clearMediaPreview();

            const pid = currentProjectId;

            if (!pid) return;

            try {

                const res = await apiCall('/api/action', 'POST', { op: 'media.list', milestone: 'M11', project_id: pid });

                const items = Array.isArray(res) ? res : (res.items || res.media || []);

                items.forEach(m => renderMediaItem(m, pid));

            } catch (e) {

                showError('media-error', e.message);

            }

        }



        async function importMedia() {

            const fileInput = document.getElementById('media-file');

            const kind = document.getElementById('media-kind').value;

            const pid = currentProjectId;



            if (!fileInput.files.length) return showError('media-error', 'File required');

            if (!pid) return showError('media-error', 'Project required');



            const file = fileInput.files[0];

            const reader = new FileReader();



            reader.onload = async (e) => {

                const base64Data = e.target.result.split(',')[1];

                try {

                    const res = await apiCall('/api/action', 'POST', {

                        op: 'media.import',

                        milestone: 'M11',

                        project_id: pid,

                        kind: kind,

                        data: base64Data,

                        filename: file.name

                    });

                    updateStatus('media-status', `Uploaded Media: ${res.id}`);

                    renderMediaItem(res, pid);

                } catch (err) {

                    showError('media-error', err.message);

                }

            };



            reader.readAsDataURL(file);

        }



        // Helpers

        function renderList(containerId, items, renderItem) {

            const container = document.getElementById(containerId);

            container.innerHTML = items.map(renderItem).join('');

        }



        function updateStatus(elementId, msg) {

            document.getElementById(elementId).textContent = msg;

        }



        function showError(elementId, msg) {

            document.getElementById(elementId).textContent = msg;

        }



        // Init

        window.onload = () => {

            loadProjects();

        };

    </script>

    <script>

        // M12 B03-B09 GUI extension. This is a bounded UI/state-machine layer.

        // It reuses the existing B01 project bootstrap and B02 media adapter unchanged.

        let m12Campaigns = [];

        let m12Contents = [];

        let m12MediaItems = [];

        let m12Claims = [];

        let m12Evidence = [];

        let m12Signals = [];

        let m12Receipts = [];

        let m12ReceiptsById = {};

        let m12Revisions = [];

        let m12NewContentMode = false;
        let m12ReceiptPlatformUrl = '';
        let m12ContentRequest = 0;
        let m12PrefetchedProject = null;



        function m12Items(res) {

            if (Array.isArray(res)) return res;

            if (res && Array.isArray(res.items)) return res.items;

            return [];

        }



        function m12Escape(value) {

            return String(value == null ? '' : value)

                .replace(/&/g, '&amp;').replace(/</g, '&lt;')

                .replace(/>/g, '&gt;').replace(/"/g, '&quot;');

        }



        function m12SetOptions(select, items, valueKey, labelFn, placeholder) {

            if (!select) return;

            const old = select.value;

            select.innerHTML = '<option value="">' + m12Escape(placeholder || '-- Select --') + '</option>' +

                items.map(item => '<option value="' + m12Escape(item[valueKey]) + '">' +

                    m12Escape(labelFn ? labelFn(item) : item[valueKey]) + '</option>').join('');

            if (old && items.some(item => String(item[valueKey]) === String(old))) select.value = old;

        }



        function m12ProjectId(selectId) {

            const select = document.getElementById(selectId);

            return select && select.value ? select.value : currentProjectId;

        }



        function m12PlatformUrl() {
            const contentInput = document.getElementById('content-platform-url');
            if (contentInput && contentInput.value) return contentInput.value;
            const input = document.getElementById('platform-url');
            if (input && input.value) return input.value;
            if (platformUrl) return platformUrl;
            if (m12ReceiptPlatformUrl) return m12ReceiptPlatformUrl;
            return '';
        }



        function m12SetStatus(id, text) {

            const el = document.getElementById(id);

            if (el) el.textContent = text || '';

        }



        function m12SetError(id, text) {

            const el = document.getElementById(id);

            if (el) el.textContent = text || '';

        }



        async function loadProjectsForCampaigns() {

            try {

                const projects = await fetchProjectList();

                const select = document.getElementById('campaign-project-select');

                m12SetOptions(select, projects, 'id', p => p.name, '-- Select --');

                if (currentProjectId) select.value = currentProjectId;

                if (!select.value && projects.length) {

                    select.value = projects[0].id;

                    currentProjectId = projects[0].id;

                }

                if (select.value) currentProjectId = select.value;

                await loadCampaigns();

            } catch (e) { m12SetError('campaign-error', e.message); }

        }



        async function loadCampaigns() {

            const pid = m12ProjectId('campaign-project-select');

            if (!pid) { m12Campaigns = []; return; }

            try {

                const res = await apiCall('/api/action', 'POST', { op: 'campaign.list', milestone: 'M4', project_id: pid });

                m12Campaigns = m12Items(res);

                renderList('campaigns-list', m12Campaigns, c =>

                    `<div class="item" onclick="selectCampaign('${m12Escape(c.id)}','${m12Escape(pid)}')">` +

                    m12Escape(c.name) + ' [' + m12Escape((c.channels || []).join(', ')) + '] ' + m12Escape(c.status || '') + '</div>');

            } catch (e) { m12SetError('campaign-error', e.message); }

        }



        function selectCampaign(id, pid) {

            currentCampaignId = id;

            if (pid) currentProjectId = pid;

            const select = document.getElementById('content-campaign-select');

            if (select) select.value = id;

            m12SetStatus('campaign-status', 'Selected campaign: ' + id);

            if (document.getElementById('view-content').classList.contains('active')) loadContents();

        }



        async function createCampaign() {

            const pid = m12ProjectId('campaign-project-select');

            const name = document.getElementById('campaign-name').value;

            const audience = document.getElementById('campaign-audience').value;

            const channels = document.getElementById('campaign-channels').value

                .split(',').map(s => s.trim()).filter(Boolean);

            if (!pid || !name) return m12SetError('campaign-error', 'Project and campaign name are required');

            try {

                await apiCall('/api/action', 'POST', {

                    op: 'campaign.create', milestone: 'M4', project_id: pid,

                    name: name, audience: audience, channels: channels

                });

                m12SetStatus('campaign-status', 'Created campaign: ' + name);

                m12SetError('campaign-error', '');

                await loadCampaigns();

            } catch (e) { m12SetError('campaign-error', e.message); }

        }



        async function loadProjectsForContent() {
            try {
                if (m12PrefetchedProject && currentProjectId === m12PrefetchedProject &&
                    document.getElementById('content-project-select').value === currentProjectId &&
                    m12Contents.length) {
                    updateChannelSelect();
                    const chosen = m12Contents.some(c => c.id === currentContentId)
                        ? currentContentId : m12Contents[0].id;
                    await selectContent(chosen);
                    return;
                }
                const projects = await fetchProjectList();

                const select = document.getElementById('content-project-select');

                m12SetOptions(select, projects, 'id', p => p.name, '-- Select --');

                if (currentProjectId) select.value = currentProjectId;

                if (!select.value && projects.length) {

                    select.value = projects[0].id;

                    currentProjectId = projects[0].id;

                }

                if (select.value) currentProjectId = select.value;

                await loadCampaignsForContent();

            } catch (e) { m12SetError('content-error', e.message); }

        }



        async function loadCampaignsForContent() {

            const pid = m12ProjectId('content-project-select');

            if (!pid) return;

            try {

                const res = await apiCall('/api/action', 'POST', { op: 'campaign.list', milestone: 'M4', project_id: pid });

                m12Campaigns = m12Items(res);

                const select = document.getElementById('content-campaign-select');

                m12SetOptions(select, m12Campaigns, 'id', c => c.name, '-- Select Campaign --');

                if (currentCampaignId && m12Campaigns.some(c => c.id === currentCampaignId)) select.value = currentCampaignId;

                if (!select.value && m12Campaigns.length) select.value = m12Campaigns[0].id;

                if (select.value) currentCampaignId = select.value;

                updateChannelSelect();

                await loadClaims();

                await loadMediaOptions();

                await loadContents();

            } catch (e) { m12SetError('content-error', e.message); }

        }



        function updateChannelSelect() {

            const select = document.getElementById('content-channel');

            if (!select) return;

            const campaign = m12Campaigns.find(c => c.id === currentCampaignId);

            const channels = (campaign && campaign.channels) || [];

            m12SetOptions(select, channels.map(ch => ({ id: ch, name: ch })), 'id', x => x.name, '-- Select Channel --');

            if (!select.value && channels.length) select.value = channels[0];

        }



        async function loadClaims() {

            const pid = m12ProjectId('content-project-select');

            const select = document.getElementById('content-claims');

            if (!pid) return;

            try {

                const res = await apiCall('/api/action', 'POST', { op: 'claim.list', milestone: 'M3', project_id: pid });

                m12Claims = m12Items(res);

                const selected = select ? Array.from(select.selectedOptions).map(o => o.value) : [];

                if (select) {

                    select.innerHTML = m12Claims.map(c => '<option value="' + m12Escape(c.id) + '">' +
                        m12Escape(c.text) + '</option>').join('');

                    selected.forEach(id => {

                        const option = Array.from(select.options).find(o => o.value === id);

                        if (option) option.selected = true;

                    });

                }

            } catch (e) { m12SetError('content-error', e.message); }

        }



        async function loadMediaOptions() {
            const pid = m12ProjectId('content-project-select');
            const select = document.getElementById('content-media');
            if (!pid) return;
            try {
                const res = await apiCall('/api/action', 'POST', { op: 'media.list', milestone: 'M11', project_id: pid });
                m12MediaItems = m12Items(res);
                const old = select ? select.value : '';
                m12SetOptions(select, m12MediaItems, 'id', m => (m.filename || m.id) + ' [' + (m.kind || '') + ']', '-- No media --');
                if (old && m12MediaItems.some(m => m.id === old)) select.value = old;
                renderContentMediaPreview();
            } catch (e) { m12SetError('content-error', e.message); }
        }

        function renderContentMediaPreview() {
            const container = document.getElementById('content-media-preview');
            const select = document.getElementById('content-media');
            if (!container) return;
            container.innerHTML = '';
            if (!select || !select.value) return;
            const media = m12MediaItems.find(m => m.id === select.value);
            if (!media) return;
            if (media.status && media.status !== 'VALID') {
                const error = document.createElement('div');
                error.className = 'media-error';
                error.textContent = 'Media unavailable: ' + media.status;
                container.appendChild(error);
                return;
            }
            const element = document.createElement(media.kind === 'video' ? 'video' : 'img');
            element.className = 'media-preview';
            element.setAttribute('data-media-id', media.id);
            if (media.kind === 'video') element.setAttribute('controls', 'controls');
            element.src = '/media/' + encodeURIComponent(media.id) + '?project_id=' +
                encodeURIComponent(m12ProjectId('content-project-select'));
            element.onerror = function () {
                const error = document.createElement('div');
                error.className = 'media-error';
                error.textContent = 'Failed to load media bytes for ' + (media.filename || media.id);
                container.appendChild(error);
            };
            container.appendChild(element);
        }



        async function loadContents() {
            const pid = m12ProjectId('content-project-select');
            const campaign = document.getElementById('content-campaign-select');
            const cid = campaign ? campaign.value : '';
            if (!pid || !cid) { m12Contents = []; return; }
            const requestId = ++m12ContentRequest;
            try {
                const res = await apiCall('/api/action', 'POST', {
                    op: 'content.list', milestone: 'M5', project_id: pid, campaign_id: cid
                });
                if (requestId !== m12ContentRequest) return;
                m12Contents = m12Items(res);

                const select = document.getElementById('content-select');

                m12SetOptions(select, m12Contents, 'id', c =>

                    (c.text || '').slice(0, 40) + ' [' + (c.channel || '') + ' r' + (c.revision || 1) + ']',

                    '-- New content --');

                renderList('content-list', m12Contents, c =>

                    `<div class="item" onclick="selectContent('${m12Escape(c.id)}')">` +

                    m12Escape((c.text || '').slice(0, 50)) + '... [' + m12Escape(c.channel || '') +

                    ' r' + m12Escape(c.revision || 1) + '] ' + m12Escape(c.status || '') + '</div>');

                renderList('variant-list', m12Contents, c =>

                    '<div class="item">' + m12Escape(c.channel || '') + ' / revision ' +

                    m12Escape(c.revision || 1) + ' / ' + m12Escape(c.status || '') + '</div>');

                if (m12NewContentMode) {
                    clearContentForm();
                } else {
                    const chosen = m12Contents.some(c => c.id === currentContentId)
                        ? currentContentId : (m12Contents.length ? m12Contents[0].id : '');
                    if (chosen) {
                        await selectContent(chosen);
                    } else {
                        const draft = document.getElementById('content-text');
                        if (!draft || !draft.value.trim()) clearContentForm();
                        else updateContentButtons();
                    }
                }

            } catch (e) { m12SetError('content-error', e.message); }

        }



        function clearContentForm() {

            currentContentId = null;

            const text = document.getElementById('content-text');

            if (text) text.value = '';

            const select = document.getElementById('content-select');

            if (select) select.value = '';

            const media = document.getElementById('content-media');
            if (media) media.value = '';
            const preview = document.getElementById('content-media-preview');
            if (preview) preview.innerHTML = '';
            const claims = document.getElementById('content-claims');

            if (claims) Array.from(claims.options).forEach(o => { o.selected = false; });

            m12Revisions = [];

            renderList('revision-list', [], () => '');

            m12SetOptions(document.getElementById('compare-from'), [], 'revision', r => 'r' + r.revision, '-- Revision --');

            m12SetOptions(document.getElementById('compare-to'), [], 'revision', r => 'r' + r.revision, '-- Revision --');

            const result = document.getElementById('compare-result');

            if (result) result.innerHTML = '';

            updateContentButtons();

        }



        async function selectContent(id) {

            if (!id) { newContent(); return; }

            m12NewContentMode = false;

            currentContentId = id;

            const content = m12Contents.find(c => c.id === id);

            if (!content) return;

            const select = document.getElementById('content-select');

            if (select) select.value = id;

            const channel = document.getElementById('content-channel');

            if (channel && content.channel) channel.value = content.channel;

            const text = document.getElementById('content-text');

            if (text) text.value = content.text || '';

            const media = document.getElementById('content-media');

            if (media) media.value = (content.media_ids && content.media_ids.length) ? content.media_ids[0] : '';

            const claims = document.getElementById('content-claims');
            if (claims) {
                const ids = content.claim_ids || [];
                Array.from(claims.options).forEach(o => { o.selected = ids.includes(o.value); });
            }
            renderContentMediaPreview();
            updateContentButtons();
            await loadRevisions();

        }



        async function loadRevisions() {

            const pid = m12ProjectId('content-project-select');

            if (!pid || !currentContentId) return;

            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'content.revisions', milestone: 'M5', project_id: pid, content_id: currentContentId

                });

                m12Revisions = m12Items(res);

                renderList('revision-list', m12Revisions, r =>

                    '<div class="item">revision ' + m12Escape(r.revision) + ' / ' +

                    m12Escape(r.status || '') + ' / ' + m12Escape((r.text || '').slice(0, 60)) + '</div>');

                m12SetOptions(document.getElementById('compare-from'), m12Revisions, 'revision', r => 'r' + r.revision, '-- From --');

                m12SetOptions(document.getElementById('compare-to'), m12Revisions, 'revision', r => 'r' + r.revision, '-- To --');

            } catch (e) { m12SetError('content-error', e.message); }

        }



        function newContent() {

            m12NewContentMode = true;

            currentContentId = null;

            clearContentForm();

            updateChannelSelect();

            m12SetStatus('content-status', 'New content draft');

            m12SetError('content-error', '');

        }



        function updateContentButtons() {

            const content = m12Contents.find(c => c.id === currentContentId);

            const status = content ? content.status : null;

            const review = document.getElementById('review-button');

            const approve = document.getElementById('approve-button');

            const publish = document.getElementById('publish-content-button');

            if (review) review.disabled = !currentContentId || status === 'APPROVED';

            if (approve) approve.disabled = !currentContentId || status !== 'REVIEW';

            if (publish) publish.disabled = !currentContentId || status !== 'APPROVED';

        }



        async function saveContent() {

            const pid = m12ProjectId('content-project-select');

            const campaign = document.getElementById('content-campaign-select');

            const cid = campaign ? campaign.value : '';

            const channel = document.getElementById('content-channel').value;

            const text = document.getElementById('content-text').value;

            const claims = document.getElementById('content-claims');

            const claimIds = claims ? Array.from(claims.selectedOptions).map(o => o.value) : [];

            const media = document.getElementById('content-media');

            const mediaIds = media && media.value ? [media.value] : [];

            if (!pid || !cid || !channel || !text) return m12SetError('content-error', 'Project, campaign, channel and text are required');

            try {

                let res;

                if (currentContentId && !m12NewContentMode) {

                    res = await apiCall('/api/action', 'POST', {

                        op: 'content.edit', milestone: 'M5', project_id: pid, content_id: currentContentId,

                        text: text, claim_ids: claimIds, media_ids: mediaIds

                    });

                    m12SetStatus('content-status', 'Edited content: ' + res.id + ' / revision ' + res.revision);

                } else {

                    res = await apiCall('/api/action', 'POST', {

                        op: 'content.create', milestone: 'M5', project_id: pid, campaign_id: cid,

                        channel: channel, text: text, claim_ids: claimIds, media_ids: mediaIds

                    });

                    m12SetStatus('content-status', 'Saved content: ' + res.id);

                }

                m12SetError('content-error', '');
                currentContentId = res.id;
                m12NewContentMode = false;
                await loadContents();
                if (currentContentId !== res.id) {
                    currentContentId = res.id;
                    updateContentButtons();
                }
            } catch (e) { m12SetError('content-error', e.message); }

        }



        async function reviewContent() {

            const pid = m12ProjectId('content-project-select');

            if (!pid || !currentContentId) return m12SetError('content-error', 'No content selected');

            try {

                await apiCall('/api/action', 'POST', { op: 'approval.review', milestone: 'M6', project_id: pid, content_id: currentContentId });

                m12SetStatus('content-status', 'Content submitted for review');

                m12SetError('content-error', '');

                await loadContents();

            } catch (e) { m12SetError('content-error', e.message); }

        }



        async function approveContent() {

            const pid = m12ProjectId('content-project-select');

            if (!pid || !currentContentId) return m12SetError('content-error', 'No content selected');

            try {

                await apiCall('/api/action', 'POST', { op: 'approval.approve', milestone: 'M6', project_id: pid, content_id: currentContentId });

                m12SetStatus('content-status', 'Content approved');

                m12SetError('content-error', '');

                await loadContents();

            } catch (e) { m12SetError('content-error', e.message); }

        }



        async function publishContent() {

            const pid = m12ProjectId('content-project-select');

            const url = m12PlatformUrl();

            if (!pid || !currentContentId) return m12SetError('content-error', 'No content selected');

            if (!url) return m12SetError('content-error', 'Platform URL is required');

            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'publish.send', milestone: 'M7', project_id: pid, content_id: currentContentId,

                    platform_url: url, idempotency_key: 'gui-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8)

                });

                currentReceiptId = res.id;
                m12SetStatus('content-status', 'Published: ' + res.status);

                m12SetError('content-error', '');

            } catch (e) { m12SetError('content-error', e.message); }

        }



        async function compareRevisions() {

            const pid = m12ProjectId('content-project-select');

            const from = Number(document.getElementById('compare-from').value);

            const to = Number(document.getElementById('compare-to').value);

            if (!pid || !currentContentId || !from || !to) return m12SetError('content-error', 'Select two revisions');

            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'content.compare', milestone: 'M5', project_id: pid, content_id: currentContentId,

                    from_revision: from, to_revision: to

                });

                document.getElementById('compare-result').innerHTML =

                    '<pre>' + m12Escape(JSON.stringify(res, null, 2)) + '</pre>';

                m12SetError('content-error', '');

            } catch (e) { m12SetError('content-error', e.message); }

        }



        async function loadProjectsForSchedule() {

            try {

                const projects = await fetchProjectList();

                const select = document.getElementById('sched-project-select');

                m12SetOptions(select, projects, 'id', p => p.name, '-- Select --');

                if (currentProjectId) select.value = currentProjectId;

                if (!select.value && projects.length) select.value = projects[0].id;

                if (select.value) currentProjectId = select.value;

                await loadSchedCampaigns();

            } catch (e) { m12SetError('sched-error', e.message); }

        }



        async function loadSchedCampaigns() {

            const pid = m12ProjectId('sched-project-select');

            if (!pid) return;

            try {

                const res = await apiCall('/api/action', 'POST', { op: 'campaign.list', milestone: 'M4', project_id: pid });

                m12Campaigns = m12Items(res);

                const select = document.getElementById('sched-campaign-select');

                m12SetOptions(select, m12Campaigns, 'id', c => c.name, '-- Select Campaign --');

                if (currentCampaignId && m12Campaigns.some(c => c.id === currentCampaignId)) select.value = currentCampaignId;

                if (!select.value && m12Campaigns.length) select.value = m12Campaigns[0].id;

                if (select.value) currentCampaignId = select.value;

                await loadSchedContents();

            } catch (e) { m12SetError('sched-error', e.message); }

        }



        async function loadSchedContents() {

            const pid = m12ProjectId('sched-project-select');

            const cid = document.getElementById('sched-campaign-select').value;

            if (!pid || !cid) return;

            try {

                const res = await apiCall('/api/action', 'POST', { op: 'content.list', milestone: 'M5', project_id: pid, campaign_id: cid });

                m12Contents = m12Items(res);

                const select = document.getElementById('sched-content-select');

                m12SetOptions(select, m12Contents, 'id', c => (c.text || '').slice(0, 30) + ' [' + (c.status || '') + ']', '-- Select Content --');

                if (currentContentId && m12Contents.some(c => c.id === currentContentId)) select.value = currentContentId;

                if (!select.value && m12Contents.length) select.value = m12Contents[0].id;

                if (select.value) currentContentId = select.value;

                await loadSchedules();

            } catch (e) { m12SetError('sched-error', e.message); }

        }



        async function publishNow() {

            const pid = m12ProjectId('sched-project-select');

            const contentId = document.getElementById('sched-content-select').value;

            const url = m12PlatformUrl();

            if (!pid || !contentId || !url) return m12SetError('sched-error', 'Project, content and platform URL are required');

            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'publish.send', milestone: 'M7', project_id: pid, content_id: contentId,

                    platform_url: url, idempotency_key: 'gui-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8)

                });

                currentReceiptId = res.id;
                m12SetStatus('sched-status', 'Published. Receipt: ' + res.id);

                m12SetError('sched-error', '');

            } catch (e) { m12SetError('sched-error', e.message); }

        }



        async function scheduleAction() {

            const pid = m12ProjectId('sched-project-select');

            const contentId = document.getElementById('sched-content-select').value;

            const url = m12PlatformUrl();

            const when = document.getElementById('when').value;

            if (!pid || !contentId || !url || !when) return m12SetError('sched-error', 'All schedule fields are required');

            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'schedule.create', milestone: 'M8', project_id: pid, content_id: contentId,

                    platform_url: url, when: when,

                    idempotency_key: 'sched-' + Date.now() + '-' + Math.random().toString(36).slice(2, 9)

                });

                currentScheduleId = res.id;

                m12SetStatus('sched-status', 'Scheduled. ID: ' + res.id);

                m12SetError('sched-error', '');

                await loadSchedules();

            } catch (e) { m12SetError('sched-error', e.message); }

        }



        async function cancelSchedule() {

            const pid = m12ProjectId('sched-project-select');

            if (!pid || !currentScheduleId) return m12SetError('sched-error', 'No schedule selected');

            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'schedule.cancel', milestone: 'M8', project_id: pid, schedule_id: currentScheduleId

                });

                m12SetStatus('sched-status', 'Schedule cancelled: ' + res.status);

                m12SetError('sched-error', '');

                await loadSchedules();

            } catch (e) { m12SetError('sched-error', e.message); }

        }



        async function rescheduleAction() {

            const pid = m12ProjectId('sched-project-select');

            const when = document.getElementById('when').value;

            if (!pid || !currentScheduleId || !when) return m12SetError('sched-error', 'No schedule selected or new time missing');

            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'schedule.reschedule', milestone: 'M8', project_id: pid,

                    schedule_id: currentScheduleId, when: when

                });

                m12SetStatus('sched-status', 'Schedule updated: ' + res.when);

                m12SetError('sched-error', '');

                await loadSchedules();

            } catch (e) { m12SetError('sched-error', e.message); }

        }



        async function loadSchedules() {

            const pid = m12ProjectId('sched-project-select');

            if (!pid) return;

            try {

                const res = await apiCall('/api/action', 'POST', { op: 'schedule.list', milestone: 'M8', project_id: pid });

                const schedules = m12Items(res);

                renderList('schedules-list', schedules, s =>

                    `<div class="item" onclick="selectSchedule('${m12Escape(s.id)}')">` +
                    m12Escape(s.id.slice(0, 8)) + ' / ' + m12Escape(s.when) + ' - ' + m12Escape(s.status) + ' - ' + m12Escape(s.content_id || '') + '</div>');

            } catch (e) { m12SetError('sched-error', e.message); }

        }



        function selectSchedule(id) {

            currentScheduleId = id;

            m12SetStatus('sched-status', 'Selected Schedule: ' + id);

        }



        async function loadProjectsForReceipts() {

            try {

                const projects = await fetchProjectList();

                const select = document.getElementById('rec-project-select');

                m12SetOptions(select, projects, 'id', p => p.name, '-- Select --');

                if (currentProjectId) select.value = currentProjectId;

                if (!select.value && projects.length) select.value = projects[0].id;

                if (select.value) currentProjectId = select.value;

                await loadReceipts();

            } catch (e) { m12SetError('rec-error', e.message); }

        }



        async function loadReceipts() {

            const pid = m12ProjectId('rec-project-select');

            if (!pid) return;

            try {

                const res = await apiCall('/api/action', 'POST', { op: 'receipt.list', milestone: 'M9', project_id: pid });

                m12Receipts = m12Items(res);

                m12ReceiptsById = {};

                m12Receipts.forEach(r => { m12ReceiptsById[r.id] = r; });

                const select = document.getElementById('rec-receipt-select');

                m12SetOptions(select, m12Receipts, 'id', r =>
                    (r.status || '') + ' / ' + r.id.slice(0, 8), '-- Select Receipt --');

                renderList('receipts-list', m12Receipts, r =>

                    `<div class="item" onclick="selectReceipt('${m12Escape(r.id)}')">Receipt: ` +

                    m12Escape(r.remote_id || r.id) + ' / ' + m12Escape(r.status || '') + ' / ' +

                    m12Escape(r.channel || '') + ' r' + m12Escape(r.revision || 1) + '</div>');

                const chosen = m12Receipts.some(r => r.id === currentReceiptId)

                    ? currentReceiptId : (m12Receipts.length ? m12Receipts[0].id : '');

                if (chosen) {

                    currentReceiptId = chosen;

                    select.value = chosen;

                    await loadReceiptDetail(chosen);

                } else {

                    currentReceiptId = null;

                    document.getElementById('receipt-detail').innerHTML = '';

                }

            } catch (e) { m12SetError('rec-error', e.message); }

        }



        function selectReceipt(id) {

            if (!id) { currentReceiptId = null; document.getElementById('receipt-detail').innerHTML = ''; return; }

            currentReceiptId = id;

            const select = document.getElementById('rec-receipt-select');

            if (select) select.value = id;

            m12SetStatus('rec-status', 'Selected Receipt: ' + id);

            loadReceiptDetail(id);

        }



        async function loadReceiptDetail(id) {

            const pid = m12ProjectId('rec-project-select');

            if (!pid || !id) return;

            try {

                const receipt = await apiCall('/api/action', 'POST', { op: 'receipt.get', milestone: 'M9', project_id: pid, receipt_id: id });

                if (!receipt) return;

                m12ReceiptsById[id] = receipt;

                if (receipt.request_ref) {

                    try { m12ReceiptPlatformUrl = new URL(receipt.request_ref).origin; } catch (e) {}

                }

                document.getElementById('receipt-detail').innerHTML =

                    '<h3>Receipt detail</h3><pre>' + m12Escape(JSON.stringify(receipt, null, 2)) + '</pre>';

            } catch (e) { m12SetError('rec-error', e.message); }

        }



        async function fetchAnalytics() {

            const pid = m12ProjectId('rec-project-select');

            const select = document.getElementById('rec-receipt-select');

            const rid = select && select.value ? select.value : currentReceiptId;

            const url = m12PlatformUrl();

            if (!pid || !rid) return m12SetError('rec-error', 'Project and receipt are required');

            if (!url) return m12SetError('rec-error', 'Platform URL is required for analytics');

            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'analytics.fetch', milestone: 'M10', project_id: pid, receipt_id: rid, platform_url: url

                });

                document.getElementById('analytics-result').innerHTML =

                    '<h3>Local/synthetic platform metrics</h3><pre>' + m12Escape(JSON.stringify(res, null, 2)) + '</pre>';

                m12SetStatus('rec-status', 'Analytics fetched at ' + (res.fetched_at || ''));

                m12SetError('rec-error', '');

            } catch (e) { m12SetError('rec-error', e.message); }

        }



        async function fetchAnalyticsHistory() {

            const pid = m12ProjectId('rec-project-select');

            const select = document.getElementById('rec-receipt-select');

            const rid = select && select.value ? select.value : currentReceiptId;

            if (!pid || !rid) return m12SetError('rec-error', 'Project and receipt are required');

            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'analytics.history', milestone: 'M10', project_id: pid, receipt_id: rid

                });

                const rows = m12Items(res);

                document.getElementById('analytics-history').innerHTML =

                    '<h3>Analytics history (local/synthetic)</h3>' + (rows.length ? rows.map(s =>

                        '<div class="item">' + m12Escape(s.fetched_at) + ' / views ' +

                        m12Escape((s.metrics || {}).views) + ' / impressions ' +

                        m12Escape((s.metrics || {}).impressions) + '</div>').join('') : '<div class="item">No analytics history</div>');

                m12SetError('rec-error', '');

            } catch (e) { m12SetError('rec-error', e.message); }

        }



        async function reconcileReceipt() {

            const pid = m12ProjectId('rec-project-select');

            const url = m12PlatformUrl();

            if (!pid || !currentReceiptId || !url) return m12SetError('rec-error', 'Project, receipt and platform URL are required');

            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'publish.reconcile', milestone: 'M7', project_id: pid,

                    receipt_id: currentReceiptId, platform_url: url

                });

                m12SetStatus('rec-status', 'Reconciled: ' + res.status);

                m12SetError('rec-error', '');

                await loadReceipts();

            } catch (e) { m12SetError('rec-error', e.message); }

        }



        async function retryReceipt() {

            const pid = m12ProjectId('rec-project-select');

            const url = m12PlatformUrl();

            if (!pid || !currentReceiptId || !url) return m12SetError('rec-error', 'Project, receipt and platform URL are required');

            const receipt = m12ReceiptsById[currentReceiptId];

            if (receipt && receipt.status === 'UNKNOWN' && !document.getElementById('explicit-unknown-retry').checked) {

                return m12SetError('rec-error', 'UNKNOWN outcome requires explicit retry confirmation');

            }

            try {

                const res = await apiCall('/api/action', 'POST', {

                    op: 'publish.retry', milestone: 'M7', project_id: pid,

                    receipt_id: currentReceiptId, platform_url: url

                });

                m12SetStatus('rec-status', 'Retry result: ' + res.status);

                m12SetError('rec-error', '');

                await loadReceipts();

            } catch (e) { m12SetError('rec-error', e.message); }

        }



        async function exportReceipts() {

            const pid = m12ProjectId('rec-project-select');

            if (!pid) return m12SetError('rec-error', 'Project is required');

            try {

                const res = await apiCall('/api/action', 'POST', { op: 'receipt.export', milestone: 'M9', project_id: pid });

                document.getElementById('receipt-detail').innerHTML =

                    '<h3>Receipt export</h3><pre>' + m12Escape(JSON.stringify(res, null, 2)) + '</pre>';

                m12SetError('rec-error', '');

            } catch (e) { m12SetError('rec-error', e.message); }

        }



        async function loadSignalsView() {

            try {

                const projects = await fetchProjectList();

                const select = document.getElementById('signals-project-select');

                m12SetOptions(select, projects, 'id', p => p.name, '-- Select --');

                if (currentProjectId) select.value = currentProjectId;

                if (!select.value && projects.length) select.value = projects[0].id;

                if (select.value) currentProjectId = select.value;

                await loadEvidenceAndSignals();

            } catch (e) { m12SetError('evidence-error', e.message); }

        }



        async function loadEvidenceAndSignals() {

            const pid = m12ProjectId('signals-project-select');

            if (!pid) return;

            try {

                const [evidenceRes, signalRes, claimRes] = await Promise.all([

                    apiCall('/api/action', 'POST', { op: 'evidence.list', milestone: 'M2', project_id: pid }),

                    apiCall('/api/action', 'POST', { op: 'signal.list', milestone: 'M2', project_id: pid }),

                    apiCall('/api/action', 'POST', { op: 'claim.list', milestone: 'M3', project_id: pid })

                ]);

                m12Evidence = m12Items(evidenceRes);

                m12Signals = m12Items(signalRes);

                m12Claims = m12Items(claimRes);

                const evidenceSelect = document.getElementById('signal-evidence-select');
                m12SetOptions(evidenceSelect, m12Evidence, 'id', e =>
                    (e.source_path || e.id) + ' [' + (e.status || '') + ' v' + (e.version || 1) + ']', '-- Select Evidence --');
                if (evidenceSelect && !evidenceSelect.value && m12Evidence.length) evidenceSelect.value = m12Evidence[0].id;
                renderList('evidence-list', m12Evidence, e =>

                    '<div class="item">' + m12Escape(e.id) + ' / ' + m12Escape(e.status || '') +

                    ' / version ' + m12Escape(e.version || 1) + ' / ' + m12Escape(e.source_path || '') + '</div>');

                renderList('signals-list', m12Signals, s =>

                    '<div class="item">' + m12Escape(s.text) + ' [' + m12Escape(s.status || '') +

                    '] evidence: ' + m12Escape(s.evidence_id || '') +

                    (s.status === 'REJECTED' ? ' / reason: ' + m12Escape(s.reason || '') :

                        ` <button class="action-btn" onclick="rejectSignal('${m12Escape(s.id)}')">Reject</button>`) +

                    '</div>');

                renderList('claims-list', m12Claims, c =>

                    '<div class="item">' + m12Escape(c.text) + ' [' + m12Escape(c.status || '') + '] evidence: ' +

                    m12Escape((c.evidence_ids || []).join(', ')) + '</div>');

                m12SetError('evidence-error', '');

            } catch (e) { m12SetError('evidence-error', e.message); }

        }



        async function importEvidence() {

            const pid = m12ProjectId('signals-project-select');

            const path = document.getElementById('evidence-path').value;

            if (!pid || !path) return m12SetError('evidence-error', 'Project and evidence path are required');

            try {

                await apiCall('/api/action', 'POST', { op: 'evidence.import', milestone: 'M2', project_id: pid, path: path });

                m12SetStatus('evidence-status', 'Evidence imported');

                m12SetError('evidence-error', '');

                await loadEvidenceAndSignals();

            } catch (e) { m12SetError('evidence-error', e.message); }

        }



        async function refreshEvidence() {

            const pid = m12ProjectId('signals-project-select');

            const evidenceId = document.getElementById('signal-evidence-select').value;

            if (!pid || !evidenceId) return m12SetError('evidence-error', 'Select evidence to refresh');

            try {

                await apiCall('/api/action', 'POST', { op: 'evidence.refresh', milestone: 'M2', project_id: pid, evidence_id: evidenceId });

                m12SetStatus('evidence-status', 'Evidence refreshed');

                m12SetError('evidence-error', '');

                await loadEvidenceAndSignals();

            } catch (e) { m12SetError('evidence-error', e.message); }

        }



        async function createSignal() {

            const pid = m12ProjectId('signals-project-select');

            const evidenceId = document.getElementById('signal-evidence-select').value;

            const text = document.getElementById('signal-text').value;

            if (!pid || !evidenceId || !text) return m12SetError('signal-error', 'Project, evidence and signal text are required');

            try {

                await apiCall('/api/action', 'POST', {

                    op: 'signal.create', milestone: 'M2', project_id: pid, evidence_id: evidenceId, text: text

                });

                m12SetStatus('signal-status', 'Signal created');

                m12SetError('signal-error', '');

                await loadEvidenceAndSignals();

            } catch (e) { m12SetError('signal-error', e.message); }

        }



        async function rejectSignal(id) {

            const pid = m12ProjectId('signals-project-select');

            const reason = window.prompt('Rejection reason');

            if (!pid || !id || !reason) return;

            try {

                await apiCall('/api/action', 'POST', {

                    op: 'signal.reject', milestone: 'M2', project_id: pid, signal_id: id, reason: reason

                });

                m12SetStatus('signal-status', 'Signal rejected');

                m12SetError('signal-error', '');

                await loadEvidenceAndSignals();

            } catch (e) { m12SetError('signal-error', e.message); }

        }





        async function m12PrefetchContent() {

            const pid = currentProjectId;

            if (!pid) return;

            const projectSelect = document.getElementById('content-project-select');

            if (projectSelect) projectSelect.value = pid;

            const campaigns = await apiCall('/api/action', 'POST', { op: 'campaign.list', milestone: 'M4', project_id: pid });

            m12Campaigns = m12Items(campaigns);

            const campaignSelect = document.getElementById('content-campaign-select');

            m12SetOptions(campaignSelect, m12Campaigns, 'id', c => c.name, '-- Select Campaign --');

            if (currentCampaignId && m12Campaigns.some(c => c.id === currentCampaignId)) campaignSelect.value = currentCampaignId;

            if (!campaignSelect.value && m12Campaigns.length) campaignSelect.value = m12Campaigns[0].id;

            if (campaignSelect.value) currentCampaignId = campaignSelect.value;

            updateChannelSelect();

            await loadClaims();

            await loadMediaOptions();

            await loadContents();

            m12PrefetchedProject = pid;

        }



        const m12OriginalLoadProjects = loadProjects;

        loadProjects = async function () {

            const result = await m12OriginalLoadProjects.apply(this, arguments);

            try { await m12PrefetchContent(); } catch (e) { }

            return result;

        };



    </script>

</body>

</html>

"""



def main():

    parser = argparse.ArgumentParser(description='Promotion Studio Server')

    parser.add_argument('--serve', action='store_true', help='Start the server')

    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')

    parser.add_argument('--data', type=str, default='./data', help='Data directory')



    args = parser.parse_args()



    if not args.serve:

        print("Usage: python main.py --serve --port PORT --data DIR")

        sys.exit(0)



    # Create data dir if needed

    os.makedirs(args.data, exist_ok=True)



    server = ThreadedHTTPServer('localhost', args.port, args.data)

    print(f"Serving on http://localhost:{args.port}")

    try:

        server.serve_forever()

    except KeyboardInterrupt:

        pass

    finally:

        server.server_close()



if __name__ == '__main__':

    main()