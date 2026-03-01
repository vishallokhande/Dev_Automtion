/* jshint esversion: 11 */
'use strict';

(function () {
    // ==================== CONFIG ====================
    const API = '/api/v1';
    const TOKEN_KEY = 'autoapply_token';
    let pollingInterval = null;
    let isLoginMode = true;
    let allJobs = [];

    // ==================== DOM REFS ====================
    const $ = (id) => document.getElementById(id);
    const $qs = (sel) => document.querySelector(sel);

    const authOverlay = $('auth-overlay');
    const mainLayout = $('main-layout');
    const settingsOverlay = $('settings-overlay');

    // Auth form
    const authForm = $('auth-form');
    const authTitle = $('auth-title');
    const authSubtitle = $('auth-subtitle');
    const authEmail = $('auth-email');
    const authSubmitBtn = $('auth-submit-btn');
    const authToggleLink = $('auth-toggle-link');
    const authToggleText = $('auth-toggle-text');
    const authError = $('auth-error');
    const authSuccess = $('auth-success');

    // Nav elements
    const navAvatar = $('nav-avatar');
    const navEmail = $('nav-email');
    const topNavUser = $('top-nav-user');
    const navSettings = $('nav-settings');
    const sidebarAvatar = $('sidebar-avatar');
    const sidebarName = $('sidebar-user-name');
    const sidebarEmail = $('sidebar-user-email');

    // Settings / profile
    const closeSettings = $qs('.close-settings');
    const logoutBtn = $('logout-btn');
    const profileForm = $('profile-form');
    const profileName = $('profile-name');
    const profileDetails = $('profile-details');
    const saveProfileBtn = $('save-profile-btn');
    const resumeUploadForm = $('resume-upload-form');
    const resumeFile = $('resume-file');
    const fileUploadArea = $('file-upload-area');
    const fileSelectedName = $('file-selected-name');
    const uploadResumeBtn = $('upload-resume-btn');
    const settingsError = $('settings-error');
    const settingsSuccess = $('settings-success');

    // Jobs
    const createJobForm = $('create-job-form');
    const submitBtn = $('submit-btn');
    const refreshBtn = $('refresh-btn');
    const jobsContainer = $('jobs-container');
    const jobTemplate = $('job-card-template');
    const formError = $('form-error');
    const formSuccess = $('form-success');

    // Stats
    const statTotal = $('stat-total');
    const statSuccess = $('stat-success');
    const statPending = $('stat-pending');
    const statFailed = $('stat-failed');

    // Toast
    const toastEl = $('toast');

    // ==================== UTILITY ====================
    function getToken() { return localStorage.getItem(TOKEN_KEY); }
    function setToken(t) { localStorage.setItem(TOKEN_KEY, t); }
    function clearToken() { localStorage.removeItem(TOKEN_KEY); }

    function showAlert(el, msg, persist = false) {
        if (!el) return;
        el.innerHTML = msg;
        el.style.display = 'flex';
        if (!persist) {
            setTimeout(() => { el.style.display = 'none'; }, 30000);
        }
    }

    function hideAlert(el) {
        if (el) el.style.display = 'none';
    }

    function showToast(msg, type = 'info') {
        toastEl.textContent = msg;
        toastEl.className = `toast toast-${type} show`;
        clearTimeout(toastEl._timer);
        toastEl._timer = setTimeout(() => {
            toastEl.classList.remove('show');
        }, 3500);
    }

    function setButtonLoading(btn, loading) {
        if (!btn) return;
        const text = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.btn-spinner');
        btn.disabled = loading;
        if (text) text.style.display = loading ? 'none' : '';
        if (spinner) spinner.style.display = loading ? 'block' : 'none';
    }

    function formatTime(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        return d.toLocaleString(undefined, {
            month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    }

    function initials(email) {
        if (!email) return 'U';
        return email.charAt(0).toUpperCase();
    }

    // ==================== API HELPERS ====================
    async function apiFetch(path, options = {}) {
        const token = getToken();
        const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        // If body is FormData or URLSearchParams, don't set Content-Type
        if (options.body instanceof FormData || options.body instanceof URLSearchParams) {
            delete headers['Content-Type'];
        }

        const res = await fetch(`${API}${path}`, { ...options, headers });
        return res;
    }

    // ==================== AUTH ====================
    function showMainApp(isNewLogin = false) {
        authOverlay.classList.remove('active');
        mainLayout.style.display = 'flex';
        loadUserProfile(isNewLogin);
        fetchJobs();
        startPolling();
    }

    function showAuth() {
        if (pollingInterval) clearInterval(pollingInterval);
        mainLayout.style.display = 'none';
        authOverlay.classList.add('active');
        hideAlert(authError);
        hideAlert(authSuccess);
    }

    // Tab switching
    const tabLogin = document.getElementById('tab-login');
    const tabSignup = document.getElementById('tab-signup');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');

    function switchTab(mode) {
        const isLogin = mode === 'login';
        tabLogin.classList.toggle('active', isLogin);
        tabSignup.classList.toggle('active', !isLogin);
        loginForm.style.display = isLogin ? 'block' : 'none';
        signupForm.style.display = isLogin ? 'none' : 'block';
        hideAlert(authError);
        hideAlert(authSuccess);
    }
    tabLogin.addEventListener('click', () => switchTab('login'));
    tabSignup.addEventListener('click', () => switchTab('signup'));

    // LOGIN
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert(authError);
        hideAlert(authSuccess);
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        const submitBtn = document.getElementById('login-submit-btn');

        if (!email || !password) {
            showAlert(authError, 'Please enter your email and password.');
            return;
        }
        setButtonLoading(submitBtn, true);
        try {
            const res = await fetch(`${API}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            if (res.ok) {
                const data = await res.json();
                setToken(data.access_token);
                showToast('Welcome back!', 'success');
                showMainApp(false);
            } else {
                const data = await res.json().catch(() => ({}));
                showAlert(authError, data.detail || 'Invalid email or password.');
            }
        } catch (err) {
            showAlert(authError, 'Network error. Please try again.');
        } finally {
            setButtonLoading(submitBtn, false);
        }
    });

    // SIGN UP
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert(authError);
        hideAlert(authSuccess);
        const name = document.getElementById('signup-name').value.trim();
        const email = document.getElementById('signup-email').value.trim();
        const password = document.getElementById('signup-password').value;
        const submitBtn = document.getElementById('signup-submit-btn');

        if (!name || !email || !password) {
            showAlert(authError, 'Please fill in all fields.');
            return;
        }
        if (password.length < 6) {
            showAlert(authError, 'Password must be at least 6 characters.');
            return;
        }
        setButtonLoading(submitBtn, true);
        try {
            const res = await fetch(`${API}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });
            if (res.ok) {
                const data = await res.json();
                setToken(data.access_token);
                showToast(`Welcome, ${name}! Your account has been created.`, 'success');
                showMainApp(true);
            } else {
                const data = await res.json().catch(() => ({}));
                showAlert(authError, data.detail || 'Registration failed. Please try again.');
            }
        } catch (err) {
            showAlert(authError, 'Network error. Please try again.');
        } finally {
            setButtonLoading(submitBtn, false);
        }
    });

    // ==================== USER PROFILE ====================
    async function loadUserProfile(checkSetup = false) {
        try {
            const res = await apiFetch('/auth/profile');
            if (!res.ok) {
                if (res.status === 401) { handleUnauthorized(); }
                return;
            }
            const user = await res.json();
            const email = user.email || '';
            const letter = initials(email);

            // Update nav/sidebar
            if (navAvatar) navAvatar.textContent = letter;
            if (navEmail) navEmail.textContent = email;
            if (sidebarAvatar) sidebarAvatar.textContent = letter;
            if (sidebarEmail) sidebarEmail.textContent = email;

            // Profile fields
            const name = user.profile?.full_name || '';
            if (sidebarName) sidebarName.textContent = name || email.split('@')[0] || 'User';
            if (profileName) profileName.value = name;
            if (profileDetails) profileDetails.value = user.profile?.additional_details || '';
            // Note: we never pre-fill the li_at cookie for security — user must paste it each time
            const liCookieInput = document.getElementById('profile-li-cookie');
            if (liCookieInput && user.profile?.linkedin_cookie) {
                liCookieInput.placeholder = '✓ Cookie saved — paste new value to update';
            }

            // Auto-open Profile Settings if profile is incomplete (first login / no name / no resume)
            if (checkSetup) {
                const hasName = !!user.profile?.full_name;
                const hasResume = !!user.profile?.resume_path;
                if (!hasName || !hasResume) {
                    openSettings();
                    showToast(
                        !hasResume
                            ? '⚠️ Please complete your profile and upload your resume before starting automation.'
                            : '⚠️ Please add your Full Name to help with Easy Apply forms.',
                        'warning'
                    );
                    // Show a banner inside the settings modal
                    const banner = document.getElementById('settings-error');
                    if (banner) {
                        banner.textContent = !hasResume
                            ? 'Action required: Upload your resume (PDF) and fill in your name before running automations.'
                            : 'Action required: Add your Full Name to pre-fill Easy Apply forms.';
                        banner.style.display = 'flex';
                    }
                }
            }
        } catch (err) {
            console.error('Profile load error:', err);
        }
    }

    function handleUnauthorized() {
        clearToken();
        showAuth();
        showToast('Session expired. Please sign in again.', 'error');
    }

    // Settings Modals
    topNavUser.addEventListener('click', () => openSettings());
    navSettings.addEventListener('click', (e) => { e.preventDefault(); openSettings(); });
    if ($qs('#sidebar-user')) {
        $qs('#sidebar-user').addEventListener('click', openSettings);
    }

    function openSettings() {
        settingsOverlay.classList.add('active');
        hideAlert(settingsError);
        hideAlert(settingsSuccess);
    }

    closeSettings.addEventListener('click', () => settingsOverlay.classList.remove('active'));

    settingsOverlay.addEventListener('click', (e) => {
        if (e.target === settingsOverlay) settingsOverlay.classList.remove('active');
    });

    logoutBtn.addEventListener('click', () => {
        clearToken();
        if (pollingInterval) clearInterval(pollingInterval);
        settingsOverlay.classList.remove('active');
        showAuth();
        showToast('Signed out successfully.');
    });

    // Save Profile
    profileForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        setButtonLoading(saveProfileBtn, true);
        hideAlert(settingsError);
        hideAlert(settingsSuccess);

        try {
            const liCookieInput = document.getElementById('profile-li-cookie');
            const liCookieValue = liCookieInput ? liCookieInput.value.trim() : null;

            const payload = {
                full_name: profileName.value.trim(),
                additional_details: profileDetails.value.trim()
            };
            // Only include cookie if the user typed something (don't overwrite with empty)
            if (liCookieValue) {
                payload.linkedin_cookie = liCookieValue;
            }

            const res = await apiFetch('/auth/profile', {
                method: 'PUT',
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                showAlert(settingsSuccess, 'Profile saved successfully.');
                await loadUserProfile();
                showToast('Profile updated!', 'success');
            } else {
                const data = await res.json().catch(() => ({}));
                showAlert(settingsError, data.detail || 'Failed to save profile.');
            }
        } catch (err) {
            showAlert(settingsError, 'Network error. Please try again.');
        } finally {
            setButtonLoading(saveProfileBtn, false);
        }
    });

    // File Upload Area
    if (resumeFile && fileUploadArea) {
        resumeFile.addEventListener('change', () => {
            const file = resumeFile.files[0];
            if (file) {
                fileSelectedName.textContent = `✓ ${file.name}`;
                fileSelectedName.style.display = 'flex';
            } else {
                fileSelectedName.style.display = 'none';
            }
        });

        // Drag & drop
        fileUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUploadArea.classList.add('drag-over');
        });

        fileUploadArea.addEventListener('dragleave', () => {
            fileUploadArea.classList.remove('drag-over');
        });

        fileUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUploadArea.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            if (file && file.type === 'application/pdf') {
                // Assign to input
                const dt = new DataTransfer();
                dt.items.add(file);
                resumeFile.files = dt.files;
                fileSelectedName.textContent = `✓ ${file.name}`;
                fileSelectedName.style.display = 'flex';
            } else {
                showToast('Only PDF files are accepted.', 'error');
            }
        });
    }

    // Upload Resume
    resumeUploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const file = resumeFile.files[0];
        if (!file) {
            showAlert(settingsError, 'Please select a PDF file first.');
            return;
        }

        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showAlert(settingsError, 'Only PDF files are allowed.');
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            showAlert(settingsError, 'File is too large. Maximum size is 10MB.');
            return;
        }

        setButtonLoading(uploadResumeBtn, true);
        hideAlert(settingsError);
        hideAlert(settingsSuccess);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const token = getToken();
            const res = await fetch(`${API}/auth/profile/resume`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            if (res.ok) {
                showAlert(settingsSuccess, 'Resume uploaded successfully!');
                showToast('Resume uploaded!', 'success');
                resumeUploadForm.reset();
                fileSelectedName.style.display = 'none';
            } else {
                const data = await res.json().catch(() => ({}));
                showAlert(settingsError, data.detail || 'Upload failed. Please try again.');
            }
        } catch (err) {
            showAlert(settingsError, 'Network error. Please try again.');
        } finally {
            setButtonLoading(uploadResumeBtn, false);
        }
    });

    // ==================== JOBS ====================
    async function fetchJobs(showLoading = false) {
        const token = getToken();
        if (!token) return;

        if (showLoading) {
            jobsContainer.innerHTML = `<div class="empty-state" id="jobs-loading"><div class="spinner"></div><p>Loading automations...</p></div>`;
        }

        try {
            const res = await apiFetch('/jobs');

            if (res.status === 401) { handleUnauthorized(); return; }
            if (!res.ok) return;

            const jobs = await res.json();
            allJobs = jobs;
            renderJobs(jobs);
            updateStats(jobs);
        } catch (err) {
            console.error('Failed to fetch jobs:', err);
        }
    }

    function renderJobs(jobs) {
        if (!jobs || jobs.length === 0) {
            jobsContainer.innerHTML = `
                <div class="empty-state">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    <p>No automations yet. Launch your first one!</p>
                </div>`;
            return;
        }

        // Sort by newest first
        const sorted = [...jobs].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

        jobsContainer.innerHTML = '';
        sorted.forEach((job) => {
            const clone = jobTemplate.content.cloneNode(true);
            const item = clone.querySelector('.job-item');

            // Title
            const titleEl = item.querySelector('.job-title');
            if (titleEl) titleEl.textContent = job.title || 'Untitled';

            // Status badge
            const badge = item.querySelector('.job-status-badge');
            if (badge) {
                const status = (job.status || 'pending').toLowerCase();
                const displayStatus = status === 'success' ? 'success' : status;
                badge.textContent = displayStatus;
                badge.className = `job-status-badge status-${displayStatus}`;
            }

            // Meta: location
            const locationEl = item.querySelector('.location');
            if (locationEl) {
                locationEl.innerHTML = locationEl.innerHTML + (job.location || '');
            }

            // Meta: created at
            const createdEl = item.querySelector('.created-at');
            if (createdEl) {
                createdEl.innerHTML = createdEl.innerHTML + formatTime(job.created_at);
            }

            // Tracking timestamps
            if (job.link_opened_at) {
                const linkWrap = item.querySelector('.link-opened-wrap');
                const linkTime = item.querySelector('.link-opened-time');
                if (linkWrap && linkTime) {
                    linkTime.textContent = formatTime(job.link_opened_at);
                    linkWrap.style.display = 'inline-flex';
                }
            }

            if (job.applied_at) {
                const applyWrap = item.querySelector('.applied-at-wrap');
                const applyTime = item.querySelector('.applied-time');
                if (applyWrap && applyTime) {
                    applyTime.textContent = formatTime(job.applied_at);
                    applyWrap.style.display = 'inline-flex';
                }
            }

            // Keywords
            const keywordsEl = item.querySelector('.job-keywords');
            if (keywordsEl && Array.isArray(job.keywords)) {
                job.keywords.slice(0, 5).forEach((kw) => {
                    const tag = document.createElement('span');
                    tag.className = 'keyword-tag';
                    tag.textContent = kw;
                    keywordsEl.appendChild(tag);
                });
            }

            // Applied Jobs Details
            const appliedListWrap = item.querySelector('.applied-jobs-list');
            if (appliedListWrap && job.applied_jobs_details && job.applied_jobs_details.length > 0) {
                appliedListWrap.style.display = 'block';
                const countBadge = appliedListWrap.querySelector('.applied-jobs-count');
                if (countBadge) countBadge.textContent = job.applied_jobs_details.length;

                const ul = appliedListWrap.querySelector('.applied-jobs-items');
                if (ul) {
                    ul.innerHTML = ''; // clear prototype
                    job.applied_jobs_details.forEach(jobDetail => {
                        const li = document.createElement('li');
                        li.className = 'applied-job-item';

                        const titleSpan = document.createElement('span');
                        titleSpan.className = 'applied-job-title';
                        titleSpan.textContent = jobDetail.title || 'Role';

                        const companySpan = document.createElement('span');
                        companySpan.className = 'applied-job-company';
                        companySpan.textContent = jobDetail.company || 'Company';

                        li.appendChild(titleSpan);
                        li.appendChild(document.createTextNode(' at '));
                        li.appendChild(companySpan);

                        if (jobDetail.link) {
                            const link = document.createElement('a');
                            link.href = jobDetail.link;
                            link.target = '_blank';
                            link.className = 'applied-job-link';
                            link.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>';
                            li.appendChild(link);
                        }
                        ul.appendChild(li);
                    });
                }
            }

            jobsContainer.appendChild(clone);
        });
    }

    function updateStats(jobs) {
        if (!jobs) return;
        const total = jobs.length;
        const success = jobs.filter(j => j.status === 'success').length;
        const pending = jobs.filter(j => j.status === 'pending').length;
        const failed = jobs.filter(j => j.status === 'failed').length;

        animateCount(statTotal, total);
        animateCount(statSuccess, success);
        animateCount(statPending, pending);
        animateCount(statFailed, failed);
    }

    function animateCount(el, target) {
        if (!el) return;
        const start = parseInt(el.textContent, 10) || 0;
        if (start === target) return;
        const step = target > start ? 1 : -1;
        let current = start;
        const timer = setInterval(() => {
            current += step;
            el.textContent = current;
            if (current === target) clearInterval(timer);
        }, 40);
    }

    // Create Job
    createJobForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert(formError);
        hideAlert(formSuccess);

        const title = $('job-title').value.trim();
        const location = $('job-location').value.trim();
        const keywordsRaw = $('job-keywords').value.trim();
        const maxApps = parseInt($('job-max-apps').value, 10) || 5;
        const timeFilterEl = $('job-time-filter');
        const timeFilter = timeFilterEl ? timeFilterEl.value : 'any';

        if (!title || !location || !keywordsRaw) {
            showAlert(formError, 'Please fill in all required fields (Job Title, Location, Keywords).');
            return;
        }

        const keywords = keywordsRaw.split(',').map(k => k.trim()).filter(Boolean);
        if (keywords.length === 0) {
            showAlert(formError, 'Please enter at least one keyword.');
            return;
        }

        setButtonLoading(submitBtn, true);

        try {
            const res = await apiFetch('/jobs', {
                method: 'POST',
                body: JSON.stringify({
                    title,
                    location,
                    keywords,
                    time_filter: timeFilter,
                    max_applications: maxApps
                })
            });

            if (res.status === 401) { handleUnauthorized(); return; }

            if (res.ok) {
                const job = await res.json();
                createJobForm.reset();
                showAlert(formSuccess, `Automation launched! Job ID: ${job.id.substring(0, 8)}...`);
                showToast('Automation launched successfully!', 'success');
                await fetchJobs();
            } else {
                const data = await res.json().catch(() => ({}));
                showAlert(formError, data.detail || 'Failed to create automation. Please try again.');
            }
        } catch (err) {
            showAlert(formError, 'Network error. Please check your connection.');
        } finally {
            setButtonLoading(submitBtn, false);
        }
    });

    // Refresh button
    refreshBtn.addEventListener('click', async () => {
        refreshBtn.style.opacity = '0.5';
        refreshBtn.disabled = true;
        await fetchJobs();
        refreshBtn.style.opacity = '';
        refreshBtn.disabled = false;
        showToast('Jobs refreshed.');
    });

    // Auto-polling every 8 seconds
    function startPolling() {
        if (pollingInterval) clearInterval(pollingInterval);
        pollingInterval = setInterval(() => {
            fetchJobs(false);
        }, 8000);
    }

    // ==================== INIT ====================
    // CRITICAL: Always validate token against the server — never trust localStorage alone.
    // A stale/expired/invalid token must NOT auto-login the user.
    (async function initApp() {
        const token = getToken();
        if (!token) {
            // No token at all → show login
            return;
        }
        try {
            const res = await fetch(`${API}/auth/profile`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                // Token is valid → show main app
                showMainApp();
            } else {
                // Token is invalid or expired → clear it and show login
                clearToken();
                showAuth();
            }
        } catch (err) {
            // Network error — don't auto-login; show auth
            clearToken();
            showAuth();
        }
    })();
})();
