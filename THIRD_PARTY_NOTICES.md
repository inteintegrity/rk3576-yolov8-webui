# Third-party notices

The root `LICENSE` applies to original application code. The components and
media below are excluded from that MIT license and retain their respective
licenses and rights. The Rockchip-derived `postprocess.py` remains Apache-2.0.

## Precompiled YOLOv8n model

- Distributor: https://huggingface.co/RKNNAI/RK3576-CNN-yolov8n
- Revision: `5062767692fac53f9d69125abf8edf9d891bff4e`
- Upstream source cited by distributor: https://github.com/airockchip/ultralytics_yolov8
- License: GNU AGPL v3, preserved in `rk3576-webui/models/MODEL-LICENSE`
- Model configuration, provenance, and publisher README are preserved in `models/`.

## Rockchip inference example

- Source: https://github.com/airockchip/rknn_model_zoo/tree/v2.3.2/examples/yolov8
- License: Apache-2.0, preserved in `rk3576-webui/vendor/LICENSE`
- `vendor/yolov8.py` preserves the original example.
- `postprocess.py` adapts its filter, NMS, box decoding, and class labels; DFL uses
  NumPy instead of Torch and the original attribution is retained.
- `vendor/dog.jpg` is the upstream example's `model/bus.jpg`, retained as an
  inference test fixture. No independent ownership claim is made for the image.

## Test video and generated images

`video/test.mp4` is a user-provided test asset included at the project owner's
explicit request. The traffic detection sample in `verification/` is generated
from that video. Neither is represented as being licensed under the upstream
Rockchip code license. Any separate rights in these media remain with their
respective owners.
