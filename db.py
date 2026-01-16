import mysql.connector


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "**96430397@Ah",
    "database": "traffic_ai_db"
}





def get_db():
    return mysql.connector.connect(**DB_CONFIG)


