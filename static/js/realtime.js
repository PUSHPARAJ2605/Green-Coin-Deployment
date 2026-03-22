const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
const socket = new WebSocket(`${protocol}://${window.location.host}/ws/reports/`);

socket.onopen = () => console.log('WebSocket Connected');

socket.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);
        if (data.type === 'status_update') {
            const user = JSON.parse(localStorage.getItem('user'));
            
            // Update markers on map if global function exists
            if (window.updateMarker) window.updateMarker(data.report_id, data.status);
            
            if (window.loadReports) window.loadReports();
            if (window.loadActivity) window.loadActivity();
            if (window.loadSummary) window.loadSummary();
            if (window.loadStats) window.loadStats(); // Collector dashboard
        }
    } catch(e) {
        console.error('WebSocket Error processing message:', e);
    }
};

socket.onclose = () => console.log('WebSocket Disconnected');
