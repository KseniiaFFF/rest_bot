import sqlite3

def db(str, params = ()):

    connection = sqlite3.connect('restaurant.db', check_same_thread=False)
    cursor = connection.cursor()
    cursor.execute(str,params)
    connection.commit()
    return cursor

def db_fetchall(sql, params=()):
    with sqlite3.connect('restaurant.db', check_same_thread=False) as conn:
        return conn.execute(sql, params).fetchall()
  