
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(loginForm);
            const errorMsg = document.getElementById('errorMsg');

            try {
                const response = await fetch('/token', {
                    method: 'POST',
                    body: formData // sending as form-data for OAuth2PasswordRequestForm
                });

                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('access_token', data.access_token);
                    // Redirect to saved return URL or dashboard
                    const returnUrl = sessionStorage.getItem('returnUrl') || '/dashboard';
                    sessionStorage.removeItem('returnUrl');
                    window.location.href = returnUrl;
                } else {
                    errorMsg.style.display = 'block';
                }
            } catch (err) {
                console.error('Login error:', err);
                errorMsg.style.display = 'block';
                errorMsg.textContent = 'Connection error. Please try again.';
            }
        });
    }
});

// Helper to get auth header
function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Redirect if not logged in (call this on protected pages)
function requireAuth() {
    if (!localStorage.getItem('access_token')) {
        // Save the full current URL so we can return after login
        sessionStorage.setItem('returnUrl', window.location.href);
        window.location.href = '/login';
    }
}
