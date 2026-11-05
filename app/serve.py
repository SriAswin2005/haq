"""Start the Haq web app and open it in the browser.

  python -m app.serve            # real models (keys from .env)
  python -m app.serve --mock     # no keys: canned model
  python -m app.serve --port 8000 --no-browser
"""
import argparse
import os
import threading
import webbrowser


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m app.serve")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 7860)))
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    if a.mock:
        os.environ["AI_LAWYER_MOCK"] = "1"
    import uvicorn
    url = f"http://localhost:{a.port}"
    print(f"Haq is starting at {url}  (Ctrl+C to stop)")
    if not a.no_browser:
        threading.Timer(2.0, lambda: webbrowser.open(url)).start()
    uvicorn.run("app.server:app", host=a.host, port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
