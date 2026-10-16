import requests, time, json
from pathlib import Path
s=requests.Session();s.trust_env=False;base='http://192.168.3.120:8080'
with open('verification/test-detected.mp4','rb') as video:
 r=s.post(base+'/api/jobs',data=video,headers={'X-Filename':'lifecycle-test.mp4'},timeout=60)
assert r.status_code==202,(r.status_code,r.text)
job=r.json();url=base+'/api/jobs/'+job['id']
r=s.post(base+'/api/jobs',data=b'ftyp',headers={'X-Filename':'busy.mp4'},timeout=10)
assert r.status_code==409,(r.status_code,r.text)
r=s.delete(url,timeout=10);assert r.status_code==409
r=s.post(url+'/cancel',timeout=10);r.raise_for_status()
for _ in range(25):
 state=s.get(url,timeout=10).json()
 if state['status'] in ['cancelled','failed','completed']:break
 time.sleep(1)
assert state['status']=='cancelled',state
s.delete(url,timeout=10).raise_for_status()
assert s.get(url,timeout=10).status_code==404
Path('verification/lifecycle.json').write_text(json.dumps({'passed':['busy rejection','active deletion protection','NPU worker cancellation','test run cleanup'], 'cancelled_status':state},indent=2),encoding='utf-8')
print('Lifecycle checks passed:',state['status'],flush=True)
