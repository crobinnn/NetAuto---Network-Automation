import tkinter as tk
import db_connection as db
import os
import json
import base64
import capture_config as cap
import push_config as push
import generate_config as gen
import single_update as single
import db_view as dbview
import bulk_update as bulk
import uat_page as uat
from tkinter import ttk

header = []
push_header = []
cap_header = []

single_visible = ''
bulk_visible = ''
push_visible = ''
generate_visible = ''
capture_visible = ''

icon = \
""" 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
"""
icondata = base64.b64decode(icon)

tempFile= "icon.ico"
iconfile= open(tempFile,"wb")

iconfile.write(icondata)
iconfile.close()

# Create main config mode UI function
def create_config_gui():
  global push_visible, generate_visible, capture_visible
  global conf_frame
  global cap_header
  push_header = ["No.", "Device IP", "Session","Reload in", "Existing Interface", "Backup Existing", "Copy New Config", "Push Config", "Verify Interface Status","Capture Config"]
  cap_header = ["No.", "Device IP", "Session", "Capture Config"]
  
  # Creating intially & forget config submodes UI
  push.push_config_gui(push_header,push_frame)
  push_frame.forget()
  gen.generate_config_gui(gen_frame)
  gen_frame.forget()
  cap.capture_config_gui(cap_header,capture_frame)
  capture_frame.forget()

  # Switching config submodes UI
  def switch_to_push():
    gen_frame.pack_forget()
    capture_frame.pack_forget()
    push_frame.pack()

  def switch_to_generate():
    push_frame.pack_forget()
    capture_frame.pack_forget()
    gen_frame.pack()
    
  def switch_to_capture():
    push_frame.pack_forget()
    gen_frame.pack_forget()
    capture_frame.pack()

  def change_conf_mode(event=None):
    global conf_mode
    conf_mode = select_conf_mode_var.get()
    if conf_mode == 'Push Config':
      switch_to_push()
    elif conf_mode == 'Generate Config':
      switch_to_generate()
    else:
      switch_to_capture()

  select_conf_mode_label = ttk.Label(conf_frame, text='Select config modes:')
  select_conf_mode_label.grid(row=0, column=0, padx=10, pady=3, sticky=tk.W)
  select_conf_mode_var = tk.StringVar()
  select_conf_mode_dropdown = ttk.Combobox(conf_frame, textvariable=select_conf_mode_var, values=['Push Config', 'Generate Config', 'Capture Config'])
  select_conf_mode_dropdown.grid(row=0, column=1, padx=(120,0), pady=3)
  select_conf_mode_dropdown.bind('<<ComboboxSelected>>', change_conf_mode)
  
  conf_frame.pack()
  push_visible = False
  generate_visible = False
  capture_visible = False

# Create main update mode UI function
def create_update_gui():
  global header
  global single_visible,bulk_visible
  global upd_frame
  header = ["No.", "Device IP", "SSH Session", "Old Version","Flash","Copy Image","Verify MD5","Upgrade","Reboot","Reconnect SSH","New Version","Verify Config","Verify Interface","Verify VLAN","Status"]
  
 # Creating intially & forget update submodes UI
  single.create_single_gui(single_frame)
  single_frame.forget()
  bulk.create_bulk_gui(header,bulk_frame)
  bulk_frame.forget()

  # Switching update submodes UI
  def switch_to_single():
    bulk_frame.pack_forget()
    single_frame.pack()

  def switch_to_bulk():
    bulk.fetch_available_switch_types()
    single_frame.pack_forget()
    bulk_frame.pack()

  def change_mode(event=None):
    global mode
    mode = select_mode_var.get()
    if mode == 'Single Update':
      switch_to_single()
    elif mode == 'Bulk Update':
      switch_to_bulk()

  select_mode_label = ttk.Label(upd_frame, text='Select update modes:')
  select_mode_label.grid(row=0, column=0, padx=10, pady=3, sticky=tk.W)
  select_mode_var = tk.StringVar()
  select_mode_dropdown = ttk.Combobox(upd_frame, textvariable=select_mode_var, values=['Single Update', 'Bulk Update'])
  select_mode_dropdown.grid(row=0, column=1, padx=(120,0), pady=3)
  select_mode_dropdown.bind('<<ComboboxSelected>>', change_mode)
  
  upd_frame.pack()
  single_visible = False
  bulk_visible = False
  
