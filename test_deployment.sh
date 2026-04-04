#!/bin/bash

# Test Deployment Script for Kuraz AI
# Usage: ./test_deployment.sh https://your-app-name.onrender.com

if [ -z "$1" ]; then
    echo "❌ Error: Please provide your Render URL"
    echo "Usage: ./test_deployment.sh https://your-app-name.onrender.com"
    exit 1
fi

BASE_URL=$1
echo "🧪 Testing Kuraz AI deployment at: $BASE_URL"
echo "================================================"
echo ""

# Test 1: Root endpoint
echo "1️⃣  Testing root endpoint..."
curl -s "$BASE_URL/" | head -n 5
echo ""
echo ""

# Test 2: Health check
echo "2️⃣  Testing health check..."
curl -s "$BASE_URL/api/health"
echo ""
echo ""

# Test 3: Seed database
echo "3️⃣  Seeding database..."
curl -s -X POST "$BASE_URL/api/seed"
echo ""
echo ""

# Test 4: Get room types
echo "4️⃣  Getting room types..."
curl -s "$BASE_URL/api/room-types" | head -n 10
echo ""
echo ""

# Test 5: Dashboard KPIs
echo "5️⃣  Getting dashboard KPIs..."
curl -s "$BASE_URL/api/dashboard/kpis"
echo ""
echo ""

echo "================================================"
echo "✅ Testing complete!"
echo ""
echo "📚 View full API docs at: $BASE_URL/docs"
echo ""
