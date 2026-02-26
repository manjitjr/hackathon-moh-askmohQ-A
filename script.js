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
            aiStatus.textContent = 'Govtech AIBot • Smart & Secure';
            aiStatus.style.color = '#00a651';
        } else {
            aiStatus.textContent = 'Rule-based • Fast & Free';
            aiStatus.style.color = '#7f8c8d';
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

    // Upload and process
    uploadBtn.addEventListener('click', async () => {
        if (!selectedFile) return;
        
        uploadBtn.disabled = true;
        statusSection.style.display = 'block';
        resultsSection.style.display = 'none';
        
        updateStatus('Uploading file...', 20);
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('use_llm', aiToggle.checked ? 'true' : 'false');
                console.log('🎚️ AI Toggle:', aiToggle.checked ? 'ON (AI Enabled)' : 'OFF (Rule-based)');
                try {
            updateStatus(aiToggle.checked ? 'Processing with AI...' : 'Processing Excel file...', 40);
            
            const response = await fetch('http://localhost:5000/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Upload failed');
            }
            
            updateStatus('Cleaning and formatting data...', 70);
            
            const result = await response.json();
            cleanedData = result;
            
            updateStatus('Complete!', 100);
            
            setTimeout(() => {
                displayResults(result);
            }, 500);
            
        } catch (error) {
            alert('Error processing file: ' + error.message + '\n\nMake sure the Flask server is running on port 5000');
            statusSection.style.display = 'none';
            uploadBtn.disabled = false;
        }
    });

    function updateStatus(message, progress) {
        statusMessage.textContent = message;
        progressFill.style.width = progress + '%';
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
        
        let csv = 'Category,Question,Answer\n';
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
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'cleaned_qa_data.xlsx';
            a.click();
        } catch (error) {
            alert('Error downloading Excel file: ' + error.message);
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
