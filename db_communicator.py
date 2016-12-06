import psycopg2, credentials


def query(queryString, values, result):
	conn = psycopg2.connect("dbname='{0}' user='{1}' host='localhost' password='{2}'".format(credentials.db_name, credentials.db_username, credentials.db_password))
	cur = conn.cursor()
	cur.execute(queryString, values)
	if result:
		result = cur.fetchall()
	conn.commit()
	cur.close()
	conn.close()

	return result