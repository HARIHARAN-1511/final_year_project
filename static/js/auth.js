
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
                    window.location.href = '/dashboard'; // Redirect to dashboard
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
        window.location.href = '/login';
    }
}
