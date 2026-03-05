import sys
import requests
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import hashlib
from fastapi.middleware.cors import CORSMiddleware
import threading
import time
from contextlib import asynccontextmanager
import json
# Thêm cái này ngay dưới dòng app = FastAPI()
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)
# ===== CONFIG =====
NODES = cfg["nodes"]  # Danh sách các node trong cụm
NODE_STATUS = {node: True for node in NODES}

PORT = sys.argv[1]          # LẤY PORT TỪ CMD
CURRENT_NODE = f"http://127.0.0.1:{PORT}"

# ===== APP =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ===== STARTUP =====
    recover_data()
    threading.Thread(
        target=heartbeat_loop,
        daemon=True
    ).start()
    yield   # 👈 FastAPI chạy ở đây
    # ===== SHUTDOWN (có thể bỏ trống) =====
    print("Node shutting down...")
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép tất cả các nguồn (cổng 8000, 8001, 8002...)
    allow_methods=["*"], # Cho phép mọi loại lệnh (GET, POST, PUT...)
    allow_headers=["*"], # Cho phép mọi loại Header
)
store = {}
#hash cố định
def heartbeat_loop():
    while True:
        for node in NODES:
            if node == CURRENT_NODE:
                continue
            try:
                requests.get(f"{node}/heartbeat", timeout=1)
                NODE_STATUS[node] = True
            except:
                NODE_STATUS[node] = False
        time.sleep(3)
def recover_data():
    for node in NODES:
        if node == CURRENT_NODE:
            continue
        try:
            data = requests.get(
                f"{node}/snapshot_for",
                params={"node_url": CURRENT_NODE},
                timeout=2
            ).json()

            store.update(data)
            print("Recovered correct partition from", node)
        except:
            pass

def hash_co_dinh(key: str):
    key_bytes = key.encode('utf-8')
    hash_object = hashlib.md5(key_bytes)
    return int(hash_object.hexdigest(), 16)

# ===== UI =====
app.mount("/static", StaticFiles(directory="static"), name="static")
def get_primary_node(key: str):
    return NODES[hash_co_dinh(key) % len(NODES)]

def get_replica_node(key: str):
    return NODES[(hash_co_dinh(key) + 1) % len(NODES)]
def get_replica1_node(key: str):
    return NODES[(hash_co_dinh(key) + 2) % len(NODES)]

@app.get("/")
def ui():
    return FileResponse("static/index.html")


# ===== PUT =====
@app.post("/put")
def put(key: str, value: str):
    primary = get_primary_node(key)
    replica = get_replica_node(key)
    replica1 = get_replica1_node(key)

    # Nếu request tới node không phải primary → forward
    if CURRENT_NODE != primary:
        try:
            return requests.post(
                f"{primary}/put",
                params={"key": key, "value": value},
                timeout=2
            ).json()
        except Exception:
            return {"lỗi": "node primary không phản hồi"}

    # LƯU PRIMARY
    store[key] = value

    # GHI REPLICA (không để crash)
    try:
        requests.post(
            f"{replica}/replica",
            params={"key": key, "value": value},
            timeout=2
        )
    except Exception:
        pass  # replica chết cũng không sao
    try:
        requests.post(
            f"{replica1}/replica",
            params={"key": key, "value": value},
            timeout=2
        )
    except Exception:
        pass  # replica chết cũng không sao
    return {
        "stored_at": primary,
        "replica": replica,
        "replica1": replica1,
        "key": key,
        "value": value
    }
@app.post("/replica")
def replica_put(key: str, value: str):
    store[key] = value
    return {"replica_store": CURRENT_NODE,}

# ===== GET =====
@app.get("/get_local")
def get_local(key: str):
    if key not in store:
        return {"lỗi": "Không tim thấy trong local"}
    return {
        "value": store[key],
        "source": CURRENT_NODE
    }
@app.get("/get")
def get(key: str):
    primary = get_primary_node(key)
    replica = get_replica_node(key)
    replica1 = get_replica1_node(key)

    # Nếu không phải primary → forward
    if CURRENT_NODE != primary:
        try:
            return requests.get(
                f"{primary}/get",
                params={"key": key},
                timeout=2
            ).json()
        except Exception:
            # primary chết → thử replica
            try:
                return requests.get(
                    f"{replica}/get_local",
                    params={"key": key},
                    timeout=2
                ).json()
            except Exception:
                # replica cũng chết → thử replica1
                try:
                    return requests.get(
                        f"{replica1}/get_local",
                        params={"key": key},
                        timeout=2
                    ).json()
                except Exception:
                    return {"lỗi": "các node đều không phản hồi"}

    # PRIMARY LOCAL
    if key in store:
        return {
            "value": store[key],
            "source": primary
        }

    # PRIMARY CHẾT TRƯỚC ĐÓ → fallback replica
    try:
        return requests.get(
            f"{replica}/get_local",
            params={"key": key},
            timeout=2
        ).json()
    except Exception:
        try:
            return requests.get(
                f"{replica1}/get_local",
                params={"key": key},
                timeout=2
            ).json()
        except Exception:
            return {"lỗi": "không tìm thấy key trên các node"}
# delete key
# ===== DELETE =====
@app.delete("/delete")
def delete(key: str):
    primary = get_primary_node(key)
    replica = get_replica_node(key)
    replica1 = get_replica1_node(key)

    # Nếu request tới node không phải primary → forward
    if CURRENT_NODE != primary:
        try:
            return requests.delete(
                f"{primary}/delete",
                params={"key": key},
                timeout=2
            ).json()
        except Exception:
            return {"lỗi": "node primary không phản hồi"}

    # XÓA PRIMARY
    if key in store:
        del store[key]

    # XÓA REPLICA
    try:
        requests.delete(
            f"{replica}/delete_local",
            params={"key": key},
            timeout=2
        )
    except:
        pass

    try:
        requests.delete(
            f"{replica1}/delete_local",
            params={"key": key},
            timeout=2
        )
    except:
        pass

    return {
        "deleted_from": primary,
        "replica": replica,
        "replica1": replica1,
        "key": key
    }
#xoa local
@app.delete("/delete_local")
def delete_local(key: str):
    if key in store:
        del store[key]
    return {"deleted_at": CURRENT_NODE}
@app.get("/all_data")
def get_all_data():
    # Trả về dữ liệu local của chính Node này
    return {
        "node": CURRENT_NODE,
        "data": store
    }
@app.get("/heartbeat")
def heartbeat():
    return {"status": "alive", "node": CURRENT_NODE}
@app.get("/snapshot_for")
def snapshot_for(node_url: str):
    result = {}
    for k, v in store.items():
        if get_primary_node(k) == node_url \
           or get_replica_node(k) == node_url \
           or get_replica1_node(k) == node_url:
            result[k] = v
    return result

if __name__ == "__main__":
    import uvicorn
    import sys

    port = int(sys.argv[1])
    uvicorn.run("server:app", host="127.0.0.1", port=port, reload=False)