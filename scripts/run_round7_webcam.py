"""Run measured webcam PAD with locked E3_43; scene labels are user-declared."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import time

import cv2
import numpy as np
from PIL import Image
import torch
from torchvision.transforms import v2
import yaml

from deepface_pad.figure_inference import load_model
from deepface_pad.round7 import read, sha
from deepface_pad.webcam import MedianGate, yunet_boxes


def run(args):
    cfg = read(args.config)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    summary = {"status":"starting", "scenario":args.scenario,
               "scene_label_source":"user declaration; no independent scene verification",
               "started_utc":datetime.now(timezone.utc).isoformat(),
               "config":cfg, "config_sha256":sha(args.config),
               "environment":{"platform":platform.platform(), "cpu":platform.processor(),
                              "torch":torch.__version__, "opencv":cv2.__version__, "device":"cpu"},
               "probe_only":args.probe}
    cap = writer = None
    frames = []
    try:
        model = None
        if not args.probe:
            if cv2.__version__ != cfg.get("opencv_version",cv2.__version__):
                raise ValueError("OpenCV runtime differs from config; use the isolated demo-runtime PYTHONPATH in WEBCAM_GUIDE.md")
            audit = read("reports/ROUND_6_RESULTS_2026-10-22.json")
            if cfg["run_key"] != "E3_43":
                raise ValueError("demo must use preselected E3_43, not test-ranked seeds")
            record = audit["runs"][cfg["run_key"]]
            folder = Path(args.drive) / "runs" / record["run_id"]
            for name in ("best.ckpt", "config.yaml", "threshold.json"):
                if sha(folder/name) != record["hashes"][name]:
                    raise ValueError(f"changed frozen model artifact: {name}")
            model_cfg = yaml.safe_load((folder/"config.yaml").read_text(encoding="utf-8"))
            threshold = read(folder/"threshold.json")
            if (threshold["source"] != "validation" or cfg["threshold"] != threshold["threshold"]
                or cfg["normalization"] != model_cfg["data"]["normalization"]
                or cfg["image_size"] != model_cfg["data"]["image_size"]
                or model_cfg["model"]["name"] != "cdcn_official_head" or model_cfg["seed"] != 43):
                raise ValueError("demo differs from frozen model/threshold/preprocessing")
            if cfg["detector"] not in ("opencv_haar_frontalface_default","opencv_yunet_2023mar") or cfg["crop"] != "detected_rectangle_no_margin_clamped_to_frame":
                raise ValueError("unsupported detector/crop")
            torch.set_num_threads(cfg["torch_threads"])
            model = load_model({"folder":folder, "config":model_cfg}, torch.device("cpu"))
            summary["run_id"] = record["run_id"]
            summary["checkpoint_sha256"] = record["hashes"]["best.ckpt"]
            summary["frozen_config_sha256"] = record["hashes"]["config.yaml"]
            transform = v2.Compose([v2.ToImage(), v2.Resize((256,256)),
                                    v2.ToDtype(torch.float32,scale=True),
                                    v2.Normalize((.5,)*3,(128/255,)*3)])
            if cfg["detector"] == "opencv_haar_frontalface_default":
                cascade_path = Path(cv2.data.haarcascades)/"haarcascade_frontalface_default.xml"
                detector = cv2.CascadeClassifier(str(cascade_path))
                if detector.empty(): raise RuntimeError("face detector did not load")
                summary["detector_sha256"] = sha(cascade_path)
            else:
                detector_path = Path(cfg["detector_model"])
                if sha(detector_path) != cfg["detector_model_sha256"]:
                    raise ValueError("YuNet model hash differs from config")
                side = cfg["detector_input_side"]
                detector = cv2.FaceDetectorYN_create(str(detector_path),"",(side,side),
                    cfg["detector_score_threshold"],cfg["detector_nms_threshold"])
                summary["detector_sha256"] = sha(detector_path)
                summary["detector_resize"] = "Camera BGR resized to square 320 for detector only; boxes mapped back, PAD crop uses original frame."
            gate = MedianGate(cfg["threshold"], cfg["window_length"], cfg["maximum_gap_seconds"], cfg["minimum_tracking_iou"])
            with torch.inference_mode():
                for _ in range(cfg["warmup_forwards"]): model(torch.zeros(1,3,256,256))
        cap = cv2.VideoCapture(cfg["camera_index"])
        if not cap.isOpened(): raise RuntimeError("camera could not be opened")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,cfg["width"])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,cfg["height"])
        summary["camera"] = {"index":cfg["camera_index"], "backend":cap.getBackendName(),
                             "reported_width":cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                             "reported_height":cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                             "reported_fps_not_measured":cap.get(cv2.CAP_PROP_FPS)}
        for _ in range(cfg["camera_settle_reads"]):
            ok, _ = cap.read()
            if not ok: raise RuntimeError("camera settle read failed")
        if args.probe:
            summary["status"] = "PASS: camera open/read probe only; no FPS/PAD claim"
            return summary
        summary["start_mode"] = args.start_mode
        if args.start_mode == "space":
            if args.no_preview: raise ValueError("space start requires preview; use --start-mode automatic for no-preview")
            ready_at = time.perf_counter()
            while True:
                if time.perf_counter()-ready_at > 180:
                    raise RuntimeError("no Space key within 180 seconds; measurement not started")
                ok, ready_frame = cap.read()
                if not ok: raise RuntimeError("camera readiness read failed")
                cv2.putText(ready_frame,"READY - SPACE to measure / Q to cancel",(12,28),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,255,255),2)
                cv2.imshow("Round 7 PAD - Q to stop",ready_frame)
                key = cv2.waitKey(20) & 0xFF
                if key == ord("q"): raise RuntimeError("user cancelled before measurement")
                if key == 32: break
            summary["readiness_wait_seconds_excluded"] = time.perf_counter()-ready_at
        started = time.perf_counter()
        duration = args.seconds if args.seconds is not None else cfg["duration_seconds"]
        if duration <= 0: raise ValueError("duration must be positive")
        stopped_by_user = False
        with torch.inference_mode():
            while time.perf_counter()-started < duration:
                capture_started = time.perf_counter()
                ok, image = cap.read()
                read_ended = time.perf_counter()
                if not ok: raise RuntimeError("camera read failed during measurement")
                if cfg["detector"] == "opencv_haar_frontalface_default":
                    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
                    faces = detector.detectMultiScale(gray, scaleFactor=cfg["detector_scale_factor"],
                        minNeighbors=cfg["detector_min_neighbors"], minSize=(cfg["detector_min_size"],)*2)
                else:
                    side = cfg["detector_input_side"]
                    _, detections = detector.detect(cv2.resize(image,(side,side)))
                    faces = yunet_boxes(detections,image.shape[1],image.shape[0],side)
                detected_at = time.perf_counter()
                score, box, forward_ms = None, None, None
                if len(faces) == 1:
                    x,y,w,h = map(int,faces[0])
                    x,y = max(0,x),max(0,y)
                    w,h = min(w,image.shape[1]-x),min(h,image.shape[0]-y)
                    box = (x,y,w,h)
                    rgb = cv2.cvtColor(image[y:y+h,x:x+w],cv2.COLOR_BGR2RGB)
                    tensor = transform(Image.fromarray(rgb))[None]
                    forward_started = time.perf_counter()
                    score = float(model(tensor)["score"].reshape(-1)[0])
                    forward_ms = (time.perf_counter()-forward_started)*1000
                pad_ended = time.perf_counter()
                state = gate.update(score,box,capture_started,pad_ended,face_count=len(faces))
                decision_ended = time.perf_counter()
                if state["first_decision_seconds"] is not None:
                    state["first_decision_seconds"] = decision_ended-gate.started_at
                if box:
                    x,y,w,h = box
                    cv2.rectangle(image,(x,y),(x+w,y+h),(255,200,0),2)
                value = state["median_score"]
                label = f"{state['state']} {state['window_count']}/{cfg['window_length']}"
                if value is not None: label += f" median={value:.4f}"
                cv2.putText(image,label,(12,28),cv2.FONT_HERSHEY_SIMPLEX,.65,(0,255,255),2)
                if writer is None:
                    writer = cv2.VideoWriter(str(out/"backup.avi"),cv2.VideoWriter_fourcc(*"MJPG"),
                        cfg["recording_fps"],(image.shape[1],image.shape[0]))
                    if not writer.isOpened(): raise RuntimeError("backup video writer unavailable")
                    summary["actual_frame_shape"] = list(image.shape)
                writer.write(image)
                if not args.no_preview:
                    cv2.imshow("Round 7 PAD - Q to stop",image)
                    stopped_by_user = cv2.waitKey(1) & 0xFF == ord("q")
                ended = time.perf_counter()
                frames.append({"frame":len(frames), "capture_start_seconds":capture_started-started,
                    "read_end_seconds":read_ended-started, "detector_end_seconds":detected_at-started,
                    "pad_end_seconds":pad_ended-started, "decision_end_seconds":decision_ended-started,
                    "delivery_end_seconds":ended-started,
                    "face_count":len(faces), "bbox":json.dumps(box), "score":score,
                    "detector_scores":json.dumps(detections[:,-1].tolist() if cfg["detector"] != "opencv_haar_frontalface_default" and detections is not None else []),
                    "forward_ms":forward_ms, **state})
                if stopped_by_user: break
        elapsed = time.perf_counter()-started
        calls = sum(row["score"] is not None for row in frames)
        summary.update({"status":"measured", "elapsed_seconds":elapsed,
            "read_frames":len(frames), "model_processed_frames":calls,
            "delivered_loop_fps":len(frames)/elapsed,
            "model_processed_fps":calls/elapsed,
            "stopped_by_user":stopped_by_user,
            "ttd_seconds":[row["first_decision_seconds"] for row in frames if row["first_decision_seconds"] is not None],
            "timing_scope":"Serial read -> detect -> crop/transform -> PAD -> median -> annotation/video/preview. Loop FPS includes no-face frames; model FPS counts actual forwards. Excludes warm-up/settle and final file flushing. Not sensor capture FPS.",
            "ttd_definition":"First eligible read-call START to first full-window PAD/median decision; includes window acquisition, not physical face onset or sensor exposure latency.",
            "video_timing":"AVI uses fixed encoding FPS from config; CSV timestamps are authoritative real timing.",
            "tracking_limit":"IoU continuity heuristic cannot guarantee identity when faces swap at same location.",
            "scope":"Different domain/window from CASIA video mean; unchanged threshold is not calibrated for webcam; user-declared scenes are not benchmark labels."})
    except Exception as exc:
        summary.update({"status":"unavailable_or_incomplete", "error":f"{type(exc).__name__}: {exc}",
                        "partial_frames":len(frames)})
    finally:
        if cap is not None: cap.release()
        if writer is not None: writer.release()
        if not args.no_preview: cv2.destroyAllWindows()
        if frames:
            log_path = out/"frames.csv"
            with log_path.open("w",newline="",encoding="utf-8") as stream:
                w = csv.DictWriter(stream,fieldnames=list(frames[0]))
                w.writeheader(); w.writerows(frames)
            summary["frames_sha256"] = sha(log_path)
        video_path = out/"backup.avi"
        if video_path.exists(): summary["video_sha256"] = sha(video_path)
        (out/"summary.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config",default="configs/round7_webcam.json")
    p.add_argument("--drive",default="G:/My Drive/face-pad")
    p.add_argument("--output",required=True,help="Fresh artifact directory")
    p.add_argument("--scenario",choices=["unlabelled","live","print","screen_photo","replay","failure"],default="unlabelled")
    p.add_argument("--seconds",type=float)
    p.add_argument("--no-preview",action="store_true")
    p.add_argument("--probe",action="store_true",help="Only open/read camera; no model or FPS measurement")
    p.add_argument("--start-mode",choices=["space","automatic"],default="space")
    result = run(p.parse_args())
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["status"] in ("measured","PASS: camera open/read probe only; no FPS/PAD claim") else 1)
