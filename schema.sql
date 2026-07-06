-- ============================================================
-- DVD Rental Data Warehouse — Schema Creation
-- Author: Ramani Chiranjeevulu | Clark University
-- Course: MSDA3040-S26
-- Description: Star schema for dvd_warehouse OLAP database
-- ============================================================

-- Step 1: Create the database
-- CREATE DATABASE dvd_warehouse;

-- Step 2: Create all 6 tables

CREATE TABLE DimDate (
    date_key    INT PRIMARY KEY,
    full_date   DATE,
    day_of_week VARCHAR(10),
    day_num     INT,
    month_num   INT,
    month_name  VARCHAR(10),
    quarter     INT,
    year        INT
);

CREATE TABLE DimCustomer (
    customer_key SERIAL PRIMARY KEY,
    customer_id  INT,
    first_name   VARCHAR(50),
    last_name    VARCHAR(50),
    email        VARCHAR(100),
    city         VARCHAR(50),
    country      VARCHAR(50),
    active       BOOLEAN
);

CREATE TABLE DimFilm (
    film_key         SERIAL PRIMARY KEY,
    film_id          INT,
    title            VARCHAR(255),
    rating           VARCHAR(10),
    category         VARCHAR(50),
    rental_duration  INT,
    rental_rate      NUMERIC(4,2),
    length           INT,
    replacement_cost NUMERIC(5,2)
);

CREATE TABLE DimStore (
    store_key SERIAL PRIMARY KEY,
    store_id  INT,
    city      VARCHAR(50),
    country   VARCHAR(50)
);

CREATE TABLE DimStaff (
    staff_key  SERIAL PRIMARY KEY,
    staff_id   INT,
    first_name VARCHAR(50),
    last_name  VARCHAR(50)
);

CREATE TABLE FactRental (
    rental_key          SERIAL PRIMARY KEY,
    rental_id           INT,
    date_key            INT REFERENCES DimDate(date_key),
    customer_key        INT REFERENCES DimCustomer(customer_key),
    film_key            INT REFERENCES DimFilm(film_key),
    store_key           INT REFERENCES DimStore(store_key),
    staff_key           INT REFERENCES DimStaff(staff_key),
    rental_duration_days INT,
    amount_paid         NUMERIC(5,2)
);

-- Step 3: Populate DimDate (2005-2007)
INSERT INTO DimDate (date_key, full_date, day_of_week, day_num, month_num, month_name, quarter, year)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INT,
    d::DATE,
    TO_CHAR(d, 'Day'),
    EXTRACT(DOW FROM d)::INT,
    EXTRACT(MONTH FROM d)::INT,
    TO_CHAR(d, 'Month'),
    EXTRACT(QUARTER FROM d)::INT,
    EXTRACT(YEAR FROM d)::INT
FROM generate_series('2005-01-01'::DATE, '2007-12-31'::DATE, '1 day'::INTERVAL) AS d;

-- Step 4: Verify all tables
-- \dt
-- SELECT 'dimcustomer' as table_name, COUNT(*) FROM dimcustomer
-- UNION ALL SELECT 'dimfilm', COUNT(*) FROM dimfilm
-- UNION ALL SELECT 'dimstore', COUNT(*) FROM dimstore
-- UNION ALL SELECT 'dimstaff', COUNT(*) FROM dimstaff
-- UNION ALL SELECT 'dimdate', COUNT(*) FROM dimdate
-- UNION ALL SELECT 'factrental', COUNT(*) FROM factrental;
