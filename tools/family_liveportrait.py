"""Encode a face video as a motion/audio ZIP, or render that ZIP offline."""
import argparse
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from zipfile import ZIP_DEFLATED, ZipFile


def local_input(path):
    """Build FFmpeg input arguments with file and pipe protocols only."""
    return ("-protocol_whitelist", "file,pipe", "-i", str(path))


def ffmpeg(executable, *args, **kwargs):
    return subprocess.run([executable, "-v", "error", "-nostdin", *map(str, args)],
                          check=True, **kwargs)


def load_runtime(checkout):
    def no_network(event, _args):
        if event in {"socket.connect", "socket.getaddrinfo"}:
            raise RuntimeError("This tool runs offline. Install the weights first.")

    sys.addaudithook(no_network)
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", CUDA_VISIBLE_DEVICES="")
    sys.path.insert(0, str(checkout.resolve()))
    import cv2
    import numpy as np
    import torch
    from src.config.inference_config import InferenceConfig
    from src.live_portrait_wrapper import LivePortraitWrapper
    from src.utils.camera import get_rotation_matrix

    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    model = LivePortraitWrapper(InferenceConfig(flag_force_cpu=True, flag_use_half_precision=False))
    return cv2, np, torch, model, get_rotation_matrix


def pack(args, runtime):
    _, np, torch, model, rotation = runtime
    crop = f"crop={args.crop}," if args.crop else ""
    video_filter = f"{crop}fps={args.fps},scale=256:256:force_original_aspect_ratio=increase,crop=256:256"
    raw = ffmpeg(args.ffmpeg, *local_input(args.clip), "-an", "-vf", video_filter,
                 "-frames:v", args.fps * 30 + 1, "-pix_fmt", "rgb24", "-threads", 1,
                 "-f", "rawvideo", "-", capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, 256, 256, 3)
    if not 1 <= len(frames) <= args.fps * 30:
        raise ValueError("Use a clip with video of at most 30 seconds")
    motion = []
    start = time.perf_counter()
    for frame in frames:
        pose = model.get_kp_info(model.prepare_source(frame))
        matrix = rotation(pose["pitch"], pose["yaw"], pose["roll"])
        if not motion:
            first, first_matrix = pose, matrix
        relative = (matrix @ first_matrix.transpose(1, 2), pose["exp"] - first["exp"],
                    pose["t"] - first["t"], pose["scale"] / first["scale"])
        motion.append(torch.cat([item.flatten() for item in relative]).numpy())
    duration = len(frames) / args.fps
    audio = ffmpeg(args.ffmpeg, "-copyts", *local_input(args.clip), "-map", "0:a:0", "-vn",
                   "-af", "aresample=async=1:first_pts=0,apad", "-t", duration, "-ac", 1,
                   "-c:a", "libopus", "-b:a", "24k", "-f", "ogg", "-", capture_output=True).stdout
    encoded = io.BytesIO()
    np.save(encoded, np.asarray(motion, dtype="<f4"), allow_pickle=False)
    with ZipFile(args.output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("message.json", json.dumps({"version": 1, "fps": args.fps, "frames": len(frames)}))
        archive.writestr("motion.npy", encoded.getvalue())
        archive.writestr("audio.ogg", audio)
    if args.baseline:
        with tempfile.TemporaryDirectory() as scratch:
            voice = Path(scratch) / "audio.ogg"
            voice.write_bytes(audio)
            ffmpeg(args.ffmpeg, "-y", *local_input(args.clip), *local_input(voice), "-vf", video_filter,
                   "-map", "0:v:0", "-map", "1:a:0", "-t", duration, "-c:v", "libx264",
                   "-b:v", "64k", "-maxrate", "64k", "-bufsize", "128k", "-pix_fmt", "yuv420p",
                   "-c:a", "copy", "-movflags", "+faststart", args.baseline)
    print(json.dumps({"frames": len(frames), "fps": args.fps, "seconds": duration,
                      "zip_bytes": args.output.stat().st_size, "audio_bytes": len(audio),
                      "baseline_bytes": args.baseline.stat().st_size if args.baseline else None,
                      "pack_seconds": round(time.perf_counter() - start, 2)}), flush=True)


def read_message(path, np):
    with ZipFile(path) as archive:
        limits = {"message.json": 1024, "motion.npy": 300_000, "audio.ogg": 512_000}
        if sorted(archive.namelist()) != sorted(limits) or any(
            entry.file_size > limits[entry.filename] for entry in archive.infolist()
        ):
            raise ValueError("Unexpected message entries or size")
        metadata = json.loads(archive.read("message.json"))
        fps = metadata["fps"]
        count = metadata["frames"]
        if metadata["version"] != 1 or type(fps) is not int or type(count) is not int or not (
            1 <= fps <= 30 and 1 <= count <= fps * 30
        ):
            raise ValueError("Unsupported message metadata")
        track = np.load(io.BytesIO(archive.read("motion.npy")), allow_pickle=False)
        if track.shape != (count, 76) or track.dtype != np.dtype("<f4") or not np.isfinite(track).all():
            raise ValueError("Invalid motion track")
        return fps, track, archive.read("audio.ogg")


def render(args, runtime):
    cv2, np, torch, model, rotation = runtime
    fps, track, audio = read_message(args.message, np)
    image = cv2.imread(str(args.portrait))
    if image is None or image.shape[:2] != (256, 256):
        raise ValueError("The preloaded portrait must be a 256 × 256 image")
    source = model.prepare_source(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    pose = model.get_kp_info(source)
    matrix = rotation(pose["pitch"], pose["yaw"], pose["roll"])
    keypoints = model.transform_keypoint(pose)
    appearance = model.extract_feature_3d(source)
    start = time.perf_counter()
    with tempfile.TemporaryDirectory() as scratch:
        voice = Path(scratch) / "audio.ogg"
        voice.write_bytes(audio)
        command = [args.ffmpeg, "-v", "error", "-y", "-f", "rawvideo", "-pixel_format", "rgb24",
                   "-video_size", "512x512", "-framerate", str(fps), *local_input("pipe:0"), *local_input(voice),
                   "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-movflags", "+faststart", str(args.output)]
        with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
            for index, row in enumerate(torch.from_numpy(track), 1):
                angles = row[:9].reshape(1, 3, 3) @ matrix
                expression = pose["exp"] + row[9:72].reshape(1, 21, 3)
                shift = pose["t"] + row[72:75]
                shift[..., 2] = 0
                scale = pose["scale"] * row[75]
                target = scale[..., None] * (pose["kp"] @ angles + expression) + shift[:, None, :]
                target = model.stitching(keypoints, target)
                result = model.warp_decode(appearance, keypoints, target)["out"]
                encoder.stdin.write(model.parse_output(result)[0].tobytes())
                if index % 5 == 0:
                    print(f"Rendered {index}/{len(track)} frames", flush=True)
            encoder.stdin.close()
            if encoder.wait():
                raise RuntimeError("Video encoding failed")
    elapsed = time.perf_counter() - start
    ffmpeg(args.ffmpeg, "-xerror", *local_input(args.output), "-f", "null", "-")
    print(json.dumps({"frames": len(track), "fps": fps, "render_and_encode_seconds": round(elapsed, 2),
                      "portrait_bytes": args.portrait.stat().st_size}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--liveportrait", type=Path, required=True)
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    commands = parser.add_subparsers(dest="command", required=True)
    sender = commands.add_parser("pack")
    sender.add_argument("clip", type=Path)
    sender.add_argument("output", type=Path)
    sender.add_argument("--fps", type=int, choices=range(1, 31), default=15, metavar="1–30")
    sender.add_argument("--crop", help="FFmpeg crop as width:height:x:y")
    sender.add_argument("--baseline", type=Path)
    receiver = commands.add_parser("render")
    receiver.add_argument("message", type=Path)
    receiver.add_argument("portrait", type=Path)
    receiver.add_argument("output", type=Path)
    args = parser.parse_args()
    if not args.ffmpeg:
        parser.error("Set --ffmpeg or add ffmpeg to PATH")
    if getattr(args, "crop", None) and not re.fullmatch(r"\d+:\d+:\d+:\d+", args.crop):
        parser.error("--crop requires width:height:x:y in pixels")
    inputs = ("clip",) if args.command == "pack" else ("message", "portrait")
    for name in inputs:
        path = getattr(args, name).resolve()
        if not path.is_file():
            parser.error(f"{name} must be a local file")
        setattr(args, name, path)
    args.output = args.output.resolve()
    if getattr(args, "baseline", None):
        args.baseline = args.baseline.resolve()
    input_paths = {getattr(args, name) for name in inputs}
    if args.output in input_paths or getattr(args, "baseline", None) in input_paths | {args.output}:
        parser.error("Use separate output and input paths")
    runtime = load_runtime(args.liveportrait)
    with runtime[2].inference_mode():
        (pack if args.command == "pack" else render)(args, runtime)


if __name__ == "__main__":
    main()
