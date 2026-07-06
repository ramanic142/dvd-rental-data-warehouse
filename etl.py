import psycopg2

src = psycopg2.connect(host='localhost', dbname='dvdrental', user='postgres', password='postgres')
dst = psycopg2.connect(host='localhost', dbname='dvd_warehouse', user='postgres', password='postgres')

src_cur = src.cursor()
dst_cur = dst.cursor()

print('Loading DimCustomer...')
src_cur.execute('''
SELECT c.customer_id, c.first_name, c.last_name, c.email, ci.city, co.country, c.activebool
FROM customer c
JOIN address a ON c.address_id = a.address_id
JOIN city ci ON a.city_id = ci.city_id
JOIN country co ON ci.country_id = co.country_id
''')
rows = src_cur.fetchall()
dst_cur.executemany('INSERT INTO dimcustomer (customer_id, first_name, last_name, email, city, country, active) VALUES (%s,%s,%s,%s,%s,%s,%s)', rows)
print(f'DimCustomer: {len(rows)} rows loaded')

print('Loading DimFilm...')
src_cur.execute('''
SELECT f.film_id, f.title, f.rating::TEXT, c.name, f.rental_duration, f.rental_rate, f.length, f.replacement_cost
FROM film f
JOIN film_category fc ON f.film_id = fc.film_id
JOIN category c ON fc.category_id = c.category_id
''')
rows = src_cur.fetchall()
dst_cur.executemany('INSERT INTO dimfilm (film_id, title, rating, category, rental_duration, rental_rate, length, replacement_cost) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)', rows)
print(f'DimFilm: {len(rows)} rows loaded')

print('Loading DimStore...')
src_cur.execute('''
SELECT s.store_id, ci.city, co.country
FROM store s
JOIN address a ON s.address_id = a.address_id
JOIN city ci ON a.city_id = ci.city_id
JOIN country co ON ci.country_id = co.country_id
''')
rows = src_cur.fetchall()
dst_cur.executemany('INSERT INTO dimstore (store_id, city, country) VALUES (%s,%s,%s)', rows)
print(f'DimStore: {len(rows)} rows loaded')

print('Loading DimStaff...')
src_cur.execute('SELECT staff_id, first_name, last_name FROM staff')
rows = src_cur.fetchall()
dst_cur.executemany('INSERT INTO dimstaff (staff_id, first_name, last_name) VALUES (%s,%s,%s)', rows)
print(f'DimStaff: {len(rows)} rows loaded')

print('Loading FactRental...')
src_cur.execute('''
SELECT
    r.rental_id,
    TO_CHAR(r.rental_date, 'YYYYMMDD')::INT,
    c.customer_id,
    i.film_id,
    i.store_id,
    r.staff_id,
    CASE WHEN r.return_date IS NOT NULL THEN EXTRACT(DAY FROM (r.return_date - r.rental_date))::INT ELSE 0 END,
    COALESCE(p.amount, 0)
FROM rental r
JOIN inventory i ON r.inventory_id = i.inventory_id
JOIN customer c ON r.customer_id = c.customer_id
LEFT JOIN payment p ON p.rental_id = r.rental_id
''')
rows = src_cur.fetchall()

dst_cur.execute('SELECT customer_id, customer_key FROM dimcustomer')
cust_map = {r[0]: r[1] for r in dst_cur.fetchall()}
dst_cur.execute('SELECT film_id, film_key FROM dimfilm')
film_map = {r[0]: r[1] for r in dst_cur.fetchall()}
dst_cur.execute('SELECT store_id, store_key FROM dimstore')
store_map = {r[0]: r[1] for r in dst_cur.fetchall()}
dst_cur.execute('SELECT staff_id, staff_key FROM dimstaff')
staff_map = {r[0]: r[1] for r in dst_cur.fetchall()}

fact_rows = []
for r in rows:
    rental_id, date_key, customer_id, film_id, store_id, staff_id, duration, amount = r
    if customer_id in cust_map and film_id in film_map:
        fact_rows.append((
            rental_id, date_key,
            cust_map[customer_id],
            film_map[film_id],
            store_map.get(store_id),
            staff_map.get(staff_id),
            duration, amount
        ))

dst_cur.executemany('INSERT INTO factrental (rental_id, date_key, customer_key, film_key, store_key, staff_key, rental_duration_days, amount_paid) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)', fact_rows)
print(f'FactRental: {len(fact_rows)} rows loaded')

dst.commit()
src.close()
dst.close()
print('ETL complete!')
