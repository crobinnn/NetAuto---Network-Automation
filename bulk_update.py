import tkinter as tk
import db_connection as db
import csv
import re
import os
import threading
import time
import difflib
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException
from tkinter import ttk,messagebox,filedialog,font

def create_bulk_gui(header,bulk_frame):
  global fetch_available_switch_types
  json_data = db.json_data
  file_path = db.file_path
  def fetch_available_switch_types(event=None):
    if json_data is None:
      messagebox.showinfo('Error Occured', 'Cannot access database. JSON not loaded.')
      return
    try:
      switch_types = list(json_data.get("UpdateDB", {}).keys())
      available_ver_dropdown['values'] = switch_types
    except Exception as e:
      version_text.insert(tk.END,f"Failed Fetching SW types. {e}")
      
  
  def fetch_versions(event=None):
    switch_type = available_ver_var.get()
    if json_data is None:
      messagebox.showinfo('Error Occured', 'Cannot access database. JSON not loaded.')
      return
    try:
      switch_data = json_data.get("UpdateDB", {}).get(switch_type, {})
      versions = [version["name"] for version in switch_data.get("versions", [])]
      version_text.delete(1.0, tk.END)  # Clear previous content
      version_text.insert(tk.END, 'Available Versions:\n')
      if versions:
        # Format versions with bullet points
        for version in versions:
          version_text.insert(tk.END, f'> {version}\n')
      else:
        version_text.insert(tk.END, 'No versions available.')
    except Exception as e:
      version_text.insert(tk.END,"Failed fetching version")

  def load_csv():
    filename = filedialog.askopenfilename(title="Select CSV File", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
    if filename:
      try:
        with open(filename, newline='') as file:
          reader = csv.DictReader(file)
          data = [row for row in reader]
        return data
      except FileNotFoundError:
        return None

  def display_bulks():
    # Clear existing data in the Treeview
    for item in bulk_tree.get_children():
      bulk_tree.delete(item)

    data = load_csv()
    if data:
      required_fields = ['user', 'password', 'protocol', 'type', 'version', 'ip', 'serverip', 'secret']

      # Check for missing fields
      missing_fields = [field for field in required_fields if field not in data[0]]

      if missing_fields:
        messagebox.showwarning("Warning", f"CSV is missing the following required fields: {', '.join(missing_fields)}")
        return
      # Create header row
      for i, item in enumerate(header):
        bulk_tree.heading("#" + str(i+1), text=item)
        bulk_tree.column("#" + str(i+1), stretch=True, width=100)

      # Start SSH process for each bulk
      for index,bulk in enumerate(data):
        bulk['no'] = index + 1
        row_data = [bulk['no'], bulk['ip'], "", "", "", "", "", "", "", "", "", "", "", "", ""]
        item_id = bulk_tree.insert("", "end", values=row_data)
        # Start SSH process for each bulk
        threading.Thread(target=ssh_process, args=(bulk, item_id)).start()
        
  def ssh_process(bulk, item_id):
    number = bulk['no']
    switch_type = bulk['type']
    os_version = bulk['version']
    ip = bulk['ip']
    user = bulk['user']
    password = bulk['password']
    protocol = bulk['protocol']
    tftp_server = bulk['serverip']
    secret = bulk['secret']
    save_path = path_entry.get()
    cleanup = clean_var.get()
    doc = json_data.get("UpdateDB", {}).get(switch_type, {})

    if doc:
      found_version = False
      for version in doc.get("versions", []):
        if version['name'] == os_version:
          firmware = version['firmware']
          hash_value = version['hash']
          size = int(version['size'])
          path = version['path']
          found_version = True
          break

      if not found_version:
        messagebox.showinfo("Information", f"OS version '{os_version}' not found in the database for switch type '{switch_type}'.")
        return
    else:
        messagebox.showinfo("Information", f"Switch type '{switch_type}' not found in the database.")
        return

    # SSH Parameter
    if switch_type == 'C2960':
      cisco_device = {
        'device_type': 'cisco_ios',
        'host': ip,
        'username': user,
        'password': password,
        'port': 22,
        'secret': secret
      }
    else:
      cisco_device = {
        'device_type': 'cisco_xe',
        'host': ip,
        'username': user,
        'password': password,
        'port': 22,
        'secret': secret
      }
    
    def check_connection(cisco_device):
      try:
        connect = ConnectHandler(**cisco_device)
        return connect, None
      except Exception as e:
        return None, str(e)

    net_connect, error = check_connection(cisco_device)
    if error:
      tk.messagebox.showinfo('Error Occured', error)
      bulk_tree.set(item_id, "#3", "Fail")
      bulk_tree.update_idletasks()
      return
    else:
      isenable = net_connect.check_enable_mode()
      if isenable == False:
        net_connect.enable()
        device_prompt = net_connect.find_prompt()
        bulk_tree.set(item_id, "#3", "Connected")
        bulk_tree.update_idletasks()
      else:
        device_prompt = net_connect.find_prompt()
        bulk_tree.set(item_id, "#3", "Connected")
        bulk_tree.update_idletasks()

      if switch_type == 'C2960':
        shcurrentver = net_connect.send_command('show ver', read_timeout=300)
        firstline = shcurrentver.strip().split('\n')[0]
        version_index = firstline.find("Version")

        # Get version 
        if version_index != -1:
          comma_index = firstline.find(",", version_index)
          if comma_index != -1:
            currentver = firstline[version_index + len("Version"):comma_index]
          else:
            currentver = 'Not Found'
        else:
          currentver = 'Not Found'

        bulk_tree.set(item_id, "#4", currentver)
        bulk_tree.update_idletasks()
        
        currentconfig = net_connect.send_command('show run', read_timeout=300)

        currentint = net_connect.send_command('show ip int br', read_timeout=300)

        currentvlan = net_connect.send_command('show vlan', read_timeout=300)

        output = net_connect.send_command('dir flash:')
        bytes_free_pattern = r'\((\d+) bytes free\)'
        matches = re.search(bytes_free_pattern, output)

        if matches:
          free_bytes = int(matches.group(1))
          if free_bytes > size:
            bulk_tree.set(item_id, "#5", "Available")
            bulk_tree.update_idletasks()

            while True:
              device_prompt = net_connect.find_prompt()
              # Copy firmware
              if protocol == 'tftp':
                output = net_connect.send_command_timing('copy ' + protocol + '://' + tftp_server + '/' + path + ' flash:', read_timeout=300)
              else:
                output = net_connect.send_command_timing('copy ' + protocol + '://' + 'compnet:C0mpn3t!@' + tftp_server + '/' + path + ' flash:', read_timeout=300)
                  
              # confirmation prompt enter empty string biar kayak enter
              output = net_connect.send_command('\n', expect_string='Accessing ' + protocol + '://', read_timeout=100)
            
              while True:
                output_part = net_connect.read_channel()
                
                if output_part:
                  bulk_tree.set(item_id, "#6", "Copying..")
                  bulk_tree.update_idletasks()
                
                if device_prompt in output_part:
                  break

                time.sleep(3)

              output = net_connect.send_command('dir flash:*.bin', read_timeout=300)

              # confirm apakah file udh ad di flash or not, kalau ad kita ganti system boot ke firmware yg ud dicopy
              if firmware in output:
                bulk_tree.set(item_id, "#6", "Success")
                bulk_tree.update_idletasks()
                #Verify MD5
                output = net_connect.send_command('verify /md5 flash:' + firmware + ' ' + hash_value ,expect_string='...')

                verified = False

                while True:
                  output_part = net_connect.read_channel()
              
                  if output_part:
                    bulk_tree.set(item_id, "#7", "Verifying..")
                    bulk_tree.update_idletasks()
                  
                  if 'Verified' in output_part:
                    verified = True
                    break

                  if device_prompt in output_part:
                    break

                  time.sleep(3)

                if verified == True:
                  # Upgrade firmware
                  bulk_tree.set(item_id, "#7", "Success")
                  bulk_tree.update_idletasks()

                  bulk_tree.set(item_id, "#8", "Upgrading..")
                  bulk_tree.update_idletasks()
                  output = net_connect.send_config_set('boot system flash:' + firmware)

                  output = net_connect.send_command('reload', expect_string='[confirm]', delay_factor=4, max_loops=1000, read_timeout=120)

                  # Confirm reload
                  output = net_connect.send_command('yes')
                  bulk_tree.set(item_id, "#8", "Done")
                  net_connect.disconnect()
                  bulk_tree.set(item_id, "#9", "Rebooting..")
                  bulk_tree.set(item_id, "#10", "Reconnecting..")
                  bulk_tree.update_idletasks()

                  reconnected = False
                  while not reconnected:
                    try:
                      with ConnectHandler(**cisco_device) as net_connect:
                          # REconnect SSH
                          bulk_tree.set(item_id, "#9", "UP")
                          bulk_tree.set(item_id, "#10", "Reconnected")
                          bulk_tree.update_idletasks()
                          reconnected = True

                          # Update ver
                          shupdatever = net_connect.send_command('show ver', read_timeout=300)
                          firstline = shupdatever.strip().split('\n')[0]
                          version_index = firstline.find("Version")

                          # Get version after upd
                          if version_index != -1:
                            comma_index = firstline.find(",", version_index)
                            if comma_index != -1:
                              updatever = firstline[version_index + len("Version"):comma_index]
                            else:
                              updatever = 'Not Found'
                          else:
                            updatever = 'Not Found'
                              
                          bulk_tree.set(item_id, "#11", updatever)
                          bulk_tree.update_idletasks()

                          if updatever != currentver:
                            #config verify
                            bulk_tree.set(item_id, "#12", "Verifying..")
                            bulk_tree.update_idletasks()

                            updateconfig = net_connect.send_command('show run', read_timeout=300)
                            
                            updateconf_lines = updateconfig.strip().split('\n')
                            currentconf_lines = currentconfig.strip().split('\n')

                            confdiff = difflib.unified_diff(currentconf_lines, updateconf_lines)
                            # Check if there are differences
                            if any(confdiff):
                              added_lines =[]
                              removed_lines = []
                              # Classify lines as added (+) or removed (-)
                              for line in confdiff:
                                if line.startswith('+'):
                                  added_lines.append(line[1:])  
                                elif line.startswith('-'):
                                  removed_lines.append(line[1:])  

                              bulk_tree.set(item_id, "#12", "Not Match")
                              bulk_tree.update_idletasks()

                              conf_filename = f"{switch_type}_{ip}_conf.txt"
                              with open(os.path.join(save_path, conf_filename), 'w') as f:
                                f.write("Added lines:\n")
                                for line in added_lines:
                                  f.write(f"+ {line}\n")
                                
                                f.write("\nRemoved lines:\n")
                                for line in removed_lines:
                                  f.write(f"- {line}\n")
                                
                            else:
                              # If no differences, display confirmation message
                              bulk_tree.set(item_id, "#12", "Match")
                              bulk_tree.update_idletasks()
                
                            bulk_tree.set(item_id, "#13", "Verifying..")
                            bulk_tree.update_idletasks()

                            updateint = net_connect.send_command('show ip int br', read_timeout=300)
                            updateint_lines = updateint.strip().split('\n')
                            currentint_lines = currentint.strip().split('\n')
                            
                            intdiff = difflib.unified_diff(currentint_lines, updateint_lines)
                            # Check if there are differences
                            if any(intdiff):
                              added_lines =[]
                              removed_lines = []
                              # Classify lines as added (+) or removed (-)
                              for line in intdiff:
                                if line.startswith('+'):
                                  added_lines.append(line[1:])  
                                elif line.startswith('-'):
                                  removed_lines.append(line[1:])  

                              bulk_tree.set(item_id, "#13", "Not Match")
                              bulk_tree.update_idletasks()

                              int_filename = f"{switch_type}_{ip}_int.txt"
                              with open(os.path.join(save_path, int_filename), 'w') as f:
                                f.write("Added lines:\n")
                                for line in added_lines:
                                  f.write(f"+ {line}\n")
                                
                                f.write("\nRemoved lines:\n")
                                for line in removed_lines:
                                  f.write(f"- {line}\n")      
                            else:
                              # If no differences, display confirmation message
                              bulk_tree.set(item_id, "#13", "Match")
                              bulk_tree.update_idletasks()
                                
                            bulk_tree.set(item_id, "#14", "Verifying..")
                            bulk_tree.update_idletasks()

                            updatevlan = net_connect.send_command('show vlan', read_timeout=300)
                            net_connect.disconnect()
                            updatevlan_lines = updatevlan.strip().split('\n')
                            currentvlan_lines = currentvlan.strip().split('\n')

                            vlandiff = difflib.unified_diff(updatevlan_lines, currentvlan_lines)

                            # Check if there are differences
                            if any(vlandiff):
                              added_lines =[]
                              removed_lines = []
                              # Classify lines as added (+) or removed (-)
                              for line in vlandiff:
                                if line.startswith('+'):
                                  added_lines.append(line[1:]) 
                                elif line.startswith('-'):
                                  removed_lines.append(line[1:])  

                              bulk_tree.set(item_id, "#14", "Not Match")
                              bulk_tree.update_idletasks()

                              vlan_filename = f"{switch_type}_{ip}_vlan.txt"
                              with open(os.path.join(save_path, vlan_filename), 'w') as f:
                                f.write("Added lines:\n")
                                for line in added_lines:
                                  f.write(f"+ {line}\n")
                                
                                f.write("\nRemoved lines:\n")
                                for line in removed_lines:
                                  f.write(f"- {line}\n")
                            else:
                              # If no differences, display confirmation message
                              bulk_tree.set(item_id, "#14", "Match")
                              bulk_tree.update_idletasks()
                                
                            bulk_tree.set(item_id, "#15", "Done!")
                            bulk_tree.update_idletasks()
                            time.sleep(3)
  
                          else:
                            bulk_tree.set(item_id, "#11", "Not Updated")
                            bulk_tree.update_idletasks()
                            net_connect.disconnect()
                            
                    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
                      bulk_tree.set(item_id, "#10", "Reconnecting..")
                      bulk_tree.update_idletasks()
                      time.sleep(3)
                      
                    except Exception as e:
                      bulk_tree.set(item_id, "#10", "Reconnecting..")
                      bulk_tree.update_idletasks()
                      time.sleep(3)
                else:
                  bulk_tree.set(item_id, "#7", "Fail")
                  bulk_tree.update_idletasks()
                  net_connect.disconnect()
              
              else:
                choice = messagebox.askquestion('Process No. ' + str(number) + ' IP: ' + ip, 'Failed to copy file. Do you want to try again?')
                bulk_tree.set(item_id, "#6", "Fail")
                bulk_tree.update_idletasks()
                if choice.lower() != 'yes':
                  return
                else:
                  # Continue to the beginning of the outer while loop for retry
                  continue

          elif free_bytes < size:
            bulk_tree.set(item_id, "#5", "Not Available")
            bulk_tree.update_idletasks()
            net_connect.disconnect()
        else:
          bulk_tree.set(item_id, "#5", "ERR")
          bulk_tree.update_idletasks()
          net_connect.disconnect()

      else:
        ## Before update Version
        shcurrentver = net_connect.send_command('show ver', read_timeout=300)
        firstline = shcurrentver.strip().split('\n')[1]
        version_index = firstline.find("Version")

        # Get version
        if version_index != -1:
          comma_index = firstline.find(",", version_index)
          if comma_index != -1:
            currentver = firstline[version_index + len("Version"):comma_index]
          else:
            currentver = 'Not Found'
        else:
          currentver = 'Not Found'

        bulk_tree.set(item_id, "#4", currentver)
        bulk_tree.update_idletasks()
        
        currentconfig = net_connect.send_command('show run', read_timeout=300)

        currentint = net_connect.send_command('show ip int br', read_timeout=300)

        currentvlan = net_connect.send_command('show vlan', read_timeout=300)

        output = net_connect.send_command('dir flash:')
        bytes_free_pattern = r'\((\d+) bytes free\)'
        matches = re.search(bytes_free_pattern, output)

        if matches:
          free_bytes = int(matches.group(1))
          if free_bytes > size:
            bulk_tree.set(item_id, "#5", "Available")
            bulk_tree.update_idletasks()

          elif free_bytes < size:
            bulk_tree.set(item_id, "#5", "Not Available")
            bulk_tree.update_idletasks()
            output = net_connect.send_command('install remove inactive',expect_string='install_remove:')

            while True:
              output_part = net_connect.read_channel()
              if output_part:
                bulk_tree.set(item_id, "#5", "Cleaning Flash..")
                bulk_tree.update_idletasks()

              if '[y/n]' in output_part:
                output += net_connect.send_command_timing("y")

              if device_prompt in output_part:
                break
              
              
              

              time.sleep(3)

            bulk_tree.set(item_id, "#5", "Cleaned Up!")
            bulk_tree.update_idletasks()
            time.sleep(2)
            bulk_tree.set(item_id, "#5", "Run Again Later")
            bulk_tree.update_idletasks()
            net_connect.disconnect()
            return
            
        else:
          bulk_tree.set(item_id, "#5", "ERR")
          bulk_tree.update_idletasks()
          net_connect.disconnect()
          return
          
        while True:
          device_prompt = net_connect.find_prompt()
          # Copy firmware
          if protocol == 'tftp':
            output = net_connect.send_command_timing('copy ' + protocol + '://' + tftp_server + '/' + path + ' flash:', read_timeout=100)
              
          else:
            output = net_connect.send_command_timing('copy ' + protocol + '://' + 'compnet:C0mpn3t!@' + tftp_server + '/' + path + ' flash:', read_timeout=100)
              
          # confirmation prompt enter empty string biar enter
          output = net_connect.send_command('\n', expect_string='Accessing ' + protocol + '://', read_timeout=100)
        
          while True:
            output_part = net_connect.read_channel()
            
            if output_part:
              bulk_tree.set(item_id, "#6", "Copying..")
              bulk_tree.update_idletasks()
          
            if device_prompt in output_part:
              break

            time.sleep(3)

          output = net_connect.send_command('dir flash:*.bin', read_timeout=300)

          # confirm apakah file udh ad di flash or not, kalau ad kita ganti system boot ke firmware yg ud dicopy
          if firmware in output:
            bulk_tree.set(item_id, "#6", "Success")
            bulk_tree.update_idletasks()
            break
            
          else:
            choice = messagebox.askquestion('Process No. ' + str(number) + ' IP: ' + ip, 'Failed to copy file. Do you want to try again?')
            bulk_tree.set(item_id, "#6", "Fail")
            bulk_tree.update_idletasks()
            if choice.lower() != 'yes':
              continue
            else:
              return
        
        #Verify MD5
        output = net_connect.send_command('verify /md5 flash:' + firmware + ' ' + hash_value ,expect_string='...')

        verified = False

        while True:
          output_part = net_connect.read_channel()
      
          if output_part:
            bulk_tree.set(item_id, "#7", "Verifying..")
            bulk_tree.update_idletasks()
          
          if 'Verified' in output_part:
            verified = True
            break

          if device_prompt in output_part:
            break

          time.sleep(3)

        if verified == True:
          # Upgrade firmware
          bulk_tree.set(item_id, "#7", "Success")
          bulk_tree.update_idletasks()

        else:
          bulk_tree.set(item_id, "#7", "Fail")
          bulk_tree.update_idletasks()
          net_connect.disconnect()
          return

        output = net_connect.send_config_set('no boot system')

        output = net_connect.send_config_set('boot system flash:packages.conf')

        output = net_connect.send_config_set('no boot manual')

        output = net_connect.send_command('write memory', read_timeout=300)
        
        bulk_tree.set(item_id, "#8", "Upgrading..")
        bulk_tree.update_idletasks()

        output = net_connect.send_command('install add file flash:' + firmware + ' activate commit',expect_string='install_add_activate_commit')
        
        while True:
          output_part = net_connect.read_channel()
          if output_part:
            bulk_tree.set(item_id, "#8", "Install add..")
            bulk_tree.update_idletasks()
  
          if "[y/n]" in output_part:
            output += net_connect.send_command_timing("y", strip_prompt=False, strip_command=False)

          if device_prompt in output_part:
            break

          time.sleep(3)

        bulk_tree.set(item_id, "#8", "Done")
        bulk_tree.update_idletasks()
        net_connect.disconnect()
        bulk_tree.set(item_id, "#9", "Rebooting..")
        bulk_tree.set(item_id, "#10", "Reconnecting..")
        bulk_tree.update_idletasks()

        reconnected = False
        while not reconnected:
          net_connect, error = check_connection(cisco_device)
          if error:
            bulk_tree.set(item_id, "#10", "Reconnecting..")
            bulk_tree.update_idletasks()
            reconnected = False
            time.sleep(2)
          else:
            isenable = net_connect.check_enable_mode()
            if isenable == False:
              net_connect.enable()
              bulk_tree.set(item_id, "#9", "UP")
              bulk_tree.set(item_id, "#10", "Reconnected")
              bulk_tree.update_idletasks()
              reconnected = True
              break
            else:
              bulk_tree.set(item_id, "#9", "UP")
              bulk_tree.set(item_id, "#10", "Reconnected")
              bulk_tree.update_idletasks()
              reconnected = True
              break
          
        net_connect, error = check_connection(cisco_device)
        if error:
          tk.messagebox.showinfo('Error Occured', error)
          return
        else:
          isenable = net_connect.check_enable_mode()
          if isenable == False:
            net_connect.enable()
          else:
            device_prompt = net_connect.find_prompt()
            
          if cleanup == 'yes':
            output = net_connect.send_command('install remove inactive',expect_string='install_remove:',read_timeout=600)

            while True:
              output_part = net_connect.read_channel()
              if output_part:
                bulk_tree.set(item_id, "#11", "Cleaning Flash..")
                bulk_tree.update_idletasks()

              if 'Do you want to remove the above files? [y/n]' in output_part:
                output += net_connect.send_command_timing("y",read_timeout=600)

              if device_prompt in output_part:
                break

              time.sleep(3)

            bulk_tree.set(item_id, "#11", "Cleaned Up!")
            bulk_tree.update_idletasks()

          else:
            bulk_tree.set(item_id, "#11", "No cleanup")
            bulk_tree.update_idletasks()
          
          shupdatever = net_connect.send_command('show ver', read_timeout=300)
          firstline = shupdatever.strip().split('\n')[1]
          version_index = firstline.find("Version")

          # Get version after upd
          if version_index != -1:
            comma_index = firstline.find(",", version_index)
            if comma_index != -1:
              updatever = firstline[version_index + len("Version"):comma_index]
            else:
              updatever = 'Not Found'
          else:
            updatever = 'Not Found'
              
          bulk_tree.set(item_id, "#11", updatever)
          bulk_tree.update_idletasks()

          if updatever != currentver:
            #config verify
            bulk_tree.set(item_id, "#12", "Verifying..")
            bulk_tree.update_idletasks()

            updateconfig = net_connect.send_command('show run', read_timeout=300)
            
            updateconf_lines = updateconfig.strip().split('\n')
            currentconf_lines = currentconfig.strip().split('\n')

            confdiff = difflib.unified_diff(currentconf_lines, updateconf_lines)
            # Check if there are differences
            if any(confdiff):
              added_lines =[]
              removed_lines = []
              # Classify lines as added (+) or removed (-)
              for line in confdiff:
                if line.startswith('+'):
                  added_lines.append(line[1:])  
                elif line.startswith('-'):
                  removed_lines.append(line[1:]) 

              bulk_tree.set(item_id, "#12", "Not Match")
              bulk_tree.update_idletasks()

              conf_filename = f"{switch_type}_{ip}_conf.txt"
              with open(os.path.join(save_path, conf_filename), 'w') as f:
                f.write("Added lines:\n")
                for line in added_lines:
                  f.write(f"+ {line}\n")
                
                f.write("\nRemoved lines:\n")
                for line in removed_lines:
                  f.write(f"- {line}\n")
                  
            else:
              # If no differences, display confirmation message
              bulk_tree.set(item_id, "#12", "Match")
              bulk_tree.update_idletasks()

            bulk_tree.set(item_id, "#13", "Verifying..")
            bulk_tree.update_idletasks()

            updateint = net_connect.send_command('show ip int br', read_timeout=300)
            updateint_lines = updateint.strip().split('\n')
            currentint_lines = currentint.strip().split('\n')
            
            intdiff = difflib.unified_diff(currentint_lines, updateint_lines)
            # Check if there are differences
            if any(intdiff):
              added_lines =[]
              removed_lines = []
              # Classify lines as added (+) or removed (-)
              for line in intdiff:
                if line.startswith('+'):
                  added_lines.append(line[1:])  
                elif line.startswith('-'):
                  removed_lines.append(line[1:])  

              bulk_tree.set(item_id, "#13", "Not Match")
              bulk_tree.update_idletasks()

              int_filename = f"{switch_type}_{ip}_int.txt"
              with open(os.path.join(save_path, int_filename), 'w') as f:
                f.write("Added lines:\n")
                for line in added_lines:
                  f.write(f"+ {line}\n")
                
                f.write("\nRemoved lines:\n")
                for line in removed_lines:
                  f.write(f"- {line}\n")      
            else:
              # If no differences, display confirmation message
              bulk_tree.set(item_id, "#13", "Match")
              bulk_tree.update_idletasks()
                
            bulk_tree.set(item_id, "#14", "Verifying..")
            bulk_tree.update_idletasks()

            updatevlan = net_connect.send_command('show vlan', read_timeout=300)
            net_connect.disconnect()
            updatevlan_lines = updatevlan.strip().split('\n')
            currentvlan_lines = currentvlan.strip().split('\n')

            vlandiff = difflib.unified_diff(updatevlan_lines, currentvlan_lines)

            # Check if there are differences
            if any(vlandiff):
              added_lines =[]
              removed_lines = []
              # Classify lines as added (+) or removed (-)
              for line in vlandiff:
                if line.startswith('+'):
                  added_lines.append(line[1:])  
                elif line.startswith('-'):
                  removed_lines.append(line[1:]) 

              bulk_tree.set(item_id, "#14", "Not Match")
              bulk_tree.update_idletasks()

              vlan_filename = f"{switch_type}_{ip}_vlan.txt"
              with open(os.path.join(save_path, vlan_filename), 'w') as f:
                f.write("Added lines:\n")
                for line in added_lines:
                  f.write(f"+ {line}\n")
                
                f.write("\nRemoved lines:\n")
                for line in removed_lines:
                  f.write(f"- {line}\n")
            else:
              # If no differences, display confirmation message
              bulk_tree.set(item_id, "#14", "Match")
              bulk_tree.update_idletasks()
              
            bulk_tree.set(item_id, "#15", "Done!")
            bulk_tree.update_idletasks()
            time.sleep(3)

          else:
            bulk_tree.set(item_id, "#11", "Not Updated")
            bulk_tree.update_idletasks()
            net_connect.disconnect() 
              
  style = ttk.Style()
  style.layout("Treeview",[('Treeview.treearea', {'sticky': 'nswe'})]) 
  style.layout("Custom.Treeview.Heading", style.layout("Treeview.Heading"))

  # Custom separator line style
  style.configure("Custom.Treeview", background="#D3D3D3")
  style.map("Custom.Treeview", foreground=[('selected', 'black')])
  
  bold_font = font.Font(family="TkDefaultFont", weight="bold",size=10)
  
  info_label = ttk.Label(bulk_frame, text='CSV Format = type, version, ip,user, password, secret, protocol (ftp/tftp), serverip', font=bold_font)
  info_label.grid(row=1, column=0, padx=(0,10), pady=5,columnspan=2)
  
  path_label = ttk.Label(bulk_frame, text='Difference Log File Path:')
  path_label.grid(row=2, column=0, padx=(0,200), pady=5,columnspan=2)
  path_entry = ttk.Entry(bulk_frame, width=23)
  path_entry.grid(row=3, column=0, padx=(0,200), pady=3,columnspan=2)
  
  clean_var = tk.StringVar(value='no')
  cleanup_label = ttk.Label(bulk_frame, text='Clean flash after update? (IOS XE)')
  cleanup_label.grid(row=2, column=0,columnspan=2,padx=(200,0))
  cleanup_dropdown = ttk.Combobox(bulk_frame, textvariable=clean_var, values=['yes', 'no'])
  cleanup_dropdown.grid(row=3, column=0,columnspan=2,padx=(200,0))
  
  print(clean_var.get())
  # debug check
  def on_clean_change(event):
    if clean_var.get() == 'yes':
      print('yessir')
    else:
      print('nossir')

  cleanup_dropdown.bind('<<ComboboxSelected>>', on_clean_change)
  
  available_ver_label = ttk.Label(bulk_frame, text='Check Available Version for type:')
  available_ver_label.grid(row=4, column=0, padx=(10,0))
  available_ver_var = tk.StringVar()
  available_ver_dropdown = ttk.Combobox(bulk_frame, textvariable=available_ver_var, state='readonly', width=25)
  available_ver_dropdown.grid(row=5, column=0, padx=(10,0))
  available_ver_dropdown.bind('<<ComboboxSelected>>', fetch_versions)
  fetch_available_switch_types()

  version_frame = tk.Frame(bulk_frame)
  version_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=5)

  # Create a scrollbar for the version_text
  version_scrollbar = tk.Scrollbar(version_frame, orient="vertical")
  version_scrollbar.pack(side="right", fill="y")

  # Create the version_text widget
  version_text = tk.Text(version_frame, height=5, width=20, yscrollcommand=version_scrollbar.set)
  version_text.pack(side="left", fill="both", expand=True)
  version_scrollbar.config(command=version_text.yview)

  # Button to open file explorer
  open_button = ttk.Button(bulk_frame, text="Import CSV File", command=display_bulks)
  open_button.grid(row=7, column=0, padx=10, pady=5, columnspan=2)

  
  bulk_tree = ttk.Treeview(bulk_frame, columns=[f"#{i}" for i in range(1, len(header) + 1)], show="headings",height=23,style="Custom.Treeview")
  bulk_tree.grid(row=8, column=0)
  for i, col in enumerate(header):
    bulk_tree.heading(f"#{i+1}", text=col)
    bulk_tree.column(f"#{i+1}", width=90, stretch=tk.YES)

  # Add scrollbar to the Treeview
  scrollbar = ttk.Scrollbar(bulk_frame, orient="vertical", command=bulk_tree.yview)
  bulk_tree.configure(yscroll=scrollbar.set)
  scrollbar.grid(row=8, column=1, sticky="ns")

  bulk_frame.grid_rowconfigure(3, weight=1)
  bulk_frame.grid_columnconfigure(1, weight=1)

  bulk_frame.pack()

def fetch_swtype():
  global fetch_available_switch_types
  fetch_available_switch_types()
