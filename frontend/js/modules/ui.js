/**
 * UI Modules
 * Classes for handling different views.
 */

// Toast Notification System
export class Toast {
    static container = null;

    static init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    }

    static show(type, title, message, duration = 5000) {
        this.init();

        const icons = {
            success: 'bi-check-circle',
            error: 'bi-x-circle',
            warning: 'bi-exclamation-triangle',
            info: 'bi-info-circle'
        };

        const toast = document.createElement('div');
        toast.className = `toast toast-${type} animate-slide-in-right`;
        toast.innerHTML = `
            <div class="toast-icon"><i class="bi ${icons[type]}"></i></div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close"><i class="bi bi-x"></i></button>
        `;

        this.container.appendChild(toast);

        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.dismiss(toast));

        if (duration > 0) {
            setTimeout(() => this.dismiss(toast), duration);
        }

        return toast;
    }

    static dismiss(toast) {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 200);
    }

    static success(title, message) { return this.show('success', title, message); }
    static error(title, message) { return this.show('error', title, message); }
    static warning(title, message) { return this.show('warning', title, message); }
    static info(title, message) { return this.show('info', title, message); }
}

export class ThemeManager {
    constructor() {
        this.toggleBtn = document.getElementById('themeToggle');
        this.icon = this.toggleBtn?.querySelector('i');
        // Check localStorage -> system preference -> default to light
        this.theme = localStorage.getItem('theme') ||
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        this.init();
    }

    init() {
        this.applyTheme(this.theme);
        this.toggleBtn?.addEventListener('click', () => this.toggleTheme());

        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        this.applyTheme(this.theme);
        Toast.info('Theme Changed', `Switched to ${this.theme} mode`);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        document.body.setAttribute('data-theme', theme);
        if (this.icon) {
            this.icon.className = theme === 'light' ? 'bi bi-moon-stars' : 'bi bi-sun';
        }
    }
}

export class UploadView {
    constructor(apiClient) {
        this.api = apiClient;
        this.uploadArea = document.getElementById('uploadArea');
        this.fileInput = document.getElementById('fileInput');
        this.filePreview = document.getElementById('filePreview');
        this.uploadProgress = document.getElementById('uploadProgress');
        this.uploadActions = document.getElementById('uploadActions');
        this.analyzeBtn = document.getElementById('analyzeBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.browseBtn = document.getElementById('browseBtn');
        this.clearRefBtn = document.getElementById('clearRefBtn');

        this.selectedFile = null;

        this.init();
    }

    init() {
        // Theme Manager is global, but initialized in app.js. 
        // We focus on Upload view specific events here.

        if (!this.uploadArea) return;

        // Drag and Drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, (e) => this.preventDefaults(e), false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => this.uploadArea.classList.add('dragover'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => this.uploadArea.classList.remove('dragover'), false);
        });

