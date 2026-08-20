/**
 * API Client Module
 * Handles all backend API communication.
 */
export class APIClient {
    constructor(baseUrl = '/api') {
        this.baseUrl = baseUrl;
    }

    async uploadFile(file, mode, referenceFile = null) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('mode', mode);

        if (referenceFile) {
            formData.append('reference_file', referenceFile);
        }

        const response = await fetch(`${this.baseUrl}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        return await response.json();
    }

    async getStatus(analysisId) {
        const response = await fetch(`${this.baseUrl}/analysis/${analysisId}/status`);
        if (!response.ok) throw new Error('Failed to fetch status');
        return await response.json();
    }

    async getResults(analysisId) {
        const response = await fetch(`${this.baseUrl}/analysis/${analysisId}/results`);
        if (!response.ok) throw new Error('Failed to fetch results');
        return await response.json();
    }

    async getSummary(analysisId) {
        const response = await fetch(`${this.baseUrl}/analysis/${analysisId}/summary`);
        if (!response.ok) throw new Error('Failed to fetch summary');
        return await response.json();
    }
}
