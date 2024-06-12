// Inisialisasi peta (tanpa koordinat awal)
var map = L.map('map');

// Tambahkan layer peta OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Objek untuk menyimpan marker dan data riwayat
var markers = {};
var historyData = {};

// Ambil data posisi awal dari server
fetch('/get_positions')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data && data.user && data.others) {
            // Atur tampilan awal peta berdasarkan posisi kendaraan pengguna
            map.setView([data.user.latitude, data.user.longitude], 17); // Zoom level 17 untuk tampilan lebih detail

            // Simpan riwayat data awal
            historyData[data.user.node] = [data.user.speed];
            data.others.forEach(vehicle => {
                historyData[vehicle.node] = [vehicle.speed];
            });

            // Tambahkan marker awal
            updateMap(data);
        } else {
            console.error("Invalid data received from server:", data);
        }
    })
    .catch(error => {
        console.error("Error fetching data from server:", error);
        // Tambahkan penanganan error yang sesuai (misalnya, tampilkan pesan kesalahan di UI)
        alert("Gagal memuat peta. Silakan periksa koneksi dan coba lagi.");
    });

// Fungsi untuk memeriksa potensi bahaya
function checkPotentialHazard(userVehicle, otherVehicles) {
    for (const vehicle of otherVehicles) {
        const distance = L.GeometryUtil.distance(map, userVehicle, [vehicle.latitude, vehicle.longitude]);
        const timeDiff = new Date() - new Date(vehicle.time);
        const speedDiff = Math.abs(parseFloat(userVehicle[2]) - parseFloat(vehicle.speed));

        // Hitung jarak aman menggunakan logika fuzzy (panggil fungsi dari fuzzy_logic.py)
        const safeDistance = calculateSafeDistance(parseFloat(userVehicle[2]), distance, speedDiff);

        // Kondisi bahaya: jarak < jarak aman, waktu update < 10 detik, dan penurunan kecepatan drastis
        if (distance < safeDistance && timeDiff < 10000) {
            const prevSpeeds = historyData[vehicle.node] || [];
            if (prevSpeeds.length > 2 && Math.max(...prevSpeeds) - vehicle.speed > 15) { 
                return true;
            }
        }
    }
    return false;
}

// Fungsi untuk memperbarui posisi marker dan menyimpan riwayat
function updateMap(data) {
    // Update atau buat marker untuk kendaraan pengguna
    let userMarker = markers[data.user.node];
    if (!userMarker) {
        const userIcon = L.divIcon({
            className: 'user-vehicle-marker',
            iconSize: [20, 20], // Ukuran ikon
            html: '<div style="background-color: blue; width: 100%; height: 100%; border-radius: 50%;"></div>'
        });
        userMarker = L.marker([data.user.latitude, data.user.longitude], { icon: userIcon }).addTo(map);
        markers[data.user.node] = userMarker;
    }
    userMarker.setLatLng([data.user.latitude, data.user.longitude]);
    userMarker.bindPopup(`User Vehicle<br>Speed: ${data.user.speed} m/s<br>Last Update: ${data.user.time}`); 

    // Update atau buat marker untuk kendaraan lain
    data.others.forEach(vehicle => {
        let marker = markers[vehicle.node];
        if (!marker) {
            const otherIcon = L.divIcon({
                className: 'other-vehicle-marker',
                iconSize: [20, 20], 
                html: '<div style="background-color: red; width: 100%; height: 100%; border-radius: 50%;"></div>'
            });
            marker = L.marker([vehicle.latitude, vehicle.longitude], { icon: otherIcon }).addTo(map);
            markers[vehicle.node] = marker;
        }

        marker.setLatLng([vehicle.latitude, vehicle.longitude]);

        // Hitung arah pergerakan (menggunakan bearing)
        if (historyData[vehicle.node] && historyData[vehicle.node].length > 0) {
            const prevLatLng = historyData[vehicle.node][historyData[vehicle.node].length - 1];
            const direction = L.GeometryUtil.bearing([prevLatLng.latitude, prevLatLng.longitude], [vehicle.latitude, vehicle.longitude]);
            marker.bindPopup(`Node: ${vehicle.node}<br>Speed: ${vehicle.speed} m/s<br>Direction: ${Math.round(direction)}°<br>Last Update: ${vehicle.time}`);
        } else {
            marker.bindPopup(`Node: ${vehicle.node}<br>Speed: ${vehicle.speed} m/s<br>Last Update: ${vehicle.time}`);
        }

        // Simpan riwayat data (maksimal 3 data terakhir)
        historyData[vehicle.node] = historyData[vehicle.node] || [];
        historyData[vehicle.node].push({ latitude: vehicle.latitude, longitude: vehicle.longitude, speed: vehicle.speed });
        if (historyData[vehicle.node].length > 3) {
            historyData[vehicle.node].shift(); 
        }
    });

    // Setelah memperbarui marker, pindahkan peta ke lokasi pengguna
    map.setView([data.user.latitude, data.user.longitude], 17); // Zoom level 17 untuk tampilan lebih detail
}

