@echo off
echo Testing Authentication Endpoints
echo.
echo ================================
echo 1. Testing Register Endpoint
echo ================================
curl -X POST "http://localhost:8000/auth/register" -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\",\"password\":\"password123\"}"
echo.
echo.
echo ================================
echo 2. Testing Login Endpoint
echo ================================
curl -X POST "http://localhost:8000/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=test@example.com&password=password123"
echo.
echo.
echo ================================
echo 3. Testing Duplicate Register (should fail)
echo ================================
curl -X POST "http://localhost:8000/auth/register" -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\",\"password\":\"password123\"}"
echo.
echo.
echo ================================
echo Tests Complete!
echo ================================
echo.
echo To test /auth/me endpoint, copy the access_token from above
echo and run: curl -X GET "http://localhost:8000/auth/me" -H "Authorization: Bearer YOUR_TOKEN_HERE"
pause
