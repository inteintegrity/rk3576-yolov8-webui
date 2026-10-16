from detector import Detector, annotate, ROOT
import cv2, json, time

model=Detector()
try:
 frame=cv2.imread(str(ROOT/'vendor/dog.jpg'))
 results=[]
 for _ in range(5):results,seconds=model.detect(frame)
 print(json.dumps({'npu_ms':round(seconds*1000,2),'detections':results},indent=2))
 assert any(d['class']=='bus' for d in results),'Expected bus detection in official test image'
 assert any(d['class']=='person' for d in results),'Expected person detection in official test image'
 annotate(frame,results,1/seconds,1/seconds)
 cv2.imwrite(str(ROOT/'smoke.jpg'),frame)
 (ROOT/'smoke.json').write_text(json.dumps({'npu_ms':seconds*1000,'detections':results,'backend':'RK3576 NPU'}))
 print('NPU SEMANTIC DETECTION CHECK PASSED',flush=True)
finally:model.close()