// Panggil fungsi updateMap secara berkala (misalnya, setiap 5 detik)
setInterval(() => {
    fetch('/get_positions')
        .then(response => response.json())
        .then(data => {
            if (data && data.user && data.others) {
                updateMap(data);
    
                // Periksa potensi bahaya setelah update marker
                if (checkPotentialHazard([data.user.latitude, data.user.longitude, data.user.speed], data.others)) {
                    document.getElementById('hazard-notification').style.display = 'block';
                } else {
                    document.getElementById('hazard-notification').style.display = 'none';
                }
            } else {
                console.error("Invalid data received from server:", data);
            }
        })
        .catch(error => {
            console.error("Error fetching data from server:", error);
            // Tambahkan alert sebagai penanganan error
            alert("Terjadi kesalahan saat mengambil data dari server. Silakan periksa koneksi Anda.");
        });
}, 1000);


// Fungsi untuk memusatkan peta ke lokasi pengguna
function centerMapOnUser() {
    if (markers && markers['user']) { 
        map.setView(markers['user'].getLatLng(), 17); // Zoom level 17 untuk tampilan lebih detail
    } else {
        console.warn("Marker pengguna belum ada di peta.");
    }
}

// Fungsi untuk menghitung jarak aman (logika fuzzy)
function calculateSafeDistance(currentSpeed, distanceDiff, speedDiff) {
    // Fuzzifikasi
    const speedLow = Math.max(0, 1 - currentSpeed / 30);  // Kecepatan rendah (0-30 m/s)
    const speedMedium = Math.max(0, Math.min(currentSpeed / 30, 1 - (currentSpeed - 30) / 30));  // Kecepatan sedang (30-60 m/s)
    const speedHigh = Math.max(0, (currentSpeed - 60) / 30);  // Kecepatan tinggi (60+ m/s)

    const distanceClose = Math.max(0, 1 - distanceDiff / 100);  // Jarak dekat (0-100 m)
    const distanceMedium = Math.max(0, Math.min(distanceDiff / 100, 1 - (distanceDiff - 100) / 100));  // Jarak sedang (100-200 m)
    const distanceFar = Math.max(0, (distanceDiff - 200) / 100);  // Jarak jauh (200+ m)

    const speedDiffSmall = Math.max(0, 1 - speedDiff / 10);  // Selisih kecepatan kecil (0-10 m/s)
    const speedDiffMedium = Math.max(0, Math.min(speedDiff / 10, 1 - (speedDiff - 10) / 10));  // Selisih kecepatan sedang (10-20 m/s)
    const speedDiffLarge = Math.max(0, (speedDiff - 20) / 10);  // Selisih kecepatan besar (20+ m/s)

    const safeDistanceVeryClose = Math.min(speedLow, distanceClose);
    const safeDistanceClose = Math.min(speedMedium, distanceClose);
    const safeDistanceMedium = Math.min(speedHigh, distanceClose, speedDiffSmall);
    const safeDistanceFar = Math.min(speedHigh, distanceMedium, speedDiffMedium);
    const safeDistanceVeryFar = Math.min(speedHigh, distanceFar, speedDiffLarge);

    // Defuzzifikasi (centroid)
    const numerator = (
        safeDistanceVeryClose * 10 +
        safeDistanceClose * 50 +
        safeDistanceMedium * 100 +
        safeDistanceFar * 200 +
        safeDistanceVeryFar * 300
    );
    const denominator = (
        safeDistanceVeryClose +
        safeDistanceClose +
        safeDistanceMedium +
        safeDistanceFar +
        safeDistanceVeryFar
    );

    const safeDistance = numerator / denominator;

    return safeDistance;
}
