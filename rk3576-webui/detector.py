"""RKNNLite hardware inference; no conversion, training, or CPU fallback."""
from pathlib import Path
import time
import cv2
import numpy as np
from rknnlite.api import RKNNLite
import postprocess as pp

ROOT = Path(__file__).resolve().parent
cv2.setNumThreads(2)

class Detector:
    def __init__(self, confidence=0.25, iou=0.45):
        pp.OBJ_THRESH, pp.NMS_THRESH = confidence, iou
        self.model = RKNNLite(verbose=False)
        if self.model.load_rknn(str(ROOT/'models/yolov8n.rknn')) != 0:
            raise RuntimeError('Could not load YOLOv8n model')
        if self.model.init_runtime(core_mask=RKNNLite.NPU_CORE_AUTO) != 0:
            self.model.release()
            raise RuntimeError('RK3576 NPU initialization failed')

    def detect(self, frame):
        h,w = frame.shape[:2]
        scale = min(640/w,640/h)
        nw,nh = round(w*scale),round(h*scale)
        left,top = (640-nw)//2,(640-nh)//2
        canvas=np.full((640,640,3),114,np.uint8)
        canvas[top:top+nh,left:left+nw]=cv2.resize(frame,(nw,nh))
        rgb=cv2.cvtColor(canvas,cv2.COLOR_BGR2RGB)
        start=time.perf_counter()
        outputs=self.model.inference(inputs=[np.expand_dims(rgb,0)],data_format=['nhwc'])
        elapsed=time.perf_counter()-start
        if outputs is None or len(outputs)!=9:
            raise RuntimeError('NPU returned invalid YOLOv8 outputs')
        boxes,classes,scores=pp.post_process(outputs)
        results=[]
        if boxes is not None:
            boxes[:,[0,2]]=(boxes[:,[0,2]]-left)/scale
            boxes[:,[1,3]]=(boxes[:,[1,3]]-top)/scale
            boxes[:,[0,2]]=np.clip(boxes[:,[0,2]],0,w-1)
            boxes[:,[1,3]]=np.clip(boxes[:,[1,3]],0,h-1)
            for box,cls,score in zip(boxes,classes,scores):
                results.append({'box':[int(x) for x in box],'class':pp.CLASSES[int(cls)].strip(),'class_id':int(cls),'confidence':round(float(score),4)})
        return results,elapsed

    def close(self):
        self.model.release()

def annotate(frame, detections, npu_fps, processing_fps):
    h,w=frame.shape[:2]
    for d in detections:
        x1,y1,x2,y2=d['box']
        color=(80+(d['class_id']*47)%150,190,70+(d['class_id']*71)%170)
        cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
        label=f"{d['class']} {d['confidence']:.0%}"
        (tw,th),_=cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,.5,1)
        label_y=max(th+6,y1)
        cv2.rectangle(frame,(x1,label_y-th-6),(min(w-1,x1+tw+8),label_y+2),color,-1)
        cv2.putText(frame,label,(x1+4,label_y-3),cv2.FONT_HERSHEY_SIMPLEX,.5,(16,24,18),1,cv2.LINE_AA)
    overlay=f'RK3576 NPU | YOLOv8n | NPU {npu_fps:.1f} FPS | Pipeline {processing_fps:.1f} FPS'
    font_scale=min(.57,max(.25,(w-24)/900))
    cv2.rectangle(frame,(0,0),(w,36),(20,29,26),-1)
    cv2.putText(frame,overlay,(10,24),cv2.FONT_HERSHEY_SIMPLEX,font_scale,(140,240,180),1,cv2.LINE_AA)
    return frame
