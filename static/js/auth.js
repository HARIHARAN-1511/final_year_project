
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(loginForm);
            const errorMsg = document.getElementById('errorMsg');
            const submitBtn = loginForm.querySelector('button[type="submit"]');

            // Disable button during login
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Signing in...';
            }

            try {
                const response = await fetch('/token', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('access_token', data.access_token);
                    window.location.href = '/select';
                } else {
                    errorMsg.style.display = 'block';
                    errorMsg.textContent = 'Incorrect username or password';
                }
            } catch (err) {
                console.error('Login error:', err);
                errorMsg.style.display = 'block';
                errorMsg.textContent = 'Connection error. Please try again.';
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Sign In';
                }
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
        window.location.href = '/';
    }
}

// Logout helper
function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/';
}
