# Build an Edge AI App with Codex on reComputer RK3576

Learn how to use **Codex to build, deploy, and test an application on the Seeed
Studio reComputer RK3576 Dev Kit**, starting with a natural-language request and
an SSH connection to the board.

This hands-on walkthrough uses a YOLOv8 video detection WebUI as the example.
You define the goal and hardware constraints; Codex inspects the device, writes
the application, reuses the installed NPU dependencies, deploys over SSH, and
tests the result on real hardware. The repository contains the resulting app,
reusable prompts, a test video, and verification reports so you can follow the
workflow and check its outcome.

![Edge Vision WebUI running YOLOv8 object detection on RK3576](docs/images/webui-screenshot.png)

## What you will learn

- Give Codex a concrete application goal, device context, and acceptance criteria
- Connect your development PC to an RK3576 board over SSH and inspect its setup
- Ask Codex to reuse an existing RKNN environment and find a precompiled model
- Build a browser interface around an application running on the board's NPU
- Deploy, test, and fix the complete workflow using actual device results
- Package the working project, screenshots, and documentation for GitHub

The development flow in this example is:

```text
Your requirements → Codex on your PC → SSH → reComputer RK3576
                                              ↓
PC browser ← MP4 upload / annotated result ← YOLOv8n on the NPU
```

Codex assists with development on the PC. The deployed detection application
runs on the board, and its model inference runs on the RK3576 NPU. This app does
not call an OpenAI API to perform object detection.

## Before you start

- A reComputer RK3576 Dev Kit running Linux with a working NPU driver and RKNN
  Runtime. This example starts from an existing environment, rather than flashing
  the board or installing drivers.
- A development PC with Codex, access to a local project folder, and an SSH
  client or library available to its shell tools.
- Network access from the PC to the board and permission for Codex to run the
  required SSH commands. Use your own board IP and account.
- An MP4 test video. This repository includes [`video/test.mp4`](video/test.mp4).

Open this project folder in Codex on your PC. You can either study and deploy
the included implementation or use the prompts below to build your own version.
These are reusable prompts based on this project's workflow; the generated
implementation and performance can vary with your environment.

## Walkthrough: build the application with Codex

### 1. Connect and inspect before making changes

Start by giving Codex the board's connection details and requesting a read-only
inspection. Use an SSH key where available, or supply credentials for your own
device in the session without saving them in repository files.

```text
Connect to my reComputer RK3576 via SSH.

Host: <DEVICE_IP>
Username: <DEVICE_USER>
Use my SSH key, or ask me for the connection credentials you need.

Run read-only checks of the OS, CPU architecture, available memory and storage,
RKNN Runtime, Python environments, NPU driver and device access, and existing
YOLO models. Verify that remote commands execute successfully.

Do not install packages or modify system configurations yet.
Report the environment status and anything that could block deployment.
```

Review the report before continuing. In this project, the inspection identified
Debian 12 ARM64, an accessible RKNPU device, existing RKNNLite and OpenCV
dependencies, and limited root storage. Those findings shaped the implementation.

### 2. Describe the application and define completion

Give Codex the user experience, hardware requirements, and a testable outcome
in the same request:

```text
Build and deploy a YOLOv8 object detection WebUI on my reComputer RK3576 via SSH.

Download a precompiled RK3576-compatible YOLOv8n .rknn model from Rockchip's
official resources or a verified source. Record the source and verify the
published checksum. Do not convert or train models.

Use the RK3576 NPU for inference. Create a modern English WebUI where I can
upload an MP4 from my PC, run detection, and play or download the processed
video with bounding boxes, class labels, confidence scores, and FPS.

Reuse existing RKNN dependencies and official examples whenever possible.
Keep application files in a dedicated directory. Do not reinstall drivers or
modify system configurations without permission.

Test the complete workflow on the actual board, fix errors, and provide the
working WebUI URL, measured performance, and any remaining limitations.
```

In this run, Codex reused RKNNLite, adapted Rockchip's YOLOv8 postprocessing,
and built the web server using Python's standard library. The precompiled model
was downloaded and checksum-verified. A bus/person image test checked semantic
detections before moving on to video processing.

### 3. Verify the whole application on the board

Use the browser on your PC to upload `video/test.mp4`, run detection, and inspect
the result. A page that loads is only one part of the test. Ask Codex to verify
the entire path and provide evidence:

```text
Verify the deployed application end to end using video/test.mp4.

Check PC upload, NPU inference, progress updates, bounding boxes and class labels,
browser video playback, seeking, and downloading the processed MP4 back to the
PC. Confirm that all frames of the downloaded video decode successfully.

Also check invalid uploads, busy-device handling, cancellation, and storage
cleanup using disposable test runs. Fix any errors and rerun the affected checks.

Report NPU inference FPS separately from full video processing FPS. Save the
test results and document limitations and any runtime compatibility warnings.
```

