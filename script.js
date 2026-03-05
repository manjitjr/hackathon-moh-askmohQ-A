let selectedFile = null;
let cleanedData = null;

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const statusSection = document.getElementById('statusSection');
    const resultsSection = document.getElementById('resultsSection');
    const statusMessage = document.getElementById('statusMessage');
    const progressFill = document.getElementById('progressFill');
    const aiToggle = document.getElementById('aiToggle');
    const aiStatus = document.getElementById('aiStatus');
    
    // Load AI toggle state from localStorage
    const savedAiState = localStorage.getItem('useAI') === 'true';
    aiToggle.checked = savedAiState;
    updateAiStatus();
    
    // Handle AI toggle changes
    aiToggle.addEventListener('change', function() {
        localStorage.setItem('useAI', aiToggle.checked);
        updateAiStatus();
        
        // Show info about AI requirement
        if (aiToggle.checked) {
            console.log('✅ AI Mode Enabled - Govtech AIBot will be used if configured');
            console.log('📝 To set up: Add AIBOT_API_KEY to .env file');
        } else {
            console.log('⚡ Rule-based Mode - Fast processing without API calls');
        }
    });
    
    function updateAiStatus() {
        if (aiToggle.checked) {
            aiStatus.textContent = 'Govtech AIBot';
            aiStatus.style.color = '#667eea';
        } else {
            aiStatus.textContent = 'Rule-based • Fast & Free';
            aiStatus.style.color = '#64748b';
        }
    }

    // Click to browse
    uploadBox.addEventListener('click', () => {
        console.log('Upload box clicked!');
        fileInput.click();
    });

    // File selection
    fileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files[0]);
    });

    // Drag and drop
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('drag-over');
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('drag-over');
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('drag-over');
        handleFileSelect(e.dataTransfer.files[0]);
    });

    function handleFileSelect(file) {
        if (!file) return;
        
        if (!file.name.match(/\.(xlsx|xls)$/)) {
            alert('Please select a valid Excel file (.xlsx or .xls)');
            return;
        }
        
        selectedFile = file;
        uploadBox.classList.add('file-selected');
        uploadBox.querySelector('h3').textContent = `Selected: ${file.name}`;
        uploadBox.querySelector('p').textContent = `${(file.size / 1024).toFixed(2)} KB`;
        uploadBtn.disabled = false;
    }

    // Upload and process with streaming
    uploadBtn.addEventListener('click', async () => {
        if (!selectedFile) return;
        
        uploadBtn.disabled = true;
        statusSection.style.display = 'block';
        resultsSection.style.display = 'none';
        
        // Clear previous results
        const previewBody = document.getElementById('previewBody');
        if (previewBody) {
            previewBody.innerHTML = '';
        }
        
        updateStatus('Uploading file...', 20);
        showNotification('Upload Started', 'Processing your Excel file...', 'info');
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('use_llm', aiToggle.checked ? 'true' : 'false');
        console.log('🎚️ AI Toggle:', aiToggle.checked ? 'ON (AI Enabled)' : 'OFF (Rule-based)');
        
        try {
            // Use fetch with streaming
            const response = await fetch('http://localhost:5000/upload/stream', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Process SSE stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let totalQuestions = 0;
            let processedData = [];
            let finalStats = null;
            
            while (true) {
                const {done, value} = await reader.read();
                
                if (done) break;
                
                buffer += decoder.decode(value, {stream: true});
                const lines = buffer.split('\\n\\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'start') {
                            totalQuestions = data.total;
                            updateStatus(`Processing ${totalQuestions} questions...`, 30);
                        } else if (data.type === 'progress') {
                            // Update progress bar
                            const progress = 30 + (data.percentage * 0.6); // Scale to 30-90%
                            updateStatus(`Processing question ${data.index} of ${data.total}...`, progress);
                            
                            // Add row to table in real-time
                            processedData.push(data.data);
                            addRowToTable(data.data, data.index);
                            
                            // Show results section if not already visible
                            if (resultsSection.style.display === 'none') {
                                resultsSection.style.display = 'block';
                            }
                        } else if (data.type === 'complete') {
                            cleanedData = {
                                cleaned_data: data.cleaned_data,
                                total_questions: data.total_questions,
                                ...data.stats
                            };
                            finalStats = data.stats;
                            updateStatus('Complete!', 100);
                            
                            // Update stats display
                            updateStatsDisplay(cleanedData);
                            
                            handleApiResponse(response, `Successfully cleaned ${data.total_questions} questions!`);
                        } else if (data.type === 'error') {
                            throw new Error(data.message);
                        }
                    }
                }
            }
            
        } catch (error) {
            console.error('❌ Upload error:', error);
            console.error('Error stack:', error.stack);
            showNotification('Upload Failed', error.message || 'Make sure the Flask server is running on port 5000', 'error');
            statusSection.style.display = 'none';
            uploadBtn.disabled = false;
        }
    });

    function updateStatus(message, progress) {
        statusMessage.textContent = message;
        progressFill.style.width = progress + '%';
        
        // Update percentage display
        const percentageDisplay = document.getElementById('percentageDisplay');
        if (percentageDisplay) {
            percentageDisplay.textContent = Math.round(progress) + '%';
            percentageDisplay.style.animation = 'none';
            setTimeout(() => {
                percentageDisplay.style.animation = 'scaleIn 0.3s ease-out';
            }, 10);
        }
    }

    function addRowToTable(item, index) {
        const previewBody = document.getElementById('previewBody');
        const row = document.createElement('tr');
        row.className = 'fade-in-row';
        row.innerHTML = `
            <td>${index}</td>
            <td><span class="category-badge">${item.category || 'General'}</span></td>
            <td>${item.question}</td>
            <td>${item.answer}</td>
            <td>${item.confidence}</td>
            <td>${item.reason}</td>
        `;
        previewBody.appendChild(row);
        
        // Scroll to bottom to show new row
        const previewTable = document.querySelector('.preview-table');
        if (previewTable) {
            previewTable.scrollTop = previewTable.scrollHeight;
        }
    }
    
    function updateStatsDisplay(data) {
        document.getElementById('totalQuestions').textContent = data.total_questions;
        document.getElementById('removedDuplicates').textContent = data.duplicates_removed;
        document.getElementById('fixedIssues').textContent = data.issues_fixed;
        document.getElementById('sensitiveInfo').textContent = data.sensitive_info_removed || 0;
        document.getElementById('rephrased').textContent = data.questions_rephrased || 0;
    }

    function displayResults(data) {
        statusSection.style.display = 'none';
        resultsSection.style.display = 'block';
        
        document.getElementById('totalQuestions').textContent = data.total_questions;
        document.getElementById('removedDuplicates').textContent = data.duplicates_removed;
        document.getElementById('fixedIssues').textContent = data.issues_fixed;
        document.getElementById('sensitiveInfo').textContent = data.sensitive_info_removed || 0;
        document.getElementById('rephrased').textContent = data.questions_rephrased || 0;
        
        const previewBody = document.getElementById('previewBody');
        previewBody.innerHTML = '';
        
        // Display ALL questions (not just first 10)
        data.cleaned_data.forEach((item, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td><span class="category-badge">${item.category || 'General'}</span></td>
                <td>${item.question}</td>
                <td>${item.answer}</td>
                <td>${item.confidence}</td>
                <td>${item.reason}</td>
            `;
            previewBody.appendChild(row);
        });
        
        uploadBtn.disabled = false;
    }

    // Download handlers
    document.getElementById('downloadJsonBtn').addEventListener('click', () => {
        if (!cleanedData) return;
        downloadFile(
            JSON.stringify(cleanedData.cleaned_data, null, 2),
            'cleaned_qa_data.json',
            'application/json'
        );
    });

    document.getElementById('downloadCsvBtn').addEventListener('click', () => {
        if (!cleanedData) return;
        
        let csv = 'Category,Question,Answer,Confidence,Reason\n';
        cleanedData.cleaned_data.forEach(item => {
            csv += `"${(item.category || 'General').replace(/"/g, '""')}","${item.question.replace(/"/g, '""')}","${item.answer.replace(/"/g, '""')}"\n`;
        });
        
        downloadFile(csv, 'cleaned_qa_data.csv', 'text/csv');
    });

    document.getElementById('downloadExcelBtn').addEventListener('click', async () => {
        if (!cleanedData) return;
        
        try {
            const response = await fetch('http://localhost:5000/download/excel', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(cleanedData.cleaned_data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'cleaned_qa_data.xlsx';
            a.click();
            window.URL.revokeObjectURL(url);
            showNotification('Download Complete', 'Excel file downloaded successfully', 'success');
        } catch (error) {
            console.error('Download error:', error);
            showNotification('Download Failed', error.message, 'error');
        }
    });

    function downloadFile(content, filename, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }
});

// Notification System
function showNotification(title, message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    notification.innerHTML = `
        <div class="notification-icon">${icons[type]}</div>
        <div class="notification-content">
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
        </div>
        <button class="notification-close" onclick="closeNotification(this)">×</button>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        closeNotification(notification.querySelector('.notification-close'));
    }, 5000);
}

function closeNotification(button) {
    const notification = button.closest('.notification');
    notification.classList.add('hiding');
    setTimeout(() => notification.remove(), 300);
}

function handleApiResponse(response, successMessage) {
    const statusCode = response.status;
    
    if (statusCode >= 200 && statusCode < 300) {
        showNotification('Success', successMessage || `Request completed (${statusCode})`, 'success');
        return true;
    } else if (statusCode === 404) {
        showNotification('Not Found', 'API endpoint not found (404)', 'error');
        return false;
    } else if (statusCode === 500) {
        showNotification('Server Error', 'Internal server error (500)', 'error');
        return false;
    } else if (statusCode >= 400 && statusCode < 500) {
        showNotification('Request Error', `Client error (${statusCode})`, 'error');
        return false;
    } else if (statusCode >= 500) {
        showNotification('Server Error', `Server error (${statusCode})`, 'error');
        return false;
    }
    
    return true;
}
