CREATE DATABASE IF NOT EXISTS capstone;
USE capstone;

CREATE TABLE IF NOT EXISTS dummy1 (
    date VARCHAR(100),
    time VARCHAR(100),
    latitude VARCHAR(100),
    longitude VARCHAR(100),
    speed VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dummy2 (
    date VARCHAR(100),
    time VARCHAR(100),
    node VARCHAR(100),
    latitude VARCHAR(100),
    longitude VARCHAR(100),
    speed VARCHAR(100)
);

INSERT INTO dummy1 (date, time, latitude, longitude, speed) VALUES
('2023-05-29', '10:00:00', '-6.200000', '106.816666', '60'),
('2023-05-29', '10:05:00', '-6.201000', '106.817000', '50'),
('2023-05-29', '10:10:00', '-6.202000', '106.818000', '55');

INSERT INTO dummy2 (date, time, node, latitude, longitude, speed) VALUES
('2023-05-29', '10:00:00', 'Node1', '-6.200500', '106.816500', '60'),
('2023-05-29', '10:05:00', 'Node2', '-6.201500', '106.817500', '50'),
('2023-05-29', '10:10:00', 'Node3', '-6.202500', '106.818500', '55');
