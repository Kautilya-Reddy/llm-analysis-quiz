import threading, time, os, requests

def _ping_self(url, interval):
    while True:
        try:
            requests.get(url, timeout=10)
        except Exception:
            pass
        time.sleep(interval)

def start_keepalive_thread():
    url = os.environ.get("KEEPALIVE_SELF_URL", "")
    interval = int(os.environ.get("KEEPALIVE_INTERVAL_SECONDS", "240"))
    if not url:
        return
    t = threading.Thread(target=_ping_self, args=(url, interval))
    t.daemon = True
    t.start()