        this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e), false);
        this.uploadArea.addEventListener('click', () => this.fileInput?.click());

        // File Inputs
        this.fileInput?.addEventListener('change', (e) => this.handleFileSelect(e));

        // Buttons
        this.browseBtn?.addEventListener('click', (e) => {
            e.stopPropagation(); // Avoid triggering uploadArea click
            this.fileInput?.click();
        });

        this.analyzeBtn?.addEventListener('click', () => this.upload());
        this.clearBtn?.addEventListener('click', () => this.clearFile());

        this.clearRefBtn?.addEventListener('click', () => {
            const refInput = document.getElementById('referenceInput');
            if (refInput) refInput.value = '';
        });
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleDrop(e) {
        const files = e.dataTransfer.files;
        if (files.length > 0) this.handleFile(files[0]);
    }

    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) this.handleFile(files[0]);
    }

    handleFile(file) {
        const validExtensions = ['.pdf', '.docx', '.xlsx'];
        const ext = '.' + file.name.split('.').pop().toLowerCase();

        if (!validExtensions.includes(ext)) {
            this.showError('Invalid file type. Please upload PDF, DOCX, or XLSX files.');
            return;
        }

        if (file.size > 50 * 1024 * 1024) {
            this.showError('File too large. Maximum size is 50MB.');
            return;
        }

        this.selectedFile = file;
        this.showPreview(file);
    }

    showPreview(file) {
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileSize').textContent = this.formatFileSize(file.size);

        const ext = file.name.split('.').pop().toLowerCase();
        const iconEl = document.getElementById('fileIcon');
        if (iconEl) {
            let iconClass = 'bi-file-earmark';
            if (ext === 'pdf') iconClass = 'bi-file-earmark-pdf text-danger';
            else if (ext === 'docx') iconClass = 'bi-file-earmark-word text-primary';
            else if (ext === 'xlsx') iconClass = 'bi-file-earmark-excel text-success';
            iconEl.innerHTML = `<i class="bi ${iconClass}"></i>`;
        }

        this.uploadArea.classList.add('d-none');
        this.filePreview.classList.remove('d-none');
        this.uploadActions.classList.remove('d-none');
    }

    clearFile() {
        this.selectedFile = null;
        if (this.fileInput) this.fileInput.value = '';
        this.uploadArea.classList.remove('d-none');
        this.filePreview.classList.add('d-none');
        this.uploadActions.classList.add('d-none');
        this.uploadProgress.classList.add('d-none');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + ['Bytes', 'KB', 'MB'][i];
    }

    async upload() {
        if (!this.selectedFile) return;

        this.setLoading(true);
        this.updateProgress(10, 'Uploading document...');

        try {
            const mode = document.querySelector('input[name="analysisMode"]:checked').value;
            const refInput = document.getElementById('referenceInput');
            const refFile = (refInput && refInput.files.length > 0) ? refInput.files[0] : null;

            const data = await this.api.uploadFile(this.selectedFile, mode, refFile);

            this.updateProgress(100, 'Upload complete!');
            setTimeout(() => {
                window.location.href = `/status/${data.analysis_id}`;
            }, 1000);

        } catch (error) {
            console.error(error);
            this.showError(error.message);
            this.setLoading(false);
            this.clearFile();
        }
    }

    setLoading(isLoading) {
        if (this.analyzeBtn) this.analyzeBtn.disabled = isLoading;
        if (isLoading) {
            this.filePreview.classList.add('d-none');
            this.uploadActions.classList.add('d-none');
            this.uploadProgress.classList.remove('d-none');
        }
    }

    updateProgress(percent, status) {
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        const progressStatus = document.getElementById('progressStatus');

        if (progressBar) progressBar.style.width = percent + '%';
        if (progressPercent) progressPercent.textContent = percent + '%';
        if (progressStatus) progressStatus.textContent = status;
    }

    showError(msg) {
        Toast.error('Upload Error', msg);
    }

    showSuccess(msg) {
        Toast.success('Success', msg);
    }
}

export class StatusView {
    constructor(apiClient, analysisId) {
        this.api = apiClient;
        this.analysisId = analysisId;
        this.pollingInterval = null;
        this.init();
    }

    init() {
        this.startPolling();
    }

    async poll() {
        try {
            const data = await this.api.getStatus(this.analysisId);
            this.updateUI(data);

            if (data.status === 'completed') {
                this.stopPolling();
                setTimeout(() => window.location.href = `/results/${this.analysisId}`, 1500);
            } else if (data.status === 'failed') {
                this.stopPolling();
                alert('Analysis failed: ' + (data.error_message || 'Unknown error'));
            }
        } catch (error) {
            console.error('Poll error', error);
        }
    }

    updateUI(data) {
        const statusText = document.getElementById('statusText');
        const statusProgress = document.getElementById('statusProgress');

        const map = {
            'pending': { text: 'Queued...', progress: 20 },
            'in_progress': { text: 'Analyzing...', progress: 60 },
            'completed': { text: 'Complete!', progress: 100 },
            'failed': { text: 'Failed', progress: 0 }
        };

        const info = map[data.status] || { text: 'Processing...', progress: 40 };
        if (statusText) statusText.textContent = info.text;
        if (statusProgress) statusProgress.style.width = info.progress + '%';
    }

    startPolling() {
        this.poll();
        this.pollingInterval = setInterval(() => this.poll(), 2000);
    }

    stopPolling() {
        if (this.pollingInterval) clearInterval(this.pollingInterval);
    }
}

export class ResultsView {
    constructor(apiClient, analysisId) {
        this.api = apiClient;
        this.analysisId = analysisId;
        this.init();
    }

    async init() {
        try {
            const data = await this.api.getResults(this.analysisId);
            this.render(data);
        } catch (error) {
            console.error(error);
            alert('Failed to load results');
        }
    }

    render(data) {
        // Expose data globally for legacy scripts or render logic here
        // Since original app.js relied on results.html scripts for rendering charts,
        // we can dispatch an event or call a global function.
        if (window.renderResultsData) {
            window.renderResultsData(data);
        }
    }
}

export class SummaryView {
    constructor(apiClient, analysisId) {
        this.api = apiClient;
        this.analysisId = analysisId;
        this.init();
    }

    async init() {
        try {
            const data = await this.api.getSummary(this.analysisId);
            this.render(data);
        } catch (error) {
            console.error(error);
            alert('Failed to load summary');
        }
    }

    render(data) {
        if (window.renderSummaryData) {
            window.renderSummaryData(data);
        }
    }
}
