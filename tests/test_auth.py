def test_login_page_renders(client, db_session):
    """Test that login page loads with HTTP 200."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Demo Credentials" in response.data


def test_login_success(client, db_session):
    """Test login with valid credentials redirects to dashboard."""
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome back, admin!" in response.data
    assert b"Store Overview" in response.data


def test_login_invalid_password(client, db_session):
    """Test login with invalid password fails and shows alert."""
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'wrongpassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_login_nonexistent_user(client, db_session):
    """Test login with unknown user fails."""
    response = client.post('/login', data={
        'username': 'unknown_user',
        'password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_unauthenticated_access_redirects(client, db_session):
    """Test that unauthenticated requests to protected endpoints redirect to login."""
    endpoints = ['/dashboard', '/products', '/sales', '/stock-history']
    for ep in endpoints:
        response = client.get(ep, follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']


def test_logout(auth_client, db_session):
    """Test that logging out clears session and redirects to login."""
    response = auth_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"You have been safely signed out" in response.data
