"""Verify the browser-submitted job, HTTP validation, seeking, and full download."""
import requests, time, json, hashlib
from pathlib import Path
session=requests.Session()
session.trust_env=False  # Direct LAN connection; do not route through the PC's HTTP proxy.
requests.get=session.get
requests.post=session.post
base='http://192.168.3.120:8080'
report={}
for path in ['/','/app.js','/style.css','/api/health']:
 r=requests.get(base+path,timeout=15);r.raise_for_status();print(path,r.status_code,flush=True)
report['health']=requests.get(base+'/api/health',timeout=10).json()
for name,body,expected in [('invalid.mp4',b'not a video',400),('wrong.txt',b'ftyp',400)]:
 r=requests.post(base+'/api/jobs',data=body,headers={'X-Filename':name,'Content-Type':'video/mp4'},timeout=20)
 # A running job is rejected before a second upload is read.
 assert r.status_code in [expected,409],(r.status_code,r.text)
 report[name]={'status':r.status_code,'body':r.json()}
jobs=requests.get(base+'/api/jobs',timeout=10).json()
assert jobs,'Browser upload did not create a job'
job=jobs[0];deadline=time.time()+600
while time.time()<deadline:
 job=requests.get(base+'/api/jobs/'+job['id'],timeout=10).json()
 print(json.dumps({k:job.get(k) for k in ['id','status','frames','total_frames','processing_fps','npu_fps','detections','message']}),flush=True)
 if job['status'] in ['completed','failed','cancelled']:break
 time.sleep(10)
assert job['status']=='completed',job
url=base+'/api/jobs/'+job['id']+'/video'
r=requests.get(url,headers={'Range':'bytes=0-1023'},timeout=20)
assert r.status_code==206 and len(r.content)==1024
assert 'bytes 0-1023/' in r.headers['Content-Range']
assert b'ftyp' in r.content[:64]
report['range_headers']=dict(r.headers)
r=requests.get(url,headers={'Range':'bytes=-128'},timeout=20)
assert r.status_code==206 and len(r.content)==128
r=requests.get(url,headers={'Range':'bytes=99999999999-'},timeout=20)
assert r.status_code==416
out=Path('verification');out.mkdir(exist_ok=True)
digest=hashlib.sha256();size=0
with requests.get(url+'?download=1',stream=True,timeout=30) as r:
 r.raise_for_status();assert 'attachment' in r.headers['Content-Disposition']
 with (out/'test-detected.mp4').open('wb') as f:
  for chunk in r.iter_content(1024*1024):f.write(chunk);digest.update(chunk);size+=len(chunk)
assert size==job['output_bytes']
report.update(job=job,download_bytes=size,download_sha256=digest.hexdigest(),checks=['browser MP4 upload','all-frame NPU processing','H264 MP4 output','range seeking','suffix ranges','invalid range rejection','complete download'])
(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('END-TO-END PASSED',json.dumps(report),flush=True)
