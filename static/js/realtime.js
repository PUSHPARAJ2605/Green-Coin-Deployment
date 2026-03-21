const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
const socket = new WebSocket(`${protocol}://${window.location.host}/ws/reports/`);

socket.ononopen = () => console.log('WebSocket Connected');

socket.onmessage = (event) => {
    const data = json.parse(event.data);
    if (data.type === 'status_update') {
        // Notification logic
        const user = JSON.parse(localStorage.getItem('user'));
        
        // Update markers on map if global function exists
        if (window.updateMarker) window.updateMarker(data.report_id, data.status);
        
        // If I am the reporter and it was collected, show success toast
        // (Wait, we need to know who the reporter is, we can fetch that or just show for all if wanted)
        // For now, let's refresh views
        if (window.loadActivity) window.loadActivity();
        if (window.loadSummary) window.loadSummary();
        if (window.loadStats) window.loadStats(); // Collector dashboard
    }
};

socket.onclose = () => console.log('WebSocket Disconnected');

// Fix accidental typos in method names if any
socket.onopen = () => console.log('WebSocket Connected');
socket.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);
        if (data.type === 'status_update') {
            console.log('Status update received:', data);
            if (window.loadReports) window.loadReports();
            if (window.loadActivity) window.loadActivity();
            if (window.loadSummary) window.loadSummary();
            if (window.loadStats) window.loadStats();
        }
    } catch(e) {}
};
