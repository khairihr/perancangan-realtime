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
        // Atur tampilan awal peta berdasarkan posisi kendaraan pengguna
        if (data && data.user && data.others) {
            map.setView([data.user.latitude, data.user.longitude], 13); 

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
    });


// Fungsi untuk memeriksa potensi bahaya
function checkPotentialHazard(userVehicle, otherVehicles) {
    for (const vehicle of otherVehicles) {
        const distance = L.GeometryUtil.distance(map, userVehicle, [vehicle.latitude, vehicle.longitude]);
        const timeDiff = new Date() - new Date(vehicle.time);

        // Kondisi bahaya: jarak < 50 meter, kecepatan < 5 m/s, waktu update < 10 detik, dan penurunan kecepatan drastis
        if (distance < 50 && vehicle.speed < 5 && timeDiff < 10000) {
            const prevSpeeds = historyData[vehicle.node] || [];
            if (prevSpeeds.length > 2 && prevSpeeds.every(speed => speed > 20)) { 
                return true;
            }
        }
    }
    return false;
}

// Fungsi untuk memperbarui posisi marker dan menyimpan riwayat
function updateMap(data) {
    for (const vehicle of [data.user, ...data.others]) {
        let marker = markers[vehicle.node];
        if (!marker) {
            // Tentukan ikon marker berdasarkan jenis kendaraan (user atau others)
            const icon = L.icon({
                iconUrl: vehicle.node === data.user.node ? 'https://cdn-icons-png.flaticon.com/512/1828/1828961.png' : 'https://cdn-icons-png.flaticon.com/512/3127/3127899.png',
                iconSize: [32, 32], // Ukuran ikon
            });
            marker = L.marker([vehicle.latitude, vehicle.longitude], {icon: icon}).addTo(map);
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
    }
}


// Panggil fungsi updateMap secara berkala (misalnya, setiap 5 detik)
setInterval(() => {
    fetch('/get_positions')
        .then(response => response.json())
        .then(data => {
            if (data && data.user && data.others) {
                updateMap(data);
    
                // Periksa potensi bahaya setelah update marker
                if (checkPotentialHazard([data.user.latitude, data.user.longitude], data.others)) {
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
            // Tambahkan penanganan error yang sesuai (misalnya, tampilkan pesan kesalahan di UI)
        });
}, 5000);


