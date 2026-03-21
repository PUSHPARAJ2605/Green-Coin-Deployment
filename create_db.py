import pymysql
from decouple import config

try:
    connection = pymysql.connect(
        host=config('DB_HOST', default='localhost'),
        user=config('DB_USER', default='root'),
        password=config('DB_PASSWORD', default='root')
    )
    with connection.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS civicwaste_db;")
        print("Database 'civicwaste_db' created successfully.")
    
    with connection.cursor() as cursor:
        cursor.execute("SHOW DATABASES;")
        dbs = [row[0] for row in cursor.fetchall()]
        print("Current databases:", dbs)
        
    connection.close()
except Exception as e:
    print(f"Error connecting to MySQL: {e}")
