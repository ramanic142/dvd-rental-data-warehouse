import psycopg2

PG_HOST = '172.19.0.3'
PG_USER = 'postgres'
PG_PASS = 'postgres'

src = psycopg2.connect(host=PG_HOST, dbname='dvdrental', user=PG_USER, password=PG_PASS)
dst = psycopg2.connect(host=PG_HOST, dbname='dvd_warehouse', user=PG_USER, password=PG_PASS)
src_cur = src.cursor()
dst_cur = dst.cursor()

print('Loading FactRental...')
src_cur.execute("""SELECT r.rental_id, TO_CHAR(r.rental_date, 'YYYYMMDD')::INT, c.customer_id, i.film_id, i.store_id, r.staff_id, CASE WHEN r.return_date IS NOT NULL THEN EXTRACT(DAY FROM (r.return_date - r.rental_date))::INT ELSE 0 END, COALESCE(p.amount, 0) FROM rental r JOIN inventory i ON r.inventory_id = i.inventory_id JOIN customer c ON r.customer_id = c.customer_id LEFT JOIN payment p ON p.rental_id = r.rental_id""")
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
        fact_rows.append((rental_id, date_key, cust_map[customer_id], film_map[film_id], store_map.get(store_id), staff_map.get(staff_id), duration, amount))

dst_cur.executemany('INSERT INTO factrental (rental_id, date_key, customer_key, film_key, store_key, staff_key, rental_duration_days, amount_paid) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)', fact_rows)
print(f'FactRental: {len(fact_rows)} rows loaded')

dst.commit()
src.close()
dst.close()
print('ETL COMPLETE!')
