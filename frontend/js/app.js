/**
 * Main Application Entry Point
 * Orchestrates modules based on the current page.
 */
import { APIClient } from './modules/api.js';
import { UploadView, StatusView, ResultsView, SummaryView, ThemeManager } from './modules/ui.js';

document.addEventListener('DOMContentLoaded', () => {
    const api = new APIClient();
    new ThemeManager();
    const path = window.location.pathname;

    console.log("Initializing App for path:", path);

    if (path === '/' || path.includes('index.html')) {
        new UploadView(api);
    }
    else if (path.startsWith('/status/')) {
        const id = path.split('/').pop();
        new StatusView(api, id);
    }
    else if (path.startsWith('/results/')) {
        const id = path.split('/').pop();
        new ResultsView(api, id);
    }
    else if (path.startsWith('/summary/')) {
        const id = path.split('/').pop();
        new SummaryView(api, id);
    }
});
