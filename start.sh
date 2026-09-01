#!/bin/bash
set -e
echo "Starting E-Commerce Analytics Web Application..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
