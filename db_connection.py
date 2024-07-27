import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os

json_data = None
db_connection = False
file_path = ''
switch_types = ''

# Create new json file for the db if don't have existing
def create_new_json_file():
  global json_data, db_connection, file_path
  try:
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
      initial_data = {
        "UatDB": {},
        "UpdateDB": {}
      }
      with open(file_path, 'w') as file:
        json.dump(initial_data, file, indent=4)
      json_data = initial_data
      db_connection = True
      messagebox.showinfo('File Created', f'New JSON file created at: {file_path}')
    else:
      messagebox.showwarning('No File Created', 'No file was created.')
      db_connection = False
  except Exception as e:
    messagebox.showerror('Error', f'An error occurred while creating the file: {e}')
    db_connection = False

# Use existing json file as db
def load_existing_json_file():
  global json_data, db_connection, file_path
  try:
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
      with open(file_path, 'r') as file:
        json_data = json.load(file)
      db_connection = True
      messagebox.showinfo('File Loaded', f'JSON file loaded from: {file_path}')
    else:
      messagebox.showwarning('No File Selected', 'No file was selected.')
      db_connection = False
  except Exception as e:
    messagebox.showerror('Error', f'An error occurred while loading the file: {e}')
    db_connection = False

# Show popup function for json db file selection
def json_selection():
  popup = tk.Toplevel()
  popup.title('Select Option')
  
  screen_width = popup.winfo_screenwidth()
  screen_height = popup.winfo_screenheight()
  
  width = 400
  height = 200
  
  x = (screen_width / 2) - (width / 2)
  y = (screen_height / 2) - (height / 2)
  
  popup.geometry(f'{width}x{height}+{int(x)}+{int(y)}')

  popup.grid_columnconfigure(0, weight=1)
  popup.grid_columnconfigure(1, weight=1)
  popup.grid_rowconfigure(0, weight=1)
  popup.grid_rowconfigure(1, weight=1)
  popup.grid_rowconfigure(2, weight=1)

  label = tk.Label(popup, text="Choose an option:")
  label.grid(column=0, row=0, columnspan=2, pady=10)

  load_button = tk.Button(popup, text="Load Existing JSON File", command=lambda: [popup.destroy(), load_existing_json_file()])
  load_button.grid(column=0, row=1, padx=10)
  
  load_info = tk.Label(popup, text="Load existing DB File")
  load_info.grid(column=0, row=2, padx=10)

  create_button = tk.Button(popup, text="Create New JSON File", command=lambda: [popup.destroy(), create_new_json_file()])
  create_button.grid(column=1, row=1, padx=10)
  
  create_info = tk.Label(popup, text="Create new DB File")
  create_info.grid(column=1, row=2, padx=10)

  return popup
