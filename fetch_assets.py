from pathlib import Path
import requests, hashlib, json, concurrent.futures

ROOT=Path('rk3576-webui')
BASE='https://huggingface.co/RKNNAI/RK3576-CNN-yolov8n/resolve/5062767692fac53f9d69125abf8edf9d891bff4e/'
files={
 'models/yolov8n.rknn':BASE+'yolov8n-640x640-w8a8-1/yolov8n.rknn',
 'models/SHA256SUMS':BASE+'yolov8n-640x640-w8a8-1/SHA256SUMS',
 'models/model-config.json':BASE+'yolov8n-640x640-w8a8-1/config.json',
 'models/MODEL-LICENSE':BASE+'LICENSE',
 'models/MODEL-README.md':BASE+'README.md',
 'vendor/yolov8.py':'https://raw.githubusercontent.com/airockchip/rknn_model_zoo/v2.3.2/examples/yolov8/python/yolov8.py',
 'vendor/LICENSE':'https://raw.githubusercontent.com/airockchip/rknn_model_zoo/v2.3.2/LICENSE',
 'vendor/dog.jpg':'https://raw.githubusercontent.com/airockchip/rknn_model_zoo/v2.3.2/examples/yolov8/model/bus.jpg',
}
def fetch(pair):
 name,url=pair
 r=requests.get(url,timeout=60);r.raise_for_status()
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(r.content)
 print(name,len(r.content),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 for future in concurrent.futures.as_completed([pool.submit(fetch,item) for item in files.items()]):
  try: future.result()
  except Exception as e: print('DOWNLOAD ERROR:',e,flush=True)
p=ROOT/'models/yolov8n.rknn'
digest=hashlib.sha256(p.read_bytes()).hexdigest()
assert digest=='dcd13f14741074625ffbedd7829eaceede3d3faab6cd6a333be616829ac2d197',digest
(ROOT/'models/provenance.json').write_text(json.dumps({'repository':'https://huggingface.co/RKNNAI/RK3576-CNN-yolov8n','revision':'5062767692fac53f9d69125abf8edf9d891bff4e','url':files['models/yolov8n.rknn'],'sha256':digest,'download_only':True},indent=2))
print('MODEL SHA256 VERIFIED',digest)
