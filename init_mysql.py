import sys
import time

import pymysql


def ensure_mysql_ready(host: str, port: int, user: str, password: str, retries: int = 10, delay_seconds: int = 2) -> None:
	for attempt in range(retries):
		try:
			conn = pymysql.connect(host=host, port=port, user=user, password=password)
			conn.close()
			return
		except Exception:
			if attempt == retries - 1:
				raise
			time.sleep(delay_seconds)


def main() -> int:
	host = "127.0.0.1"
	port = 3306
	root_user = "root"
	root_password = "foolishfoolz"

	# Wait for MySQL to be ready
	ensure_mysql_ready(host, port, root_user, root_password)

	conn = pymysql.connect(host=host, port=port, user=root_user, password=root_password, autocommit=True)
	try:
		with conn.cursor() as cur:
			cur.execute("CREATE DATABASE IF NOT EXISTS hrm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
			cur.execute("CREATE USER IF NOT EXISTS 'hrm'@'localhost' IDENTIFIED BY 'hrm12345';")
			cur.execute("GRANT ALL PRIVILEGES ON hrm.* TO 'hrm'@'localhost';")
			cur.execute("FLUSH PRIVILEGES;")
	finally:
		conn.close()

	print("initialized")
	return 0


if __name__ == "__main__":
	sys.exit(main())


