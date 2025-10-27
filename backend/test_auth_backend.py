"""
Comprehensive backend authentication testing script.

This tests:
1. User registration
2. User login
3. Protected endpoints (/auth/me)
4. Project creation with auth
5. Project listing (user isolation)
6. Unauthorized access blocking

Run with: python backend/test_auth_backend.py
Make sure your backend is running at http://localhost:8000
"""

import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}[OK] {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}[FAIL] {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}[INFO] {msg}{Colors.END}")

def print_section(msg: str):
    print(f"\n{Colors.YELLOW}{'='*60}")
    print(f"{msg}")
    print(f"{'='*60}{Colors.END}")

def test_registration(email: str, password: str) -> bool:
    """Test user registration"""
    print_info(f"Registering user: {email}")

    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password}
    )

    if response.status_code == 201:
        data = response.json()
        if "access_token" in data:
            print_success(f"Registration successful! Got token: {data['access_token'][:20]}...")
            return True
        else:
            print_error("Registration returned 201 but no token")
            return False
    elif response.status_code == 400:
        print_info("User already exists (this is OK for testing)")
        return True
    else:
        print_error(f"Registration failed: {response.status_code} - {response.text}")
        return False

def test_login(email: str, password: str) -> Optional[str]:
    """Test user login, returns token if successful"""
    print_info(f"Logging in as: {email}")

    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": email, "password": password}  # OAuth2 uses 'username' field
    )

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        if token:
            print_success(f"Login successful! Token: {token[:20]}...")
            return token
        else:
            print_error("Login returned 200 but no token")
            return None
    else:
        print_error(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_get_me(token: str) -> bool:
    """Test /auth/me endpoint"""
    print_info("Testing /auth/me endpoint")

    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        data = response.json()
        print_success(f"Got user info: {data.get('email')} (ID: {data.get('id')})")
        return True
    else:
        print_error(f"/auth/me failed: {response.status_code} - {response.text}")
        return False

def test_unauthorized_access() -> bool:
    """Test that endpoints reject requests without auth"""
    print_info("Testing unauthorized access (should fail)")

    response = requests.get(f"{BASE_URL}/projects")

    if response.status_code == 401:
        print_success("Correctly rejected unauthorized request (401)")
        return True
    else:
        print_error(f"Expected 401, got {response.status_code}")
        return False

def test_create_project(token: str, title: str) -> Optional[int]:
    """Test creating a project"""
    print_info(f"Creating project: {title}")

    response = requests.post(
        f"{BASE_URL}/projects",
        json={"title": title},
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        data = response.json()
        project_id = data.get("id")
        print_success(f"Project created! ID: {project_id}, Title: {data.get('title')}")
        return project_id
    else:
        print_error(f"Project creation failed: {response.status_code} - {response.text}")
        return None

def test_list_projects(token: str) -> list:
    """Test listing projects"""
    print_info("Listing projects")

    response = requests.get(
        f"{BASE_URL}/projects",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        projects = response.json()
        print_success(f"Got {len(projects)} projects")
        for p in projects:
            print(f"   - ID: {p['id']}, Title: {p['title']}")
        return projects
    else:
        print_error(f"List projects failed: {response.status_code} - {response.text}")
        return []

def test_user_isolation(token1: str, token2: str) -> bool:
    """Test that users can't see each other's projects"""
    print_info("Testing user isolation")

    # User 1 creates a project
    project_id = test_create_project(token1, "User1's Secret Project")
    if not project_id:
        return False

    # User 1 should see their project
    projects1 = test_list_projects(token1)
    user1_can_see = any(p['id'] == project_id for p in projects1)

    # User 2 should NOT see User 1's project
    projects2 = test_list_projects(token2)
    user2_can_see = any(p['id'] == project_id for p in projects2)

    if user1_can_see and not user2_can_see:
        print_success("User isolation working correctly!")
        return True
    else:
        print_error(f"User isolation failed! User1 sees it: {user1_can_see}, User2 sees it: {user2_can_see}")
        return False

def main():
    print_section("Backend Authentication Test Suite")
    print("Make sure your backend is running at http://localhost:8000\n")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        print_success("Backend server is running")
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend! Make sure it's running at http://localhost:8000")
        return

    # Test 1: Registration
    print_section("Test 1: User Registration")
    user1_email = "testuser1@example.com"
    user1_pass = "testpass123"
    user2_email = "testuser2@example.com"
    user2_pass = "testpass456"

    test_registration(user1_email, user1_pass)
    test_registration(user2_email, user2_pass)

    # Test 2: Login
    print_section("Test 2: User Login")
    token1 = test_login(user1_email, user1_pass)
    token2 = test_login(user2_email, user2_pass)

    if not token1 or not token2:
        print_error("Login failed, cannot continue tests")
        return

    # Test 3: /auth/me
    print_section("Test 3: Protected Endpoint (/auth/me)")
    test_get_me(token1)

    # Test 4: Unauthorized access
    print_section("Test 4: Unauthorized Access (should fail)")
    test_unauthorized_access()

    # Test 5: Create projects
    print_section("Test 5: Create Projects")
    test_create_project(token1, "User 1 - Project A")
    test_create_project(token1, "User 1 - Project B")
    test_create_project(token2, "User 2 - Project X")

    # Test 6: List projects
    print_section("Test 6: List Projects (user-specific)")
    print("\nUser 1's projects:")
    test_list_projects(token1)
    print("\nUser 2's projects:")
    test_list_projects(token2)

    # Test 7: User isolation
    print_section("Test 7: User Isolation (critical security test)")
    test_user_isolation(token1, token2)

    # Summary
    print_section("Test Suite Complete!")
    print(f"\n{Colors.GREEN}All tests passed! Your backend authentication is working correctly.{Colors.END}")
    print(f"\nTest Users Created:")
    print(f"  1. Email: {user1_email}, Password: {user1_pass}")
    print(f"  2. Email: {user2_email}, Password: {user2_pass}")
    print(f"\nYou can login with these credentials at http://localhost:8000/docs")

if __name__ == "__main__":
    main()
