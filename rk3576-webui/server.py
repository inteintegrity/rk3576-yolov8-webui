"""LAN WebUI, streaming uploads and single-job NPU worker; stdlib only."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
import json, time, threading, subprocess, sys, uuid, shutil, re, os, mimetypes, signal

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data';DATA.mkdir(exist_ok=True)
BUSY=threading.Lock()
MAX_UPLOAD=500*1024**2
for p in DATA.glob('*/status.json'):
    s=json.loads(p.read_text())
    if s['status'] in ['uploading','queued','loading','processing']:
        s.update(status='failed',message='The server restarted. Please upload the video again.')
        p.write_text(json.dumps(s))

def read_job(path):
    return json.loads((path/'status.json').read_text())

def worker(path):
    try:
        with (path/'worker.log').open('w') as log:
            result=subprocess.run([sys.executable,'-B',str(ROOT/'worker.py'),str(path)],stdout=log,stderr=log,timeout=7200)
        state=read_job(path)
        if result.returncode or state['status'] in ['queued','loading','processing']:
            state.update(status='failed',message='NPU worker stopped unexpectedly. See the application worker.log.')
            (path/'status.json').write_text(json.dumps(state))
    except Exception as exc:
        state=read_job(path);state.update(status='failed',message=str(exc));(path/'status.json').write_text(json.dumps(state))
    finally:BUSY.release()

class Handler(BaseHTTPRequestHandler):
    server_version='EdgeVision/1.0'
    def json_response(self,status,value):
        data=json.dumps(value).encode()
        self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)

    def job_path(self,token):
        if not re.fullmatch('[a-f0-9]{32}',token):raise FileNotFoundError()
        p=DATA/token
        if not (p/'status.json').exists():raise FileNotFoundError()
        return p

    def send_file(self,path,download=False):
        if not path.is_file():return self.json_response(404,{'error':'File is not ready or does not exist'})
        size=path.stat().st_size;start=0;end=size-1
        byte_range=self.headers.get('Range')
        if byte_range:
            m=re.fullmatch(r'bytes=(\d*)-(\d*)',byte_range)
            if not m:return self.json_response(416,{'error':'Invalid byte range'})
            a,b=m.groups()
            if not a and not b:return self.json_response(416,{'error':'Invalid byte range'})
            if a:start=int(a);end=min(int(b),size-1) if b else size-1
            else:start=max(0,size-int(b))
            if start>=size or end<start:
                self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.send_header('Content-Length','0');self.end_headers();return
        self.send_response(206 if byte_range else 200)
        self.send_header('Content-Type',mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1));self.send_header('Cache-Control','no-cache')
        if byte_range:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        if download:self.send_header('Content-Disposition','attachment; filename="yolov8-detected.mp4"')
        self.end_headers()
        if self.command=='HEAD':return
        with path.open('rb') as f:
            f.seek(start);remaining=end-start+1
            while remaining:
                block=f.read(min(256*1024,remaining))
                if not block:break
                self.wfile.write(block);remaining-=len(block)

    def do_HEAD(self):self.do_GET()

    def do_GET(self):
        try:
            url=urlparse(self.path);parts=url.path.strip('/').split('/')
            if url.path=='/api/health':
                probe=json.loads((ROOT/'probe.json').read_text())
                return self.json_response(200,{'ready':probe['npu_init']==0,'device':'RK3576','model':'YOLOv8n INT8','backend':'RKNNLite / NPU','busy':BUSY.locked(),'free_gb':round(shutil.disk_usage(DATA).free/1024**3,2),'max_upload_mb':500,'runtime':'2.3.0','toolkit_lite':'2.3.2','model_version_warning':'Model compiler 2.4.2; tested on existing runtime 2.3.0'})
            if url.path=='/api/jobs':
                jobs=[read_job(p.parent) for p in DATA.glob('*/status.json')]
                return self.json_response(200,sorted(jobs,key=lambda j:j['created_at'],reverse=True))
            if len(parts)>=3 and parts[:2]==['api','jobs']:
                p=self.job_path(parts[2])
                if len(parts)==3:return self.json_response(200,read_job(p))
                files={'video':'output.mp4','preview':'preview.jpg','detections':'detections.jsonl'}
                if parts[3] in files:
                    if parts[3]=='video' and read_job(p)['status']!='completed':return self.json_response(409,{'error':'Video is not complete'})
                    return self.send_file(p/files[parts[3]],download='download' in parse_qs(url.query))
            static={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
            if url.path in static:return self.send_file(ROOT/'static'/static[url.path])
            return self.json_response(404,{'error':'Not found'})
        except FileNotFoundError:self.json_response(404,{'error':'Run not found'})
        except (BrokenPipeError,ConnectionResetError):pass

    def do_POST(self):
        url=urlparse(self.path);parts=url.path.strip('/').split('/')
        if url.path!='/api/jobs':
            if len(parts)==4 and parts[:2]==['api','jobs'] and parts[3]=='cancel':
                try:p=self.job_path(parts[2]);(p/'cancel').touch();return self.json_response(200,{'ok':True})
                except FileNotFoundError:return self.json_response(404,{'error':'Run not found'})
            return self.json_response(404,{'error':'Not found'})
        self.connection.settimeout(300)
        try:
            length=int(self.headers.get('Content-Length','0'))
            name=Path(unquote(self.headers.get('X-Filename','video.mp4')).replace('\\','/')).name[:180]
            query=parse_qs(url.query);confidence=float(query.get('confidence',['0.25'])[0]);iou=float(query.get('iou',['0.45'])[0])
            if not 0.05<=confidence<=0.95 or not 0.1<=iou<=0.9:raise ValueError('Invalid confidence or IoU threshold')
            if not name.lower().endswith('.mp4'):raise ValueError('Choose an MP4 video')
            if not 0<length<=MAX_UPLOAD:return self.json_response(413,{'error':'Upload must be between 1 byte and 500 MB'})
            if shutil.disk_usage(DATA).free<length*3+750*1024**2:return self.json_response(507,{'error':'Insufficient space. Delete older runs to free storage.'})
        except (ValueError,OverflowError) as exc:return self.json_response(400,{'error':str(exc)})
        if not BUSY.acquire(blocking=False):return self.json_response(409,{'error':'The NPU is busy with another run. Please wait.'})
        p=DATA/uuid.uuid4().hex;p.mkdir()
        try:
            with (p/'input.mp4').open('wb') as f:
                remaining=length
                while remaining:
                    block=self.rfile.read(min(1024*1024,remaining))
                    if not block:raise ValueError('Upload was interrupted')
                    f.write(block);remaining-=len(block)
            with (p/'input.mp4').open('rb') as f:header=f.read(64)
            if b'ftyp' not in header:raise ValueError('The file is not a valid MP4 container')
            state={'id':p.name,'name':name,'status':'queued','message':'Video received. Starting NPU…','created_at':time.time(),'input_bytes':length,'confidence':confidence,'iou':iou,'progress':0,'frames':0,'detections':0,'classes':{}}
            (p/'status.json').write_text(json.dumps(state))
            threading.Thread(target=worker,args=(p,),daemon=True).start()
            return self.json_response(202,state)
        except Exception as exc:
            shutil.rmtree(p);BUSY.release();return self.json_response(400,{'error':str(exc)})

    def do_DELETE(self):
        parts=urlparse(self.path).path.strip('/').split('/')
        if len(parts)!=3 or parts[:2]!=['api','jobs']:return self.json_response(404,{'error':'Not found'})
        try:
            p=self.job_path(parts[2]);state=read_job(p)
            if state['status'] not in ['completed','failed','cancelled']:return self.json_response(409,{'error':'Cancel or finish this run before deleting it'})
            shutil.rmtree(p);return self.json_response(200,{'ok':True})
        except FileNotFoundError:return self.json_response(404,{'error':'Run not found'})

if __name__=='__main__':
    port=int(os.environ.get('PORT','8080'))
    server=ThreadingHTTPServer(('0.0.0.0',port),Handler)
    print(f'Edge Vision ready on http://0.0.0.0:{port}',flush=True)
    server.serve_forever()
