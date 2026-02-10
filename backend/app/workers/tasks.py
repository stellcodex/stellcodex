from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.core.storage import get_s3_client
from app.db.session import SessionLocal
from app.models.file import UploadFile
from app.queue import get_queue


CAD_OCCT_EXTS = {"step", "stp", "iges", "igs", "brep", "brp"}
CAD_FREECAD_EXTS = {"fcstd", "ifc"}
MESH_EXTS = {"stl", "obj", "ply", "off", "3mf", "amf", "dae"}

DEFAULT_RESULT_TTL_SECONDS = 3600
DEFAULT_JOB_TTL_SECONDS = 3600


def _ext(name: str) -> str:
    return (Path(name).suffix or "").lower().lstrip(".")


def _is_2d(content_type: str, filename: str) -> bool:
    if content_type in {"application/pdf", "image/png", "image/jpeg"}:
        return True
    return _ext(filename) in {"pdf", "png", "jpg", "jpeg", "dxf"}


def _is_gltf(content_type: str, filename: str) -> bool:
    if content_type in {"model/gltf-binary", "model/gltf+json"}:
        return True
    return _ext(filename) in {"glb", "gltf"}


def _run(cmd: list[str], timeout: int) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)


def _convert_with_assimp(input_path: str, output_path: str) -> None:
    cmd = ["assimp", "export", input_path, output_path, "-f", "glb"]
    _run(cmd, timeout=settings.conversion_timeout_seconds)


def _convert_with_occt(input_path: str, output_path: str) -> None:
    cmd = ["occt-convert", input_path, output_path]
    _run(cmd, timeout=settings.conversion_timeout_seconds)


def _freecad_script(input_path: str, output_path: str) -> str:
    return """
import FreeCAD
import Mesh
import MeshPart

doc = FreeCAD.open(r"{input_path}")
objs = [o for o in doc.Objects if hasattr(o, "Shape")]
meshes = []
for o in objs:
    try:
        shape = o.Shape
        if not shape or shape.isNull():
            continue
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.1, AngularDeflection=0.5, Relative=True)
        meshes.append(mesh)
    except Exception:
        pass

if not meshes:
    raise Exception("No meshable shape")

# Merge meshes
merged = meshes[0]
for m in meshes[1:]:
    merged.addMesh(m)

Mesh.export([merged], r"{output_path}")
""".format(input_path=input_path, output_path=output_path)


def _convert_with_freecad(input_path: str, output_path: str) -> None:
    script = _freecad_script(input_path, output_path)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_script:
        tmp_script.write(script.encode("utf-8"))
        tmp_script.flush()
        script_path = tmp_script.name
    try:
        cmd = [settings.freecad_bin, "--console", "-c", script_path]
        _run(cmd, timeout=settings.conversion_timeout_seconds)
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass


