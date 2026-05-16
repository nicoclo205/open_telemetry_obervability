import httpx
import os
import time

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

def main():
    endpoints = []
    for _ in range(20):
        endpoints.append("/stickers")
    for i in range(1, 21):
        endpoints.append(f"/stickers/{i}")
    for i in range(1, 11):
        endpoints.append(f"/stickers/album/{i}")

    total = len(endpoints)
    ok = 0
    failed = 0
    start = time.time()

    with httpx.Client(base_url=BASE_URL) as client:
        for idx, path in enumerate(endpoints, start=1):
            status = "err"
            try:
                response = client.get(path)
                status = response.status_code
                if response.status_code < 400:
                    ok += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

            if idx % 10 == 0:
                print(f"Request {idx}/{total} — status {status}")

    elapsed = time.time() - start

    print("")
    print("=== Load Test Summary ===")
    print(f"Total:   {total}")
    print(f"OK:      {ok}")
    print(f"Failed:  {failed}")
    print(f"Time:    {elapsed:.2f}s")

main()
