import couchdb
import tkinter as tk
# DB Variables
user = "compnet"
password = "C0mpn3t!"
dbname = 'cisco-device'
db = None
db_connection = False

def connect_to_db():
  global couchserver
  global dbname
  global db
  global db_connection
  try:
    couchserver = couchdb.Server(f"http://{user}:{password}@172.16.2.110:5984/")
    db = couchserver[dbname]
    db_connection = True
  except couchdb.http.Unauthorized:
    tk.messagebox.showinfo('Database Error', 'Not connected to DB! Invalid DB Credentials')
    db_connection = False
  except couchdb.http.ServerError:
    tk.messagebox.showinfo('Database Error', 'Not connected to DB! Server Error')
    db_connection = False
  except couchdb.http.ResourceNotFound:
    tk.messagebox.showinfo('Database Error', 'Not connected to DB! Resource Not Found')
    db_connection = False
  except Exception as e:
    tk.messagebox.showinfo('Database Error', f'Not connected to DB! Error: {e}')
    db_connection = False