import sqlite3

conn = sqlite3.connect('database.db')

create_table_users = """
CREATE TABLE users (
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
username TEXT NOT NULL UNIQUE, 
password TEXT NOT NULL, 
salt TEXT NOT NULL, 
mfa INTEGER NOT NULL
)
"""

create_table_queries = """
CREATE TABLE queries (
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
submitter TEXT NOT NULL,
query TEXT NOT NULL,
result TEXT NOT NULL,
FOREIGN KEY(submitter) REFERENCES users(username) ON UPDATE CASCADE
)
"""

create_table_logins = """
CREATE TABLE logins (
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
username TEXT NOT NULL,
login_time TEXT DEFAULT (DATETIME('now', 'localtime')) NOT NULL,
logout_time TEXT DEFAULT 'N/A' NOT NULL,
FOREIGN KEY(username) REFERENCES users(username) ON UPDATE CASCADE
)
"""

conn.execute(create_table_users)
conn.execute(create_table_queries)
conn.execute(create_table_logins)

conn.close()