# Work in progress for next mode
def create_UAT_gui():
  global uat_frame
  uat.uat_page_gui(uat_frame)
  
  # uat_label = ttk.Label(uat_frame, text='UAT Automation Mode')
  # uat_label.grid(row=0, column=0, padx=10, pady=3, sticky=tk.W)
  
  uat_frame.pack()

# Switching to Update Mode UI function
def switch_to_update():
  global single_visible,bulk_visible,push_visible,generate_visible,capture_visible
  generate_visible = gen_frame.winfo_ismapped()
  push_visible = push_frame.winfo_ismapped()
  capture_visible = capture_frame.winfo_ismapped()
  gen_frame.pack_forget()
  push_frame.pack_forget()
  capture_frame.pack_forget()
  conf_frame.pack_forget()
  uat_frame.pack_forget()

  upd_frame.pack()
  if single_visible:
    single_frame.pack()
  if bulk_visible:
    bulk_frame.pack()
    
# Switching to Config Mode UI function
def switch_to_config():
  global single_visible,bulk_visible,push_visible,generate_visible,capture_visible
  single_visible = single_frame.winfo_ismapped()
  bulk_visible = bulk_frame.winfo_ismapped()
  
  single_frame.pack_forget()
  bulk_frame.pack_forget()
  upd_frame.pack_forget()
  uat_frame.pack_forget()

  conf_frame.pack()
  if push_visible:
    push_frame.pack()
  if generate_visible:
    gen_frame.pack()
  if capture_visible:
    capture_frame.pack()

# Switching to UAT Mode UI function
def switch_to_UAT():
  global single_visible,bulk_visible,push_visible,generate_visible,capture_visible
  single_visible = single_frame.winfo_ismapped()
  bulk_visible = bulk_frame.winfo_ismapped()
  generate_visible = gen_frame.winfo_ismapped()
  push_visible = push_frame.winfo_ismapped()
  capture_visible = capture_frame.winfo_ismapped()
  
  gen_frame.pack_forget()
  push_frame.pack_forget()
  capture_frame.pack_forget()
  single_frame.pack_forget()
  bulk_frame.pack_forget()
  upd_frame.pack_forget()
  conf_frame.pack_forget()
  
  uat_frame.pack()

# App window
root = tk.Tk()
conf_frame = tk.Frame(root)
push_frame = tk.Frame(root)
gen_frame = tk.Frame(root)
capture_frame = tk.Frame(root)
upd_frame = tk.Frame(root)
bulk_frame = tk.Frame(root)
single_frame = tk.Frame(root)
uat_frame = tk.Frame(root)
root.iconbitmap(tempFile)
os.remove(tempFile)
root.title('NetAuto version 1')
root.state('zoomed')

# App Window Fullscreen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{int(screen_width)}x{int(screen_height)}")


selected_gui = tk.StringVar()

# Set initial value of selected_gui
selected_gui.set('Update')

# Dropdown Menu to switch modes
select_mode_label = ttk.Label(root, text='Select Mode:')
select_mode_label.pack(anchor='nw', padx=10, pady=3)
select_mode_dropdown = ttk.Combobox(root, textvariable=selected_gui, values=['Update', 'Config', 'UAT'])
select_mode_dropdown.pack(anchor='nw', padx=10, pady=3)

def change_mode(event=None):
  mode = select_mode_dropdown.get()
  if mode == 'Update':
    switch_to_update()
  elif mode == 'Config':
    switch_to_config()
  elif mode == 'UAT':
    switch_to_UAT()

select_mode_dropdown.bind('<<ComboboxSelected>>', change_mode)

popup = db.json_selection()
root.wait_window(popup)

# Init config UI and forget
create_config_gui()
conf_frame.forget()

# init UAT UI and forget
create_UAT_gui()
uat_frame.forget()

# Init Update UI and use it as initial mode to be shown
create_update_gui()

root.mainloop()