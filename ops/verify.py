import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def verify(port, expected_revision):
    expected = {"/health": {"ready": True}, "/version": {"revision": expected_revision}}
    passed = True
    for path, body in expected.items():
        try:
            with urlopen(f"http://127.0.0.1:{port}{path}", timeout=3) as response:
                status = response.status
                actual = json.load(response)
        except HTTPError as error:
            with error:
                status, actual = error.code, error.read().decode()
        except (URLError, TimeoutError, ValueError) as error:
            print(f"{path} request failed: {error}")
            passed = False
            continue
        print(f"HTTP {status} {path} {actual}")
        passed &= status == 200 and actual == body
    return passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8194)
    parser.add_argument("revision")
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.port, args.revision) else 1)
