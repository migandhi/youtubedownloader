// File: static/js/script.js

let eventSource = null;
const statusMessage = document.getElementById('status-message');
const progressBarContainer = document.querySelector('.progress-container');
const progressBar = document.getElementById('progress-bar');
const downloadBtn = document.getElementById('download-btn');

document.getElementById('download-btn').addEventListener('click', async () => {
    const url = document.getElementById('youtube-url').value;
    const format = document.getElementById('format').value;
    const subtitles = document.getElementById('subtitles').checked;

    if (!url) {
        statusMessage.textContent = 'Please enter a YouTube URL.';
        statusMessage.className = 'error';
        return;
    }

    // Disable button and show loading state
    downloadBtn.disabled = true;
    statusMessage.textContent = 'Starting download...';
    statusMessage.className = '';
    progressBarContainer.style.display = 'block';

    try {
        // Step 1: Request the download start
        const response = await fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, format, subtitles }),
        });

        const result = await response.json();

        if (result.success) {
            statusMessage.textContent = result.message;
            const sessionId = result.session_id;

            // Step 2: Connect to the Server-Sent Events stream
            if (eventSource) {
                eventSource.close();
            }
            
            // Connect to the stream using the provided session_id
            eventSource = new EventSource(`/stream/${sessionId}`);

            // Handle incoming data (progress updates)
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                // Update the status message
                statusMessage.textContent = data.message;
                
                // Update the progress bar
                let percentage = parseFloat(data.percent.replace('%', ''));
                if (!isNaN(percentage)) {
                    progressBar.style.width = percentage + '%';
                }

                // Handle download completion or error
                if (data.status === 'finished' || data.status === 'error') {
                    eventSource.close();
                    downloadBtn.disabled = false;
                    
                    if (data.status === 'finished') {
                        statusMessage.className = 'success';
                        progressBar.style.width = '100%';
                    } else {
                        statusMessage.className = 'error';
                        progressBar.style.width = '0%';
                    }
                    
                    // Hide progress bar on completion
                    setTimeout(() => {
                        progressBarContainer.style.display = 'none';
                        progressBar.style.width = '0%';
                    }, 5000); // Keep message visible for 5 seconds
                }
            };

            // Handle stream errors
            eventSource.onerror = (event) => {
                statusMessage.textContent = 'Connection to download stream failed. Check terminal for errors.';
                statusMessage.className = 'error';
                eventSource.close();
                downloadBtn.disabled = false;
            };

        } else {
            statusMessage.textContent = `Error: ${result.message}`;
            statusMessage.className = 'error';
            downloadBtn.disabled = false;
            progressBarContainer.style.display = 'none';
        }

    } catch (error) {
        statusMessage.textContent = 'Failed to connect to the server. Is it running?';
        statusMessage.className = 'error';
        downloadBtn.disabled = false;
        progressBarContainer.style.display = 'none';
    }
});