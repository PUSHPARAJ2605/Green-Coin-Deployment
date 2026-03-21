let map, userMarker;
const reports = [];

function initMap(lat = 13.1000, lng = 80.1000) {
    map = L.map('map').setView([lat, lng], 14);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Get initial location but don't track or show marker
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(pos => {
            const { latitude, longitude } = pos.coords;
            map.setView([latitude, longitude], 14);
        }, err => console.error("Location error:", err), {
            enableHighAccuracy: true
        });
    }

    loadReports();
}


function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws/reports/`);

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'status_update') {
            if (typeof loadReports === 'function' && document.getElementById('map')) {
                loadReports(); // Refresh markers if on dashboard
            }
            
            // Check if this update affects the current user's balance
            const currentUser = JSON.parse(localStorage.getItem('user'));
            if (currentUser && data.user_id === currentUser.id) {
                // Update local storage balance
                currentUser.coins = data.new_balance;
                localStorage.setItem('user', JSON.stringify(currentUser));
                
                // Refresh activity log if present
                if (typeof loadActivity === 'function') loadActivity();
                
                // Refresh transaction history if on redeem page
                if (typeof loadRedeemData === 'function') loadRedeemData();
                
                // Refresh balance display if present
                const balanceDisplay = document.getElementById('balanceDisplay');
                if (balanceDisplay) {
                    balanceDisplay.innerHTML = `${data.new_balance} <i class="bi bi-coin" style="color: #FFD700;"></i>`;
                }
            }
        }
    };

    socket.onclose = () => setTimeout(initWebSocket, 5000);
}


async function loadReports() {
    const token = localStorage.getItem('access');
    const response = await fetch('/api/reports/', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    
    data.forEach(report => {
        let markerColor = '#1565C0'; // Rich Blue for pending
        if (report.status === 'picking') markerColor = '#D97706'; // Rich Amber for picking
        if (report.status === 'collected') markerColor = '#2E7D32'; // Rich Green for collected
        
        const marker = L.circleMarker([report.latitude, report.longitude], {
            radius: 8,
            fillColor: markerColor,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);

        marker.bindPopup(`
            <div style="font-family: 'Inter', sans-serif;">
                <div class="status-badge status-${report.status}" style="margin-bottom:5px;">${report.status}</div>
                <div style="font-weight:700; color:var(--green-primary);">+${report.coins_awarded} Coins</div>
                <p style="font-size:12px; margin-top:5px;">${report.description}</p>
            </div>
        `);
    });
}


document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('map')) initMap();
    if (localStorage.getItem('access')) initWebSocket();
});
