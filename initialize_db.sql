DROP TABLE IF EXISTS schedule;
DROP TABLE IF EXISTS balance;
DROP TABLE IF EXISTS frequency;
DROP TABLE IF EXISTS type;
DROP TABLE IF EXISTS cd;
DROP TABLE IF EXISTS users;

CREATE TABLE type
(type_id SERIAL PRIMARY KEY NOT NULL
, label TEXT NOT NULL
, factor INTEGER);

INSERT INTO type (label, factor) VALUES ('Pay Check', 1);
INSERT INTO type (label, factor) VALUES ('Deposit', 1);
INSERT INTO type (label, factor) VALUES ('Bill', -1);
INSERT INTO type (label, factor) VALUES ('Payment', -1);
INSERT INTO type (label, factor) VALUES ('Other', 0);

CREATE TABLE frequency
(frequency_id SERIAL PRIMARY KEY NOT NULL
, frequency TEXT
, modifier TEXT
, n INTEGER);

INSERT INTO frequency (frequency, modifier, n) VALUES ('Daily', 'days', 1);
INSERT INTO frequency (frequency, modifier, n) VALUES ('Weekly', 'days', 7);
INSERT INTO frequency (frequency, modifier, n) VALUES ('Monthly', 'months', 1);
INSERT INTO frequency (frequency, modifier, n) VALUES ('Quarterly', 'months', 3);
INSERT INTO frequency (frequency, modifier, n) VALUES ('Yearly', 'years', 1);
INSERT INTO frequency (frequency, modifier, n) VALUES ('One Time', NULL, NULL);

CREATE TABLE cd
(cd TEXT PRIMARY KEY
, cd_group TEXT
, cd_desc TEXT);

INSERT INTO cd (cd, cd_group, cd_desc) VALUES ('CHK', 'pmt-source', 'Checking');
INSERT INTO cd (cd, cd_group, cd_desc) VALUES ('CC', 'pmt-source', 'Credit Card');
INSERT INTO cd (cd, cd_group, cd_desc) VALUES ('M', 'pmt-method', 'Manual');
INSERT INTO cd (cd, cd_group, cd_desc) VALUES ('AP', 'pmt-method', 'Auto Pay');
INSERT INTO cd (cd, cd_group, cd_desc) VALUES ('DD', 'pmt-method', 'Direct Deposit');

CREATE TABLE users
(user_id SERIAL PRIMARY KEY NOT NULL
, username TEXT
, hash TEXT);

CREATE TABLE balance
(user_id INTEGER PRIMARY KEY NOT NULL
, current NUMERIC NOT NULL DEFAULT 0 
, available NUMERIC NOT NULL DEFAULT 0 
, CONSTRAINT fk_balance_user FOREIGN KEY(user_id) REFERENCES users(user_id));

CREATE TABLE schedule
(schedule_id SERIAL PRIMARY KEY NOT NULL
, name TEXT NOT NULL
, type_id INTEGER NOT NULL
, current_dt DATE
, snoozed_dt DATE
, previous_dt DATE
, completed_dt DATE
, frequency_id INTEGER
, repeat INTEGER DEFAULT 1 
, amount NUMERIC
, user_id INTEGER
, pmt_source TEXT
, pmt_method TEXT
, CONSTRAINT fk_schedule_user FOREIGN KEY(user_id) REFERENCES users(user_id)
, CONSTRAINT fk_schedule_type FOREIGN KEY(type_id) REFERENCES type(type_id)
, CONSTRAINT fk_schedule_frequency FOREIGN KEY(frequency_id) REFERENCES frequency(frequency_id));