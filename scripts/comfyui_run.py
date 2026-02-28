#!/usr/bin/env python3
"""Queue a ComfyUI workflow (API-format JSON) and poll until done.
Prints JSON on success or structured JSON error details on failure.
"""
import argparse
import json
import sys
import time
import uuid
import urllib.request
import urllib.error


def http_json(url, method="GET", payload=None, timeout=30):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        detail = None
        if body:
            try:
                detail = json.loads(body)
            except Exception:
                detail = {"raw": body}
        print(json.dumps({
            "error": "http_error",
            "status": e.code,
            "url": url,
            "detail": detail,
        }))
        sys.exit(1)


def load_workflow(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_output_images(history_obj):
    outputs = history_obj.get("outputs", {})
    images = []
    for _node_id, node_out in outputs.items():
        for img in node_out.get("images", []) or []:
            images.append(img)
    return images


def extract_error(status_obj):
    """Pull the last execution_error payload from status.messages if present."""
    messages = status_obj.get("messages") or []
    for msg in reversed(messages):
        if isinstance(msg, list) and len(msg) >= 2 and msg[0] == "execution_error":
            detail = msg[1] if isinstance(msg[1], dict) else {"raw": msg[1]}
            return {
                "node_id": detail.get("node_id"),
                "node_type": detail.get("node_type"),
                "exception_type": detail.get("exception_type"),
                "exception_message": detail.get("exception_message"),
                "prompt_id": detail.get("prompt_id"),
            }
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", default="8188")
    ap.add_argument("--workflow", required=True, help="Path to API workflow JSON (already edited; script does not modify it)")
    ap.add_argument("--timeout", type=int, default=300, help="Seconds to wait for completion")
    ap.add_argument("--poll", type=float, default=1.5, help="Seconds between history polls")
    args = ap.parse_args()

    base = f"http://{args.host}:{args.port}"
    workflow = load_workflow(args.workflow)

    payload = {
        "client_id": str(uuid.uuid4()),
        "prompt": workflow,
    }

    resp = http_json(f"{base}/prompt", method="POST", payload=payload)
    prompt_id = resp.get("prompt_id")
    if not prompt_id:
        raise SystemExit(f"No prompt_id returned: {resp}")

    deadline = time.time() + args.timeout
    while time.time() < deadline:
        hist = http_json(f"{base}/history/{prompt_id}")
        item = hist.get(prompt_id)
        if item:
            status = item.get("status", {})
            status_str = status.get("status_str")

            if status.get("completed") and status_str != "error":
                images = find_output_images(item)
                print(json.dumps({"prompt_id": prompt_id, "images": images}))
                return

            if status_str == "error":
                err = extract_error(status) or {}
                print(json.dumps({
                    "prompt_id": prompt_id,
                    "error": "execution_error",
                    "status": status_str,
                    "detail": err,
                }))
                sys.exit(1)

        time.sleep(args.poll)

    print(json.dumps({
        "prompt_id": prompt_id,
        "error": "timeout",
        "message": f"Timed out waiting for completion after {args.timeout}s",
    }))
    sys.exit(1)


if __name__ == "__main__":
    main()
