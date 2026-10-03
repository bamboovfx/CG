"""Run the classroom chair four-view test through Tripo's v3 P2 API.

By default this script only checks authentication and balance. Pass --submit to
upload the four local views, create a paid generation task, and download its GLB.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests


BASE_URL = "https://openapi.tripo3d.ai/v3"
HERE = Path(__file__).resolve().parent
VIEWS = ("front", "left", "back", "right")
MODEL_FILE = HERE / "tripo_chair_api_p2_quad.glb"
METADATA_FILE = HERE / "tripo_chair_api_task.json"


def get_api_key():
    """Read the key from this process or the Windows user environment."""
    key = os.environ.get("TRIPO_API_KEY")
    if key:
        return key
    if sys.platform == "win32":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as entry:
                key, _ = winreg.QueryValueEx(entry, "TRIPO_API_KEY")
                return key
        except FileNotFoundError:
            pass
    raise RuntimeError("TRIPO_API_KEY is not set in the process or Windows user environment")


def api_json(session, method, path, **kwargs):
    """Call one API endpoint and return validated JSON without exposing the key."""
    response = session.request(method, BASE_URL + path, timeout=60, **kwargs)
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != 0:
        raise RuntimeError(f"Tripo API code {payload.get('code')}: {payload.get('message', 'unknown error')}")
    return payload.get("data", {})


def upload_views(session):
    """Upload each reference PNG and return Tripo's view-key input array."""
    inputs = []
    for view in VIEWS:
        path = HERE / f"chair_{view}.png"
        if not path.is_file():
            raise FileNotFoundError(path)
        with path.open("rb") as image_file:
            data = api_json(session, "POST", "/files", files={"file": (path.name, image_file, "image/png")})
        inputs.append({view: data["file_token"]})
        print(f"Uploaded {view} view")
    return inputs


def wait_for_model(session, task_id, timeout_seconds=900):
    """Poll the paid generation task until it succeeds or reaches a terminal failure."""
    deadline = time.monotonic() + timeout_seconds
    last_status = None
    while time.monotonic() < deadline:
        task = api_json(session, "GET", f"/tasks/{task_id}")
        status = task.get("status")
        if status != last_status:
            print(f"Task status: {status}")
            last_status = status
        if status == "success":
            return task
        if status in {"failed", "cancelled", "banned"}:
            raise RuntimeError(f"Tripo task ended with status {status}")
        time.sleep(3)
    raise TimeoutError(f"Tripo task {task_id} did not finish within {timeout_seconds} seconds")


def download_model(session, model_url):
    """Save the short-lived signed GLB URL to a local candidate file."""
    if MODEL_FILE.exists():
        raise FileExistsError(f"Preserving existing output: {MODEL_FILE}")
    with session.get(model_url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with MODEL_FILE.open("wb") as target:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    target.write(chunk)


def main():
    """Run a free balance preflight, then optionally submit the four-view task."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submit", action="store_true", help="Upload views and create a paid P2 quad task")
    args = parser.parse_args()

    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {get_api_key()}"
    account = api_json(session, "GET", "/account/balance")
    balance = float(account.get("balance", 0))
    print(f"Tripo API authentication: success; available balance: {balance:g}")
    if not args.submit:
        print("Preflight only. Use --submit after adding API credits.")
        return

    # P2 generation without Tripo textures is documented at 100 API credits.
    if balance < 100:
        raise RuntimeError("At least 100 API credits are required for this P2 geometry task")
    if MODEL_FILE.exists() or METADATA_FILE.exists():
        raise FileExistsError("Existing API output found; move it aside before another paid run")

    inputs = upload_views(session)
    request = {
        "inputs": inputs,
        "model": "P2-20260801",
        "quad": True,
        "face_limit": 10000,
        "texture": False,
        "pbr": False,
        "export_uv": False,
    }
    created = api_json(session, "POST", "/generation/multiview-to-model", json=request)
    task_id = created["task_id"]
    print(f"Submitted Tripo task: {task_id}")
    task = wait_for_model(session, task_id)
    model_url = task.get("output", {}).get("model_url")
    if not model_url:
        raise RuntimeError("Task succeeded but returned no model_url")
    download_model(session, model_url)

    # Store only stable audit fields; signed download URLs and file tokens expire.
    metadata = {
        "task_id": task_id,
        "model": request["model"],
        "quad": request["quad"],
        "face_limit": request["face_limit"],
        "credits_consumed": task.get("credits_consumed"),
        "model_file": MODEL_FILE.name,
    }
    METADATA_FILE.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved model: {MODEL_FILE}")


if __name__ == "__main__":
    main()
