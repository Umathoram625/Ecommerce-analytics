import os
import sys
import uvicorn

if __name__ == "__main__":
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    if cur_dir not in sys.path:
        sys.path.insert(0, cur_dir)

    print("=================================================================")
    print("  E-Commerce Sales Analytics Web Application Starting...")
    print("  Dashboard UI: http://localhost:8000")
    print("  API Docs:     http://localhost:8000/api/v1/docs")
    print("=================================================================")

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
