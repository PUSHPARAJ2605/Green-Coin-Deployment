const photoInput = document.getElementById('photoInput');
const photoPreview = document.getElementById('photoPreview');
const previewImg = document.getElementById('previewImg');
const removePhoto = document.getElementById('removePhoto');
const reportForm = document.getElementById('reportForm');

photoInput.addEventListener('change', function() {
    const file = this.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImg.src = e.target.result;
            photoPreview.style.display = 'block';
        }
        reader.readAsDataURL(file);
    }
});

removePhoto.addEventListener('click', () => {
    photoInput.value = '';
    photoPreview.style.display = 'none';
});

reportForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('access');
    const formData = new FormData();
    
    // Get location first
    navigator.geolocation.getCurrentPosition(async pos => {
        const reportError = document.getElementById('reportError');
        reportError.style.display = 'none';
        
        formData.append('latitude', pos.coords.latitude);
        formData.append('longitude', pos.coords.longitude);
        formData.append('waste_type', document.getElementById('wasteType').value);
        formData.append('description', document.getElementById('description').value);
        formData.append('photo', photoInput.files[0]);

        const submitBtn = reportForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerText;
        submitBtn.innerText = 'Submitting...';
        submitBtn.disabled = true;

        try {
            const response = await fetch('/api/reports/', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });
            
            if (response.ok) {
                window.location.href = '/success/';
            } else {
                let data;
                try {
                    data = await response.json();
                } catch (e) {
                    throw new Error(`Server returned error ${response.status}: ${response.statusText}`);
                }
                
                const errorStr = JSON.stringify(data).toLowerCase();
                
                if (response.status === 400 && errorStr.includes('penalized')) {
                    window.location.href = '/penalty/';
                } else {
                    let msg = 'Submission failed. Please check form values.';
                    if (data) {
                        if (Array.isArray(data)) msg = data.join('\n');
                        else if (typeof data === 'object') {
                            msg = Object.entries(data).map(([k, v]) => `${v}`).join('\n');
                        }
                    }
                    reportError.innerText = msg;
                    reportError.style.display = 'block';
                }
            }
        } catch (err) {
            console.error(err);
            reportError.innerText = (err.message && err.message.length < 100) ? err.message : 'An error occurred while submitting. Please try again later.';
            reportError.style.display = 'block';
        } finally {
            submitBtn.innerText = originalBtnText;
            submitBtn.disabled = false;
        }
    }, err => {
        const reportError = document.getElementById('reportError');
        reportError.innerText = 'Location access required to report waste.';
        reportError.style.display = 'block';
    }, {
        enableHighAccuracy: true,
        maximumAge: 0,
        timeout: 10000
    });

});

async function loadActivity() {
    const token = localStorage.getItem('access');
    const response = await fetch('/api/rewards/transactions/', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    
    const list = document.getElementById('activityList');
    list.innerHTML = data.map(item => {
        const isPenalty = item.transaction_type === 'penalty';
        const color = isPenalty ? '#EF4444' : 'var(--green-primary)';
        const sign = isPenalty ? '-' : '+';
        
        return `
            <div class="activity-row">
                <div class="activity-icon" style="background: ${isPenalty ? '#FEE2E2' : 'var(--green-pale)'}; color: ${color};">
                    <i class="bi bi-${isPenalty ? 'exclamation-octagon' : 'arrow-down-short'}"></i>
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600;">${item.transaction_type.toUpperCase()}</div>
                    <div style="font-size: 12px; color: var(--text-muted);">${new Date(item.created_at).toLocaleDateString()}</div>
                </div>
                <div style="font-weight: 700; color: ${color};">${sign}${item.amount}</div>
            </div>
        `;
    }).join('');
}


if (document.getElementById('activityList')) {
    loadActivity();
}
