# Edge Vision for RK3576

English LAN WebUI for MP4 upload, real RK3576 NPU inference, progress previews,
H.264 annotated playback, seeking, downloads, and local run history.

Deployment: `/home/seeed/codex-yolov8-webui`

URL: http://192.168.3.120:8080

## Start and stop

```sh
cd /home/seeed/codex-yolov8-webui
sh start.sh
# Cancel/finish active runs in the WebUI before stopping:
python3 stop.py
```

The background process survives SSH disconnects. No boot service was installed:
run `sh start.sh` after a device reboot. Logs: `server.log`, `data/<id>/worker.log`.
Default port 8080; set `PORT` when starting to use another available port.

## Reused dependencies

- `/home/seeed/venvs/rknn-lite2-test/bin/python`, Python 3.11
- Existing RKNN Toolkit Lite2 2.3.2 and system `librknnrt.so` 2.3.0
- Existing NPU driver 0.9.8, OpenCV 4.6.0, NumPy, FFmpeg library H.264 encoder
- HTTP service uses Python standard library; no new pip or OS packages required

No drivers, system configuration, existing applications, or runtime files were
replaced. RKNNLite performs the neural network on the physical NPU; CPU handles
video codecs, letterboxing, Rockchip DFL/NMS postprocessing, and drawing. There
is no CPU inference fallback.

## Model and provenance

Downloaded precompiled **YOLOv8n 640×640 W8A8 for RK3576**, COCO 80 classes,
from https://huggingface.co/RKNNAI/RK3576-CNN-yolov8n

Pinned revision: `5062767692fac53f9d69125abf8edf9d891bff4e`.

SHA-256, checked against the publisher's `SHA256SUMS`:
`dcd13f14741074625ffbedd7829eaceede3d3faab6cd6a333be616829ac2d197`

`models/provenance.json` records the exact download URL. Publisher documentation,
configuration, published checksums, and AGPL-3.0 model license are in `models/`.
This is a third-party precompiled distribution referencing Rockchip's upstream
YOLOv8. No model was trained, exported, or converted during this deployment.

Publisher specifies RKNN 2.4.0; embedded metadata reports compiler 2.4.2.
The installed 2.3.0 runtime emits a version mismatch warning. Actual NPU model
loading, bus/person detection, and video processing are tested on this device;
no runtime upgrade was performed. Compatibility with other models is not implied.

`postprocess.py` adapts the official Rockchip Model Zoo v2.3.2 YOLOv8 decoder:
https://github.com/airockchip/rknn_model_zoo/blob/v2.3.2/examples/yolov8/python/yolov8.py
The upstream example and Apache-2.0 license are retained in `vendor/`. DFL was
rewritten in NumPy to avoid requiring Torch. Input is RGB uint8 NHWC with
aspect-preserving 114-value letterbox. All nine outputs use the official decoder.

## Usage and metrics

1. Open the WebUI from a PC on the same LAN.
2. Drop/browse an MP4, adjust confidence and IoU, and run detection.
3. Wait for completion, play/seek the output, or download the annotated MP4.
4. View past runs and delete their files to free storage.

- Upload limit: 500 MiB. Input resolution up to 4K. Outputs fit 1280×720 while
  preserving aspect ratio, frame rate, duration, and all decoded frames.
- Output is silent. Audio is not retained.
- Inference FPS counts NPU API inference time. Processing FPS counts decode,
  preprocessing, inference, postprocessing, drawing, and encoding. Overall
  upload time and NPU startup are excluded. FPS is processing throughput,
  independent of source playback FPS.
- Detection counts are instances across frames, not unique tracked objects.
- One run at a time. Jobs have a two-hour processing timeout and can be cancelled.
- Uploads/results remain on the device until deleted. Storage checks reserve
  space for the OS; delete older runs if storage becomes low.
- LAN application without login or TLS. It is intended for a trusted local
  network; no router, firewall, public access, or system service was configured.

## Verification

`probe.py` checks actual model loading and inference, `smoke.py` checks bus and
person detections against Rockchip's example image, and `data/<id>/status.json`
records per-run progress and metrics. Frame-level boxes, labels, and scores are
retained in `detections.jsonl` alongside each job.

### Actual device test, 2026-10-15

The PC's `video/test.mp4` was selected and submitted through the browser WebUI.
The complete upload, NPU processing, browser playback, seeking endpoints, and
download back to the PC passed. All downloaded frames also decoded on the PC.

| Measurement | Result |
| --- | --- |
| Input | 40,969,525 bytes, 3840×2160, 29.97 FPS |
| Frames processed / decoded after download | 394 / 394 |
| Output | H.264 MP4, 1280×720, 13.146 seconds, 9,493,964 bytes |
| NPU inference throughput | 37.63 FPS |
| Full processing throughput | 7.89 FPS |
| Processing duration | 49.92 seconds, excluding upload and model startup |
| Detection instances across frames | 7,769 |
| Classes observed | car, bus, truck, traffic light |
| Browser playback | 1280×720, readyState 4, no media error; playback time advanced |
| Output SHA-256 | `b735f2c76851c4f808f8799c66c88e40eff5b4c6653e42195a18aa396e220858` |

Additional checks passed: invalid extension/container rejection, HTTP byte-range
and suffix-range responses, invalid-range rejection, simultaneous-job rejection,
protection against deleting active runs, worker cancellation, and cleanup of
the disposable lifecycle test. The complete successful `test.mp4` run remains
available in Recent runs.
