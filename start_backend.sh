#!/bin/bash

# Start Docker container
echo "Starting PostgreSQL container..."
docker start budget_buddy_db

# Wait for DB to be ready (optional, but good practice)
echo "Waiting for database to be ready..."
sleep 3

# Check if migration is needed (optional)
# npx prisma migrate deploy

# Start Node.js server
echo "Starting backend server..."
# Kill any existing node process on port 3000
echo "Checking for existing process on port 3000..."

# Try fuser
if command -v fuser &> /dev/null; then
    fuser -k 3000/tcp || true
fi

# Try lsof
if command -v lsof &> /dev/null; then
    PID=$(lsof -t -i:3000)
    if [ -n "$PID" ]; then
        kill -9 $PID || true
    fi
fi

# Try netstat/ss as fallback if needed (usually harder to parse reliably in dash/bash without tools)
# But strictly, if the above fail, we might just fail.


nohup node server.js > server.log 2>&1 &
echo "Backend server started with PID $!"
echo "Check server.log for output."