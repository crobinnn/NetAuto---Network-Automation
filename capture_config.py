import os
import tkinter as tk
from tkinter import ttk,filedialog,font
from netmiko import ConnectHandler
import threading
import csv
import re
import datetime
import time

def capture_config_gui(cap_header,capture_frame):
  global loaded_csv
  loaded_csv = []
  command_list = []
  
  def load_cmd():
    filename = filedialog.askopenfilename(title='Select capture commmand file (.txt)', filetypes=(("TXT files", "*.txt"), ("All files", "*.*")))
    if filename:
      cmd_file_var.set(f"Cmd File: {os.path.basename(filename)}")
      with open(filename, 'r') as file:
        command_list.clear()
        for line in file:
          command_list.append(line.strip())
        
        print(command_list)
    
  def load_csv():
    global loaded_csv
    csfilename = filedialog.askopenfilename(title="Select CSV File", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
    if csfilename:
      try:
        with open(csfilename, newline='') as file:
          reader = csv.DictReader(file)
          loaded_csv = [row for row in reader]
        csv_file_var.set(f"CSV File: {os.path.basename(csfilename)}")
      except FileNotFoundError:
        return None
  
  def display_cap():
    # Clear treeview table
    for item in cap_tree.get_children():
      cap_tree.delete(item)

    if loaded_csv:
      for i, item in enumerate(cap_header):
        cap_tree.heading("#" + str(i+1), text=item)
        cap_tree.column("#" + str(i+1), stretch=True, width=100)

      # Start SSH
      for index,cap in enumerate(loaded_csv):
        cap['no'] = index + 1
        row_data = [cap['no'], cap['ip'], '','']
        item_id = cap_tree.insert("", "end", values=row_data)
        threading.Thread(target=capture_config, args=(cap, item_id)).start()
  
  def capture_config(cap,item_id):
    number = cap['no']
    vendor = cap['vendor']
    ip = cap['ip']
    user = cap['user']
    password = cap['password']
    protocol = cap['protocol']
    capture_log_path = capturelog_entry.get()
    
    if vendor == 'cisco' and protocol == 'telnet':
      device = {
        'device_type': 'cisco_ios_telnet',
        'host': ip,
        'username': user,
        'password': password,
        'port': 23,
      }
    elif vendor == 'cisco' and protocol == 'ssh':
      device = {
        'device_type': 'cisco_ios',
        'host': ip,
        'username': user,
        'password': password,
        'port': 22,
      }
    
    def check_connection(device):
      try:
        connect = ConnectHandler(**device)
        return connect, None
      except Exception as e:
        return None, str(e)

    net_connect, error = check_connection(device)
    if error:
      tk.messagebox.showinfo('Error on process no. ' + str(number), error)
      cap_tree.set(item_id, "#3", "Fail")
      cap_tree.update_idletasks()
      return
    else:
      net_connect.find_prompt()
      cap_tree.set(item_id, '#3', "Connected")
      cap_tree.update_idletasks()
      net_connect.send_command('term length 0')
      
      # regular case for staging
      hostname = net_connect.send_command('sh run | include hostname').split()[1]
      date_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
      logfilename = f'{hostname}_{date_time}.txt'
      cap_tree.set(item_id, '#4', "Capturing config...")
      cap_tree.update_idletasks()
      net_connect.send_command('term length 0')
      hostname = net_connect.send_command('sh run | include hostname').split()[1]
      
      # Case for device checking, capture need Serial Number as file name
      # hostname = net_connect.send_command('sh run | include hostname').split()[1]
      # sn = net_connect.send_command('sh inv | include SN')
      # def extract_first_serial_number(output):
      #   """Extract the first serial number from the command output."""
      #   serial_number_pattern = re.compile(r'SN:\s*(\S+)')
      #   match = serial_number_pattern.search(output)
      #   if match:
      #       return match.group(1)
      #   else:
      #       return None
          
      # serial = extract_first_serial_number(sn)
      # logfilename = f'{serial}.txt'
      # cap_tree.set(item_id, '#4', "Capturing config...")
      # cap_tree.update_idletasks()
      # net_connect.send_command('term length 0')
      # hostname = net_connect.send_command('sh run | include hostname').split()[1]

      
      output = ''
      
      for cmd in command_list:
        print(f"Sending command: {cmd}")  # Debugging print
        cmd_output = net_connect.send_command(cmd, read_timeout=600)
        print(f"Command: {cmd}\nOutput: {cmd_output}")  # Debugging print
        output += f'{hostname}#{cmd}\n{cmd_output}\n\n'
        time.sleep(0.5)
      
      # case if sh tech doesnt work
      # for cmd in command_list:
      #   print(f"Sending command: {cmd}")  # Debugging print
      #   if cmd == 'sh tech' or cmd == 'show tech' or cmd == 'show tech-support':
      #     cmd_output = net_connect.send_command(cmd,read_timeout=600,expect_string='========== END ============')
      #   else:
      #     cmd_output = net_connect.send_command(cmd,read_timeout=600)
      #   print(f"Command: {cmd}\nOutput: {cmd_output}")  # Debugging print
      #   output += f'{hostname}#{cmd}\n{cmd_output}\n\n'
      #   time.sleep(0.5)
      
      with open(os.path.join(capture_log_path,logfilename),'w') as log_file:
        log_file.write(output)
      
      cap_tree.set(item_id, '#4', "Done!")
      cap_tree.update_idletasks()
      net_connect.disconnect()
        
  style = ttk.Style()
  style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])  # Remove border from the treeview
  style.layout("Custom.Treeview.Heading", style.layout("Treeview.Heading"))

  # Custom separator line style
  style.configure("Custom.Treeview", background="#D3D3D3")
  style.map("Custom.Treeview", foreground=[('selected', 'black')])
  
  bold_font = font.Font(family="TkDefaultFont", weight="bold",size=10)
  
  info_label = ttk.Label(capture_frame, text='CSV Format = vendor, ip, user, password, protocol (telnet/ssh)', font=bold_font)
  info_label.grid(row=1, column=0,columnspan=2)

  capturelog_label = ttk.Label(capture_frame, text='Path to Store Capture Logs:')
  capturelog_label.grid(row=2, column=0,columnspan=2)
  capturelog_entry = ttk.Entry(capture_frame, width=23)
  capturelog_entry.grid(row=3, column=0,columnspan=2,pady=10)
  
  cmd_file_var = tk.StringVar(value='Cmd File: No file selected')
  csv_file_var = tk.StringVar(value='CSV File: No file selected')
  
  # Button to open file explorer 
  open_txt_button = ttk.Button(capture_frame, text="Import .txt", command=load_cmd)
  open_txt_button.grid(row=5, column=0,padx=(0,300),columnspan=2)
  cmd_file_label = ttk.Label(capture_frame, textvariable=cmd_file_var)
  cmd_file_label.grid(row=6,column=0,pady=5,padx=(0,300),columnspan=2)
  
  open_csv_button = ttk.Button(capture_frame, text="Import CSV", command=load_csv)
  open_csv_button.grid(row=5, column=0,padx=(300,0),columnspan=2)
  csv_file_label = ttk.Label(capture_frame, textvariable=csv_file_var)
  csv_file_label.grid(row=6, column=0,pady=5,padx=(300,0),columnspan=2)
  
  start_button = ttk.Button(capture_frame, text="Start", command=display_cap)
  start_button.grid(row=7,column=0,pady=5,columnspan=2)

  cap_tree = ttk.Treeview(capture_frame, columns=[f"#{i}" for i in range(1, len(cap_header) + 1)], show="headings", height=25, style="Custom.Treeview")
  cap_tree.grid(row=8, column=0, sticky="nsew",columnspan=2)
  for i, col in enumerate(cap_header):
    cap_tree.heading(f"#{i+1}", text=col)
    cap_tree.column(f"#{i+1}", width=150, stretch=tk.YES)

  # Add scrollbar to the Treeview
  scrollbar = ttk.Scrollbar(capture_frame, orient="vertical", command=cap_tree.yview)
  cap_tree.configure(yscroll=scrollbar.set)
  scrollbar.grid(row=8, column=2, sticky="ns")

  capture_frame.grid_rowconfigure(3, weight=1)
  capture_frame.grid_columnconfigure(1, weight=1)
  capture_frame.pack()


    