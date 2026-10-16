from pathlib import Path
import cv2, numpy as np, time, json
from rknnlite.api import RKNNLite
base=Path(__file__).resolve().parent
r=RKNNLite(verbose=True)
try:
 ret=r.load_rknn(str(base/'models/yolov8n.rknn')); print('LOAD',ret,flush=True)
 if ret: raise RuntimeError('Model load failed')
 ret=r.init_runtime(core_mask=RKNNLite.NPU_CORE_AUTO); print('INIT',ret,flush=True)
 if ret: raise RuntimeError('NPU init failed')
 img=cv2.imread(str(base/'vendor/dog.jpg'))
 img=cv2.cvtColor(cv2.resize(img,(640,640)),cv2.COLOR_BGR2RGB)
 t=time.perf_counter(); out=r.inference(inputs=[np.expand_dims(img,0)],data_format=['nhwc'])
 print('INFERENCE_MS',(time.perf_counter()-t)*1000,flush=True)
 print('OUTPUTS',[(x.shape,str(x.dtype),float(x.min()),float(x.max())) for x in out],flush=True)
 (base/'probe.json').write_text(json.dumps({'npu_init':ret,'outputs':[list(x.shape) for x in out]}))
finally:r.release()