The original build was tested with all 394 frames of the included 4K clip.
See [actual-device verification](#actual-device-verification) for measured results
and links to the saved reports. Review Codex's changes and verify the output
yourself before relying on a new deployment.

### 4. Refine and share the working project

After the application works, use follow-up requests to improve its presentation
or package it for others:

```text
Prepare this project for GitHub. Include the source code, model provenance,
licenses, deployment instructions, test reports, and the test video I authorize
you to upload. Exclude credentials, device logs, and user upload directories.

Add my WebUI screenshot to the README and explain how to reproduce this
Codex-assisted development workflow on another reComputer RK3576.
```

This sequence gives Codex device context, a bounded implementation task, and a
clear way to check completion. For more prompting guidance, see OpenAI's
[Codex best practices](https://learn.chatgpt.com/guides/best-practices).

## The example application

The resulting English WebUI lets you upload an MP4 from your PC, run object
detection on the board, and play or download an annotated H.264 MP4. It includes:

- Real RK3576 NPU inference using the existing RKNNLite installation
- Precompiled YOLOv8n INT8 model; no conversion or training
- Upload progress, processing previews, cancellation, and run history
- Adjustable confidence and IoU thresholds
- Browser playback, byte-range seeking, and annotated MP4 download
- Storage checks and deletion of old runs
- Python standard-library HTTP server; no additional web framework required

## Project layout

```text
rk3576-webui/       Device application, model, frontend, and deployment notes
video/test.mp4     Included source clip for end-to-end testing
verification/     Measured test reports and annotated example images
fetch_assets.py   Download upstream model/assets and verify model SHA-256
verify_webui.py   HTTP workflow and output-download checks
verify_lifecycle.py  Busy/cancel/delete lifecycle checks
```

## Run on RK3576

The tested device already has Python 3.11, RKNN Toolkit Lite2 2.3.2, OpenCV 4.6,
NumPy, RKNN Runtime 2.3.0, and NPU driver 0.9.8. Reuse these dependencies.

Copy `rk3576-webui/` to the device. For the original deployment:

```sh
cd /home/seeed/codex-yolov8-webui
# Verify real NPU inference before starting the WebUI:
/home/seeed/venvs/rknn-lite2-test/bin/python -B probe.py
sh start.sh
```

Open `http://<device-ip>:8080` from a PC on the same LAN. The original deployment
uses `http://192.168.3.120:8080`.

`start.sh` uses the existing Python environment at
`/home/seeed/venvs/rknn-lite2-test/bin/python`. Adjust that application script if
your device uses a different environment. No driver installer, system service,
firewall change, or system configuration change is included. Start manually again
after reboot. See [deployment documentation](rk3576-webui/README.md) for details.

## Actual-device verification

The included `video/test.mp4` was uploaded through the browser UI and processed
in full on the RK3576. The resulting video played in the browser, downloaded
successfully, and all downloaded frames decoded on the PC.

| Measurement | Result |
| --- | --- |
| Source | 3840 × 2160, 29.97 FPS, 394 frames |
| Output | H.264 MP4, 1280 × 720, 13.146 seconds |
| NPU inference throughput | 37.63 FPS |
| Complete video pipeline throughput | 7.89 FPS |
| Processing time | 49.92 seconds, excluding upload and NPU startup |
| Detection instances across frames | 7,769 |
| Observed classes | car, bus, truck, traffic light |

Inference FPS measures time inside RKNNLite inference. Pipeline FPS also includes
video decoding, preprocessing, postprocessing, drawing, and encoding. Detection
counts represent instances across frames, not unique tracked objects.

Invalid uploads, range requests, concurrent job rejection, cancellation, and
active-run deletion protection were also checked. See
[workflow report](verification/report.json) and
[lifecycle report](verification/lifecycle.json).

## Model provenance and licenses

The precompiled model comes from
[RKNNAI/RK3576-CNN-yolov8n](https://huggingface.co/RKNNAI/RK3576-CNN-yolov8n),
pinned to revision `5062767692fac53f9d69125abf8edf9d891bff4e`.
Its SHA-256 was verified against the publisher's checksum file:

```text
dcd13f14741074625ffbedd7829eaceede3d3faab6cd6a333be616829ac2d197
```

The original model license (AGPL-3.0), publisher documentation, and exact download
URL are preserved under [`rk3576-webui/models/`](rk3576-webui/models/).
Postprocessing is adapted from the official
[Rockchip Model Zoo v2.3.2 YOLOv8 example](https://github.com/airockchip/rknn_model_zoo/blob/v2.3.2/examples/yolov8/python/yolov8.py).
The original example and Apache-2.0 license are retained in
[`rk3576-webui/vendor/`](rk3576-webui/vendor/). NumPy replaces Torch for DFL.
See [third-party notices](THIRD_PARTY_NOTICES.md).

The model's embedded compiler version is 2.4.2 and the existing runtime is 2.3.0.
RKNN emits a version warning; the documented semantic and full-video tests passed
on the actual device without replacing the runtime.

## License

Original application code is licensed under the [MIT License](LICENSE).
Third-party components retain their existing licenses: the bundled YOLOv8n model
is AGPL-3.0, and the Rockchip example and derived postprocessing are Apache-2.0.
The MIT license does not replace these licenses or grant rights to the test video
or other third-party media. See [third-party notices](THIRD_PARTY_NOTICES.md).

## Limits

- Trusted LAN use; no login, TLS, or public exposure configuration
- MP4 uploads up to 500 MiB and input resolution up to 4K
- Output fits 1280 × 720 while preserving aspect ratio, source FPS, and duration
- Output video is silent; audio is not retained
- One processing job at a time; no CPU inference fallback
- Device uploads and results are runtime data and excluded from Git

The source test clip is included by the project owner's request. It is not
covered by the upstream code or model license notices.
