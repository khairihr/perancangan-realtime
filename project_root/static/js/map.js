// Inisialisasi peta (tanpa koordinat awal)
var map = L.map('map');


// Tambahkan layer peta OpenStreetMap
L.tileLayer('/bandung/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 16,
    minZoom: 14,
    tileSize: 512,
    zoomOffset: -1
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
            //map.setView([data.user.latitude, data.user.longitude], 16);

            // Simpan riwayat data awal
            historyData[data.user.node] = [data.user.speed];
            data.others.forEach(vehicle => {
                historyData[vehicle.node] = [vehicle.speed];
            });

            // Tambahkan marker awal
            //updateMap(data);
        } else {
            console.error("Invalid data received from server:", data);
        }
    })
    .catch(error => {
        console.error("Error fetching data from server:", error);
    });

// Fungsi untuk memeriksa potensi bahaya
function checkPotentialHazard(userVehicle, otherVehicles) {
    for (const vehicle of otherVehicles) {
        if (vehicle.distance < vehicle.safe_distance) {
            return true; // Bahaya terdeteksi jika jarak aktual kurang dari jarak aman fuzzy
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

    userMarker.on('move', function() {
        map.setView([data.user.latitude, data.user.longitude], 16);
    });

    // Update atau buat marker untuk kendaraan lain
    data.others.forEach(vehicle => {
        let marker = markers[vehicle.node];
        if (!marker) {
            const otherIcon = L.divIcon({
                className: 'other-vehicle-marker',
                iconSize: [20, 20], // Ukuran ikon
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
}

// Panggil fungsi updateMap secara berkala (misalnya, setiap 1 detik)
setInterval(() => {
    fetch('/get_positions')
        .then(response => response.json())
        .then(data => {
            if (data && data.user && data.others) {
                updateMap(data);

                // Periksa potensi bahaya setelah update marker
                if (checkPotentialHazard([data.user.latitude, data.user.longitude], data.others)) {
                    document.querySelector('.hazard-text').textContent = "WARNING: Potential hazard detected!";
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
        });
}, 1000);

// // Tambahkan event listener untuk mematikan mode follow ketika peta digerakkan secara manual
// map.on('movestart', function() {
//     followUser = false; // Nonaktifkan mode follow ketika pengguna memindahkan peta secara manual
// });
