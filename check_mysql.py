import sys
import pymysql

HOST = "127.0.0.1"
PORT = 3306
USER = "root"
PASSWORD = "foolishfoolz"

try:
	conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD)
	conn.close()
	print("OK")
except Exception as e:
	print(f"ERR: {type(e).__name__}: {e}")
	sys.exit(1)


