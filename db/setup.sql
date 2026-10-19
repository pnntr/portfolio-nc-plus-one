DROP DATABASE IF EXISTS nc_plus_one;
CREATE DATABASE nc_plus_one;

\c nc_plus_one

DROP TABLE IF EXISTS users;
CREATE TABLE users (
	user_id SERIAL PRIMARY KEY,
	email VARCHAR(255) UNIQUE NOT NULL,
	password VARCHAR(255) NOT NULL,
	name VARCHAR(255) NOT NULL,
	created_at TIMESTAMP DEFAULT NOW()
);

DROP TABLE IF EXISTS venues;
CREATE TABLE venues (
	venue_id SERIAL PRIMARY KEY,
	name VARCHAR(255) NOT NULL,
	address TEXT,
	capacity INT
);

DROP TABLE IF EXISTS events;
CREATE TABLE events (
	event_id SERIAL PRIMARY KEY,
	title VARCHAR(255) NOT NULL,
	description VARCHAR(255),
	starts_at TIMESTAMP NOT NULL,
	ends_at TIMESTAMP NOT NULL,
	organiser_id INT REFERENCES users(user_id),
	venue_id INT REFERENCES venues(venue_id),
	created_at TIMESTAMP DEFAULT NOW()
);

DROP TABLE IF EXISTS rsvps;
CREATE TABLE rsvps (
	rsvp_id SERIAL PRIMARY KEY,
	attendee_id INT REFERENCES users(user_id),
	event_id INT REFERENCES events(event_id),
	created_at TIMESTAMP DEFAULT NOW()
);
