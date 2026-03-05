import os, json, time, requests

URL = os.environ.get("UPSTASH_REDIS_REST_URL","").rstrip("/")
TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN","")
QUEUE = os.environ.get("STELLCODEX_QUEUE_KEY","stellcodex:queue")

def cmd(c,*a):
    r = requests.get(f"{URL}/{c}/" + "/".join(map(str,a)),
        headers={"Authorization":f"Bearer {TOKEN}"}, timeout=20)
    r.raise_for_status()
    return r.json().get("result")

print("GitHub worker started")
while True:
    try:
        job = cmd("brpop", QUEUE, 15)
        if not job:
            print("queue empty"); continue
        _, payload = job
        try: data = json.loads(payload)
        except: data = {"raw":payload}
        print("JOB:", str(data)[:500])
        print("done")
    except Exception as e:
        print("err:", e); time.sleep(3)
