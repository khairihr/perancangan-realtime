# fuzzy_logic.py
def calculate_safe_distance(current_speed, distance_diff, speed_diff):
    # Fuzzifikasi
    current_speed_low = max(0, 1 - current_speed / 30)  # Kecepatan rendah (0-30 m/s)
    current_speed_medium = max(0, min(current_speed / 30, 1 - (current_speed - 30) / 30))  # Kecepatan sedang (30-60 m/s)
    current_speed_high = max(0, (current_speed - 60) / 30)  # Kecepatan tinggi (60+ m/s)

    distance_diff_close = max(0, 1 - distance_diff / 100)  # Jarak dekat (0-100 m)
    distance_diff_medium = max(0, min(distance_diff / 100, 1 - (distance_diff - 100) / 100))  # Jarak sedang (100-200 m)
    distance_diff_far = max(0, (distance_diff - 200) / 100)  # Jarak jauh (200+ m)

    speed_diff_small = max(0, 1 - speed_diff / 10)  # Selisih kecepatan kecil (0-10 m/s)
    speed_diff_medium = max(0, min(speed_diff / 10, 1 - (speed_diff - 10) / 10))  # Selisih kecepatan sedang (10-20 m/s)
    speed_diff_large = max(0, (speed_diff - 20) / 10)  # Selisih kecepatan besar (20+ m/s)

    # Inferensi (aturan fuzzy)
    # Contoh aturan: Jika kecepatan tinggi DAN jarak dekat, MAKA jarak aman sangat jauh
    safe_distance_very_close = min(current_speed_low, distance_diff_close)
    safe_distance_close = min(current_speed_medium, distance_diff_close)
    safe_distance_medium = min(current_speed_high, distance_diff_close, speed_diff_small)
    safe_distance_far = min(current_speed_high, distance_diff_medium, speed_diff_medium)
    safe_distance_very_far = min(current_speed_high, distance_diff_far, speed_diff_large)

    # Defuzzifikasi (centroid)
    safe_distance = (
        safe_distance_very_close * 10 +
        safe_distance_close * 50 +
        safe_distance_medium * 100 +
        safe_distance_far * 200 +
        safe_distance_very_far * 300
    ) / (
        safe_distance_very_close +
        safe_distance_close +
        safe_distance_medium +
        safe_distance_far +
        safe_distance_very_far
    )

    return safe_distance