def _render_thumbnail(glb_path: str, output_path: str) -> None:
    script = """
import bpy
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1 :]
input_path = argv[0]
output_path = argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=input_path)

# Center and scale
bbox_min = [1e9, 1e9, 1e9]
bbox_max = [-1e9, -1e9, -1e9]
for obj in bpy.context.scene.objects:
    if obj.type == "MESH":
        for v in obj.bound_box:
            bbox_min[0] = min(bbox_min[0], v[0])
            bbox_min[1] = min(bbox_min[1], v[1])
            bbox_min[2] = min(bbox_min[2], v[2])
            bbox_max[0] = max(bbox_max[0], v[0])
            bbox_max[1] = max(bbox_max[1], v[1])
            bbox_max[2] = max(bbox_max[2], v[2])

center = [(bbox_min[i] + bbox_max[i]) / 2 for i in range(3)]
for obj in bpy.context.scene.objects:
    if obj.type == "MESH":
        obj.location = [obj.location[i] - center[i] for i in range(3)]

# Camera
bpy.ops.object.camera_add(location=(2.5, -2.5, 2.0))
cam = bpy.context.active_object
cam.data.lens = 50
bpy.context.scene.camera = cam

# Light
bpy.ops.object.light_add(type="SUN", location=(5, -5, 5))

bpy.context.scene.render.engine = "BLENDER_EEVEE"
bpy.context.scene.render.image_settings.file_format = "PNG"
bpy.context.scene.render.filepath = output_path
bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 600

bpy.ops.render.render(write_still=True)
"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_script:
        tmp_script.write(script.encode("utf-8"))
        tmp_script.flush()
        script_path = tmp_script.name
    try:
        cmd = [settings.blender_bin, "-b", "--python", script_path, "--", glb_path, output_path]
        _run(cmd, timeout=settings.blender_timeout_seconds)
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass


def _parse_assimp_info(output: str) -> dict:
    data: dict[str, object] = {}
    for line in output.splitlines():
        if "Meshes:" in line:
            m = re.search(r"Meshes:\s*(\d+)", line)
            if m:
                data["meshes"] = int(m.group(1))
        if "Vertices:" in line:
            m = re.search(r"Vertices:\s*(\d+)", line)
            if m:
                data["vertices"] = int(m.group(1))
        if "Faces:" in line:
            m = re.search(r"Faces:\s*(\d+)", line)
            if m:
                data["faces"] = int(m.group(1))
        if "Bounding" in line:
            nums = re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", line)
            if len(nums) >= 6:
                vals = [float(n) for n in nums[:6]]
                data["bbox"] = {
                    "min_x": vals[0],
                    "min_y": vals[1],
                    "min_z": vals[2],
                    "max_x": vals[3],
                    "max_y": vals[4],
                    "max_z": vals[5],
                }
    return data


def _extract_metadata(glb_path: str) -> dict:
    cmd = ["assimp", "info", glb_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout + "\n" + result.stderr
    return _parse_assimp_info(output)


def _mark_failed(db: SessionLocal, f: UploadFile, detail: str) -> str:
    error_id = str(uuid4())
    f.status = "failed"
    f.meta = {**(f.meta or {}), "error": detail, "error_id": error_id}
    db.add(f)
    db.commit()
    return error_id


def _convert_cad_pipeline(f: UploadFile, s3) -> str:
    ext = _ext(f.original_filename)
    with tempfile.TemporaryDirectory() as tmp:
        suffix = f".{ext}" if ext else ""
        in_path = os.path.join(tmp, f"input{suffix}")
        out_path = os.path.join(tmp, "output.glb")
        s3.download_file(f.bucket, f.object_key, in_path)

        if ext in CAD_OCCT_EXTS:
            _convert_with_occt(in_path, out_path)
        elif ext in CAD_FREECAD_EXTS:
            mesh_path = os.path.join(tmp, "mesh.stl")
            _convert_with_freecad(in_path, mesh_path)
            _convert_with_assimp(mesh_path, out_path)
        else:
            raise RuntimeError(f"Unsupported CAD format: {ext}")

        out_key = f"converted/{f.file_id}/model.glb"
        s3.upload_file(out_path, f.bucket, out_key, ExtraArgs={"ContentType": "model/gltf-binary"})
        return out_key


def _convert_mesh_pipeline(f: UploadFile, s3) -> str:
    ext = _ext(f.original_filename)
    if ext not in MESH_EXTS:
        raise RuntimeError(f"Unsupported mesh format: {ext}")
    with tempfile.TemporaryDirectory() as tmp:
        in_path = os.path.join(tmp, f"input.{ext}")
        out_path = os.path.join(tmp, "output.glb")
        s3.download_file(f.bucket, f.object_key, in_path)
        _convert_with_assimp(in_path, out_path)
        out_key = f"converted/{f.file_id}/model.glb"
        s3.upload_file(out_path, f.bucket, out_key, ExtraArgs={"ContentType": "model/gltf-binary"})
        return out_key


def _generate_thumbnail_pipeline(f: UploadFile, s3) -> str | None:
    if not f.gltf_key:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        in_path = os.path.join(tmp, "model.glb")
        out_path = os.path.join(tmp, "thumb.png")
        s3.download_file(f.bucket, f.gltf_key, in_path)
        _render_thumbnail(in_path, out_path)
        thumb_key = f"thumbnails/{f.file_id}/thumb.png"
        s3.upload_file(out_path, f.bucket, thumb_key, ExtraArgs={"ContentType": "image/png"})
        return thumb_key


def _extract_metadata_pipeline(f: UploadFile, s3) -> dict:
    if not f.gltf_key:
        return {}
    with tempfile.TemporaryDirectory() as tmp:
        in_path = os.path.join(tmp, "model.glb")
        s3.download_file(f.bucket, f.gltf_key, in_path)
        return _extract_metadata(in_path)


def convert_cad_to_glb(file_id: str):
    return convert_file(file_id)


def convert_mesh_to_glb(file_id: str):
    return convert_file(file_id)


def generate_thumbnails(file_id: str):
    db = SessionLocal()
    try:
        f: UploadFile | None = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if not f:
            return {"status": "missing"}
        s3 = get_s3_client(settings)
        try:
            thumb_key = _generate_thumbnail_pipeline(f, s3)
            if thumb_key:
                f.thumbnail_key = thumb_key
                db.add(f)
                db.commit()
            return {"status": "ok", "thumbnail_key": thumb_key}
        except Exception as e:
            _mark_failed(db, f, str(e))
            raise
    finally:
        db.close()


def extract_metadata(file_id: str):
    db = SessionLocal()
    try:
        f: UploadFile | None = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if not f:
            return {"status": "missing"}
        s3 = get_s3_client(settings)
        data = _extract_metadata_pipeline(f, s3)
        f.meta = {**(f.meta or {}), "metadata": data}
        db.add(f)
        db.commit()
        return {"status": "ok", "metadata": data}
    finally:
        db.close()


def convert_file(file_id: str):
    db = SessionLocal()
    try:
        f: UploadFile | None = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if not f:
            return {"status": "missing"}

        if f.status == "ready" and f.gltf_key:
            return {"status": "ready", "mode": "cached"}

        f.status = "processing"
        db.add(f)
        db.commit()
        db.refresh(f)

        s3 = get_s3_client(settings)

        if _is_2d(f.content_type, f.original_filename):
            f.status = "ready"
            db.add(f)
            db.commit()
            return {"status": "ready", "mode": "2d"}

        if _is_gltf(f.content_type, f.original_filename):
            f.gltf_key = f.object_key
            f.status = "ready"
            db.add(f)
            db.commit()
        else:
            ext = _ext(f.original_filename)
            if ext in CAD_OCCT_EXTS or ext in CAD_FREECAD_EXTS:
                f.gltf_key = _convert_cad_pipeline(f, s3)
            elif ext in MESH_EXTS:
                f.gltf_key = _convert_mesh_pipeline(f, s3)
            else:
                raise RuntimeError(f"Unsupported format: {ext}")
            f.status = "ready"
            db.add(f)
            db.commit()

        # Best-effort metadata and thumbnail
        try:
            meta = _extract_metadata_pipeline(f, s3)
            if meta:
                f.meta = {**(f.meta or {}), "metadata": meta}
        except Exception as e:
            f.meta = {**(f.meta or {}), "metadata_error": str(e)}

        try:
            thumb_key = _generate_thumbnail_pipeline(f, s3)
            if thumb_key:
                f.thumbnail_key = thumb_key
        except Exception as e:
            f.meta = {**(f.meta or {}), "thumbnail_error": str(e)}

        db.add(f)
        db.commit()
        return {"status": "ready", "mode": "converted"}

    except subprocess.CalledProcessError as e:
        f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if f:
            detail = (e.stderr or e.stdout or "conversion failed").strip()
            _mark_failed(db, f, detail)
        raise
    except Exception as e:
        f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if f:
            _mark_failed(db, f, str(e))
        raise
    finally:
        db.close()


def ping_job():
    return {"status": "ok"}


def enqueue_convert_file(file_id: str) -> str:
    q = get_queue("cad")
    job = q.enqueue(
        convert_file,
        file_id,
        job_timeout=settings.conversion_timeout_seconds + 60,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
    )
    return job.get_id()


def enqueue_generate_thumbnails(file_id: str) -> str:
    q = get_queue("render")
    job = q.enqueue(
        generate_thumbnails,
        file_id,
        job_timeout=settings.blender_timeout_seconds + 60,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
    )
    return job.get_id()


def enqueue_extract_metadata(file_id: str) -> str:
    q = get_queue("cad")
    job = q.enqueue(
        extract_metadata,
        file_id,
        job_timeout=settings.conversion_timeout_seconds + 60,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
    )
    return job.get_id()


def enqueue_ping_job() -> str:
    q = get_queue("cad")
    job = q.enqueue(
        ping_job,
        job_timeout=30,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
    )
    return job.get_id()
