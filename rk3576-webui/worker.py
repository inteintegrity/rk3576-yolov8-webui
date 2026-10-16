import json, sys, time, shutil, traceback
from pathlib import Path
from collections import Counter
import cv2
from detector import Detector, annotate

jobdir=Path(sys.argv[1]).resolve()
status_path=jobdir/'status.json'
state=json.loads(status_path.read_text())

def update(**fields):
    state.update(fields)
    temp=jobdir/'status.tmp'
    temp.write_text(json.dumps(state))
    temp.replace(status_path)

cap=writer=detector=None
try:
    update(status='loading',message='Initializing RK3576 NPU…')
    detector=Detector(state['confidence'],state['iou'])
    cap=cv2.VideoCapture(str(jobdir/'input.mp4'))
    if not cap.isOpened(): raise ValueError('This MP4 could not be decoded. Try an H.264 MP4 file.')
    fps=cap.get(cv2.CAP_PROP_FPS)
    if not 1<=fps<=240: raise ValueError('Video has an invalid frame rate')
    total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    source_w,source_h=int(cap.get(3)),int(cap.get(4))
    if min(source_w,source_h)<16 or source_w*source_h>3840*2160:
        raise ValueError('Video resolution must be between 16 pixels and 4K')
    scale=min(1,1280/source_w,720/source_h)
    w,h=int(source_w*scale)//2*2,int(source_h*scale)//2*2
    writer=cv2.VideoWriter(str(jobdir/'output.part.mp4'),cv2.VideoWriter_fourcc(*'avc1'),fps,(w,h))
    if not writer.isOpened(): raise RuntimeError('H.264 encoder could not start')
    update(status='processing',message='Detecting objects on the NPU',total_frames=total,source_fps=fps,width=w,height=h,source_width=source_w,source_height=source_h,backend='RKNNLite / RK3576 NPU')
    started=time.perf_counter(); count=0; npu_seconds=0; counts=Counter(); frames_with_detections=0
    with (jobdir/'detections.jsonl').open('w') as detection_log:
        while True:
            if (jobdir/'cancel').exists(): raise InterruptedError('Processing cancelled')
            ok,frame=cap.read()
            if not ok: break
            if frame.shape[1]!=w or frame.shape[0]!=h: frame=cv2.resize(frame,(w,h))
            detections,elapsed=detector.detect(frame)
            npu_seconds+=elapsed; count+=1
            counts.update(d['class'] for d in detections)
            frames_with_detections+=bool(detections)
            detection_log.write(json.dumps({'frame':count,'timestamp':(count-1)/fps,'detections':detections})+'\n')
            npu_fps=count/npu_seconds
            pipeline_fps=count/(time.perf_counter()-started)
            annotate(frame,detections,npu_fps,pipeline_fps)
            writer.write(frame)
            if count==1 or count%15==0:
                if shutil.disk_usage(jobdir).free<350*1024**2: raise RuntimeError('Storage is almost full. Delete old runs and try again.')
                ok,jpeg=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,78])
                if ok:
                    (jobdir/'preview.tmp').write_bytes(jpeg.tobytes()); (jobdir/'preview.tmp').replace(jobdir/'preview.jpg')
                update(frames=count,progress=min(99,round(100*count/max(total,1))),npu_fps=round(npu_fps,2),processing_fps=round(pipeline_fps,2),detections=sum(counts.values()),classes=dict(counts),elapsed_seconds=round(time.perf_counter()-started,2))
    writer.release();writer=None;cap.release();cap=None
    if count==0: raise ValueError('Video contains no decodable frames')
    if total>0 and count<total-2: raise ValueError(f'Video stopped decoding early ({count}/{total} frames). The file may be damaged.')
    # Confirm encoded video opens and seek/decode its final frame before publishing.
    check=cv2.VideoCapture(str(jobdir/'output.part.mp4'))
    encoded_count=int(check.get(cv2.CAP_PROP_FRAME_COUNT))
    check.set(cv2.CAP_PROP_POS_FRAMES,max(0,count-1));decoded,last=check.read();check.release()
    if not decoded or encoded_count!=count: raise RuntimeError('Encoded video verification failed')
    (jobdir/'output.part.mp4').replace(jobdir/'output.mp4')
    update(status='completed',message='Your detection video is ready',progress=100,frames=count,total_frames=count,npu_fps=round(count/npu_seconds,2),processing_fps=round(count/(time.perf_counter()-started),2),detections=sum(counts.values()),frames_with_detections=frames_with_detections,classes=dict(counts),elapsed_seconds=round(time.perf_counter()-started,2),output_bytes=(jobdir/'output.mp4').stat().st_size,completed_at=time.time(),duration_seconds=round(count/fps,3),audio='Output video is silent')
except Exception as exc:
    traceback.print_exc()
    update(status='cancelled' if isinstance(exc,InterruptedError) else 'failed',message=str(exc),completed_at=time.time())
finally:
    if cap is not None:cap.release()
    if writer is not None:writer.release()
    if detector is not None:detector.close()
    (jobdir/'output.part.mp4').unlink(missing_ok=True)
