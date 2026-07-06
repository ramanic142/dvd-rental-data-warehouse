import psycopg2

PG_HOST = "172.19.0.3"
PG_USER = "postgres"
PG_PASS = "postgres"

src = psycopg2.connect(host=PG_HOST, dbname="dvdrental", user=PG_USER, password=PG_PASS)
dst = psycopg2.connect(host=PG_HOST, dbname="dvd_warehouse", user=PG_USER, password=PG_PASS)
src_cur = src.cursor()
dst_cur = dst.cursor()

print("Loading DimCustomer...")
src_cur.execute("SELECT c.customer_id, c.first_name, c.last_name, c.email, ci.city, co.country, c.activebool FROM customer c JOIN address a ON c.address_id = a.address_id JOIN city ci ON a.city_id = ci.city_id JOIN country co ON ci.country_id = co.country_id")
rows = src_cur.fetchall()
dst_cur.executemany("INSERT INTO dimcustomer (customer_id, first_name, last_name, email, city, country, active) VALUES (%s,%s,%s,%s,%s,%s,%s)", rows)
print("DimCustomer: " + str(len(rows)) + " rows loaded")

print("Loading DimFilm...")
src_cur.execute("SELECT f.film_id, f.title, f.rating::TEXT, c.name, f.rental_duration, f.rental_rate, f.length, f.replacement_cost FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON fc.category_id = c.category_id")
rows = src_cur.fetchall()
dst_cur.executemany("INSERT INTO dimfilm (film_id, title, rating, category, rental_duration, rental_rate, length, replacement_cost) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", rows)
print("DimFilm: " + str(len(rows)) + " rows loaded")

print("Loading DimStore...")
src_cur.execute("SELECT s.store_id, ci.city, co.country FROM store s JOIN address a ON s.address_id = a.address_id JOIN city ci ON a.city_id = ci.city_id JOIN country co ON ci.country_id = co.country_id")
rows = src_cur.fetchall()
dst_cur.executemany("INSERT INTO dimstore (store_id, city, country) VALUES (%s,%s,%s)", rows)
print("DimStore: " + str(len(rows)) + " rows loaded")

print("Loading DimStaff...")
src_cur.execute("SELECT staff_id, first_name, last_name FROM staff")
rows = src_cur.fetchall()
dst_cur.executemany("INSERT INTO dimstaff (staff_id, first_name, last_name) VALUES (%s,%s,%s)", rows)
print("DimStaff: " + str(len(rows)) + " rows loaded")

dst.commit()
print("Dimensions committed!")

print("Loading FactRental...")
src_cur.execute("SELECT r.rental_id, TO_CHAR(r.rental_date, 'YYYYMMDD')::INT, c.customer_id, i.film_id, i.store_id, r.staff_id, CASE WHEN r.return_date IS NOT NULL THEN EXTRACT(DAY FROM (r.return_date - r.rental_date))::INT ELSE 0 END, COALESCE(p.amount, 0) FROM rental r JOIN inventory i ON r.inventory_id = i.inventory_id JOIN customer c ON r.customer_id = c.customer_id LEFT JOIN payment p ON p.rental_id = r.rental_id")
rows = src_cur.fetchall()
print("Fetched " + str(len(rows)) + " rentals from source")

dst_cur.execute("SELECT customer_id, customer_key FROM dimcustomer")
cust_map = {r[0]: r[1] for r in dst_cur.fetchall()}
print("Customer map: " + str(len(cust_map)) + " entries")

dst_cur.execute("SELECT film_id, film_key FROM dimfilm")
film_map = {r[0]: r[1] for r in dst_cur.fetchall()}
print("Film map: " + str(len(film_map)) + " entries")

dst_cur.execute("SELECT store_id, store_key FROM dimstore")
store_map = {r[0]: r[1] for r in dst_cur.fetchall()}

dst_cur.execute("SELECT staff_id, staff_key FROM dimstaff")
staff_map = {r[0]: r[1] for r in dst_cur.fetchall()}

fact_rows = []
for r in rows:
    rental_id, date_key, customer_id, film_id, store_id, staff_id, duration, amount = r
    if customer_id in cust_map and film_id in film_map:
        fact_rows.append((rental_id, date_key, cust_map[customer_id], film_map[film_id], store_map.get(store_id), staff_map.get(staff_id), duration, amount))

print("Fact rows to insert: " + str(len(fact_rows)))
dst_cur.executemany("INSERT INTO factrental (rental_id, date_key, customer_key, film_key, store_key, staff_key, rental_duration_days, amount_paid) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", fact_rows)

dst.commit()
src.close()
dst.close()
print("ETL COMPLETE!")
