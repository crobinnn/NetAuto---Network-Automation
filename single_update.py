import tkinter as tk
import db_connection as db
import threading
import time
import difflib
import re
import json
from netmiko import ConnectHandler
from tkinter import ttk,simpledialog,messagebox

# Single mode update UI & functions
def create_single_gui(single_frame):
  # Get data from JSON local file as db
  json_data = db.json_data
  file_path = db.file_path

  # Get switch types available from json file
  def fetch_available_switch_types(event=None):
    if json_data is None:
      output_text.insert(tk.END, "Cannot access database. JSON not loaded.\n")
      return
      
    try:
      switch_types = list(json_data.get("UpdateDB", {}).keys())
      switch_type_dropdown['values'] = switch_types
    except Exception as e:
      output_text.insert(tk.END,f"Failed Fetching SW types. {e}")
  
  # Get versions available for update from switch type
  def fetch_versions(event=None):
    version_var.set("")
    global switch_type
    switch_type = switch_type_var.get()
    if json_data is None:
      output_text.insert(tk.END, "Cannot access database. JSON not loaded.\n")
      return
    try:
      switch_data = json_data.get("UpdateDB", {}).get(switch_type, {})
      versions = [version["name"] for version in switch_data.get("versions", [])]
      version_dropdown.config(values=versions)
      version_dropdown.config(state="readonly")
    except Exception as e:
      output_text.insert(tk.END,"Failed fetching version")
  
  # Retrieves information about the version to be updated
  def retrieve_data(event=None):
    global version_name, hash_value, firmware, size, path
    version_name = version_var.get()
    if json_data is None:
      output_text.insert(tk.END, "Cannot access database. JSON not loaded.\n")
      return
    try:
      switch_data = json_data.get("UpdateDB", {}).get(switch_type, {})
      for version in switch_data.get("versions", []):
        if version["name"] == version_name:
          hash_value = version["hash"]
          firmware = version["firmware"]
          size = int(version["size"])
          path = version["path"]
          output_text.delete('1.0', tk.END)
          output_text.insert(tk.END,f"Hash: {hash_value}\nFirmware: {firmware}\nSize: {size}\nPath: {path}")
          # You can assign these values to variables if needed
          break
      else:
        output_text.insert(tk.END, "Version not found")
    except Exception as e:
      output_text.insert(tk.END,f"Error retrieving data: {e}")
  
  # Add new switch type to the db
  def add_new_device(event=None):
    output_text.delete('1.0', tk.END)
    global switch_type, version_name, hash_value, firmware, size, path
    if json_data is None:
        output_text.insert(tk.END, "Cannot access database. JSON not loaded.\n")
        return
    new_window = tk.Toplevel(single_frame)
    new_window.title("Add New Device")

    switch_type_label = tk.Label(new_window, text="Enter Switch Type:")
    switch_type_label.grid(row=0, column=0)
    switch_type_entry = tk.Entry(new_window)
    switch_type_entry.grid(row=0, column=1)

    version_name_label = tk.Label(new_window, text="Enter Version Name:")
    version_name_label.grid(row=1, column=0)
    version_name_entry = tk.Entry(new_window)
    version_name_entry.grid(row=1, column=1)

    firmware_label = tk.Label(new_window, text="Enter Firmware Name:")
    firmware_label.grid(row=2, column=0)
    firmware_entry = tk.Entry(new_window)
    firmware_entry.grid(row=2, column=1)

    hash_label = tk.Label(new_window, text="Enter Hash:")
    hash_label.grid(row=3, column=0)
    hash_entry = tk.Entry(new_window)
    hash_entry.grid(row=3, column=1)

    size_label = tk.Label(new_window, text="Enter Size:")
    size_label.grid(row=4, column=0)
    size_entry = tk.Entry(new_window)
    size_entry.grid(row=4, column=1)

    path_label = tk.Label(new_window, text="Enter Path:")
    path_label.grid(row=5, column=0)
    path_entry = tk.Entry(new_window)
    path_entry.grid(row=5, column=1)

    def add_device():
      switch_type = switch_type_entry.get()
      version_name = version_name_entry.get()
      firmware = firmware_entry.get()
      hash_value = hash_entry.get()
      size = size_entry.get()
      path = path_entry.get()

      new_document = {
        "versions": [{
            "name": version_name,
            "firmware": firmware,
            "hash": hash_value,
            "size": int(size),
            "path": path
        }]
      }

      if "UpdateDB" not in json_data:
        json_data["UpdateDB"] = {}
          
      if switch_type in json_data["UpdateDB"]:
        json_data["UpdateDB"][switch_type]["versions"].append(new_document["versions"][0])
      else:
        json_data["UpdateDB"][switch_type] = new_document
      
      with open(file_path, 'w') as file:
        json.dump(json_data, file, indent=4)

      output_text.insert(tk.END, "New device added to the JSON file.")
      fetch_available_switch_types()
      new_window.destroy()

    add_button = tk.Button(new_window, text="Add Device", command=add_device)
    add_button.grid(row=6, column=0, columnspan=2)

  # add new version to existing switch type
  def add_new_version(event=None):
    output_text.delete('1.0', tk.END)
    global switch_type
    if json_data is None:
        output_text.insert(tk.END, "Cannot access database. JSON file not loaded.\n")
        return
    new_window = tk.Toplevel(single_frame)
    new_window.title("Add New Version")

    switch_type_label = tk.Label(new_window, text="Select Switch Type:")
    switch_type_label.grid(row=0, column=0)

    switch_type_var = tk.StringVar()
    switch_type_dropdown = ttk.Combobox(new_window, textvariable=switch_type_var, state="readonly")
    switch_type_dropdown.grid(row=0, column=1)

    switch_types = list(json_data.get("UpdateDB", {}).keys())
    switch_type_dropdown['values'] = switch_types

    def add_version():
      selected_switch_type = switch_type_var.get()
      if selected_switch_type:
        new_version_name = version_name_entry.get()
        new_firmware = firmware_entry.get()
        new_hash = hash_entry.get()
        new_size = size_entry.get()
        new_path = path_entry.get()

        # Update existing document with new version
        if selected_switch_type in json_data["UpdateDB"]:
          json_data["UpdateDB"][selected_switch_type]["versions"].append({
            "name": new_version_name,
            "firmware": new_firmware,
            "hash": new_hash,
            "size": int(new_size),
            "path": new_path
          })
          with open(file_path, 'w') as file:
            json.dump(json_data, file, indent=4)
          output_text.insert(tk.END, "New version added to the existing device.")
          version_var.set("")
          fetch_versions()
          new_window.destroy()
        else:
            output_text.insert(tk.END, "Switch type not found in JSON data")
      else:
          output_text.insert(tk.END, "Please select a switch type first.")

    version_name_label = tk.Label(new_window, text="Enter Version Name:")
    version_name_label.grid(row=1, column=0)
    version_name_entry = tk.Entry(new_window)
    version_name_entry.grid(row=1, column=1)

    firmware_label = tk.Label(new_window, text="Enter Firmware Name:")
    firmware_label.grid(row=2, column=0)
    firmware_entry = tk.Entry(new_window)
    firmware_entry.grid(row=2, column=1)

    hash_label = tk.Label(new_window, text="Enter Hash:")
    hash_label.grid(row=3, column=0)
    hash_entry = tk.Entry(new_window)
    hash_entry.grid(row=3, column=1)

    size_label = tk.Label(new_window, text="Enter Size:")
    size_label.grid(row=4, column=0)
    size_entry = tk.Entry(new_window)
    size_entry.grid(row=4, column=1)

    path_label = tk.Label(new_window, text="Enter Path:")
    path_label.grid(row=5, column=0)
    path_entry = tk.Entry(new_window)
    path_entry.grid(row=5, column=1)

    add_button = tk.Button(new_window, text="Add Version to existing Device", command=add_version)
    add_button.grid(row=6, column=0, columnspan=2)
  
  # Delete switch type from db
  def delete_switch_type(event=None):
    output_text.delete('1.0', tk.END)
    switch_type = switch_type_var.get()
    if json_data is None:
      output_text.insert(tk.END, "Cannot access database. JSON not loaded.\n")
      return
    if switch_type:
      confirm = simpledialog.askstring("Confirmation", f"Are you sure you want to delete {switch_type}? (yes/no)")
      if confirm and confirm.lower() == "yes":
        try:
          if switch_type in json_data.get("UpdateDB", {}):
            del json_data["UpdateDB"][switch_type]
            with open(file_path, 'w') as file:
                json.dump(json_data, file, indent=4)
            output_text.insert(tk.END, f"Switch type '{switch_type}' deleted from the JSON file.")
            version_var.set("")
            switch_type_var.set("")
            fetch_available_switch_types()
            fetch_versions()
          else:
            output_text.insert(tk.END, f"Switch type '{switch_type}' not found in JSON data.")
        except Exception as e:
          output_text.insert(tk.END, f"Error deleting switch type: {e}")
    else:
      output_text.insert(tk.END,"Please select switch type to delete.")

  # delete version from existing sw type
  def delete_version(event=None):
    output_text.delete('1.0', tk.END)
    switch_type = switch_type_var.get()
    version_name = version_var.get()
    
    if json_data is None:
      output_text.insert(tk.END, "Cannot access database. JSON not loaded.\n")
      return
      
    if switch_type and version_name:
      confirm = simpledialog.askstring("Confirmation", f"Are you sure you want to delete version '{version_name}' of {switch_type}? (yes/no)")
      if confirm and confirm.lower() == "yes":
        try:
          switch_data = json_data.get("UpdateDB", {}).get(switch_type, {})
          versions = switch_data.get("versions", [])
          for version in versions:
            if version["name"] == version_name:
              versions.remove(version)
              # Save changes to the JSON file
           
              json_data["UpdateDB"][switch_type]["versions"] = versions
            
              with open(file_path, 'w') as file:
                json.dump(json_data, file, indent=4)
              output_text.insert(tk.END, f"Version '{version_name}' deleted from the switch type '{switch_type}'.")
              version_var.set("")
              fetch_versions()  # Refresh version dropdown
              return
          output_text.insert(tk.END, f"Version '{version_name}' not found in the switch type '{switch_type}'.")
        except Exception as e:
            output_text.insert(tk.END, f"Error deleting version: {e}")
    else:
      output_text.insert(tk.END,"Please select both switch type and version to delete.")

  # Show current database of devices list
  def show_update_db_popup():
    popup_window = tk.Toplevel()
    popup_window.title("UpdateDB Contents")

    text_frame = tk.Frame(popup_window)
    text_frame.pack(fill=tk.BOTH, expand=True)

    text_widget = tk.Text(text_frame, wrap=tk.WORD, height=20, width=100)
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text_widget.config(yscrollcommand=scrollbar.set)

    if json_data is None or "UpdateDB" not in json_data:
      text_widget.insert(tk.END, "Cannot access database or UpdateDB not loaded.\n")
      return

    try:
      update_db = json_data["UpdateDB"]
      for switch_type, switch_info in update_db.items():
        text_widget.insert(tk.END, f"{switch_type}\n")
        for version in switch_info.get("versions", []):
          text_widget.insert(tk.END, f"  > version {version.get('name', 'N/A')}\n")
          text_widget.insert(tk.END, f"    - firmware = {version.get('firmware', 'N/A')}\n")
          text_widget.insert(tk.END, f"    - hash = {version.get('hash', 'N/A')}\n")
          text_widget.insert(tk.END, f"    - size = {version.get('size', 'N/A')}\n")
          text_widget.insert(tk.END, f"    - path = {version.get('path', 'N/A')}\n")
          text_widget.insert(tk.END, "\n")
    except Exception as e:
      text_widget.insert(tk.END, f"Error displaying data: {e}\n")

    popup_window.geometry('800x600')
  
  # Start ssh & perform update function
  def start_ssh():
    output_text.delete('1.0', tk.END)
    threading.Thread(target=cisco_ssh).start()

  # ssh for cisco device
  def cisco_ssh():
    global output_part
    # Ambil data dr input field GUI
    host = ip_entry.get()
    username = username_entry.get()
    password = password_entry.get()
    tftp_server = tftp_entry.get()
    protocol = select_transfer_var.get()
    secret = secret_entry.get()

    # SSH parameter from user input before
    if switch_type == 'C2960': 
      cisco_device = {
        'device_type': 'cisco_ios',
        'host': host,
        'username': username,
        'password': password,
        'port': 22,
      }
    else:
      cisco_device = {
        'device_type': 'cisco_xe',
        'host': host,
        'username': username,
        'password': password,
        'port': 22,
      }

    if switch_type == 'C2960':
      try:
        output_text.insert(tk.END,f'Connecting to Cisco {switch_type} via {protocol} \n') 
        output_text.update_idletasks() 
        output_text.insert(tk.END, str(size) + '\n')
        output_text.update_idletasks() 
        
        with ConnectHandler(**cisco_device) as net_connect:
          isenable = net_connect.check_enable_mode()
          if isenable == False:
            output_text.insert(tk.END, 'Currently in user exec mode, enabling...')
            output_text.update_idletasks() 
            output_text.see(tk.END)
            net_connect.enable()
            output_text.insert(tk.END, 'Entered privileged exec mode')
            output_text.update_idletasks() 
            output_text.see(tk.END)
            device_prompt = net_connect.find_prompt()
          else:
            device_prompt = net_connect.find_prompt()
            output_text.insert(tk.END, 'Currently in privileged exec mode already')
            output_text.update_idletasks() 
            output_text.see(tk.END)

          output_text.insert(tk.END, net_connect.find_prompt())
          shcurrentver = net_connect.send_command_timing('show ver', delay_factor=4, max_loops=1000)
          currentver = shcurrentver.strip().split('\n')[0]
          output_text.insert(tk.END, 'Current Ver: ' + currentver + '\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)

          output_text.insert(tk.END, 'Getting existing configuration...\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)
          currentconfig = net_connect.send_command('show run', read_timeout=300)
          output_text.insert(tk.END, currentconfig + '\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)

          output_text.insert(tk.END, 'Getting existing interface info...\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)
          currentint = net_connect.send_command('show ip int br', read_timeout=300)
          output_text.insert(tk.END, currentint + '\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)

          output_text.insert(tk.END, 'Getting existing vlan configuration...\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)
          currentvlan = net_connect.send_command('show vlan', read_timeout=300)
          output_text.insert(tk.END, currentvlan + '\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)

          # Check Flash Storage Switch
          output_text.insert(tk.END, 'Checking Flash Storage....' + '\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)
          output = net_connect.send_command('dir flash: ')
          print("Raw output from 'dir flash:':\n", output)
          output_text.insert(tk.END, f'Raw output from "dir flash:":\n{output}\n')
          output_text.update_idletasks()
          output_text.see(tk.END)
          bytes_free_pattern = r'\((\d+) bytes free\)'
          matches = re.search(bytes_free_pattern, output)

          if matches:
            free_bytes = int(matches.group(1))
            if free_bytes > size:
              output_text.insert(tk.END, 'Flash available for upgrade' + '(' + str(free_bytes) + ')' + ', proceeds for upgrading....' + '\n')
              output_text.update_idletasks() 
              output_text.see(tk.END)

              while True:
                device_prompt = net_connect.find_prompt()

                if protocol == 'tftp':
                  output = net_connect.send_command_timing('copy ' + protocol + '://' + tftp_server + '/' + path + ' flash:', read_timeout=5)
                  output_text.insert(tk.END,'copy ' + protocol + '://' + tftp_server + '/' + path + ' flash:' + '\n' )
                  output_text.insert(tk.END, output + '\n')
                  output_text.update_idletasks() 
                  output_text.see(tk.END)
                else:
                  output = net_connect.send_command_timing('copy ' + protocol + '://' + 'compnet:C0mpn3t!@' + tftp_server + '/' + path + ' flash:', read_timeout=5)
                  output_text.insert(tk.END,'copy ' + protocol + '://' + 'compnet:C0mpn3t!@' + tftp_server + '/' + path + ' flash:' + '\n' )
                  output_text.insert(tk.END, output + '\n')
                  output_text.update_idletasks() 
                  output_text.see(tk.END)

                # confirmation prompt enter empty string biar enter
                output = net_connect.send_command('\n', expect_string='Accessing ' + protocol + '://', read_timeout=100)
                output_text.insert(tk.END, output + '\n')
                output_text.update_idletasks() 
                output_text.see(tk.END)
                

                while True:
                  output_part = net_connect.read_channel()
                  
                  if output_part:
                    output_text.insert(tk.END, output_part)  
                    output_text.update_idletasks()
                    output_text.see(tk.END)
                  
                  if device_prompt in output_part:
                    break

                  time.sleep(3)

                output = net_connect.send_command_timing('dir flash:*.bin', delay_factor=4, max_loops=1000)
                output_text.insert(tk.END, output + '\n')
                output_text.see(tk.END)

                # confirm apakah file udh ad di flash or not, kalau ad kita ganti system boot ke firmware yg ud dicopy
                if firmware in output:
                  output = net_connect.send_command('verify /md5 flash:' + firmware + ' ' + hash_value ,expect_string='...')
                  output_text.insert(tk.END, output + '\n')
                  output_text.update_idletasks()
                  output_text.see(tk.END)

                  verified = False

                  while True:
                    output_part = net_connect.read_channel()
                
                    if output_part:
                      output_text.insert(tk.END, output_part)  
                      output_text.update_idletasks()
                      output_text.see(tk.END)
                    
                    if 'Verified' in output_part:
                      verified = True
                      break

                    if device_prompt in output_part:
                      break

                    time.sleep(3)

                  if verified == True:
                    output = net_connect.send_config_set('boot system flash:' + firmware)
                    output_text.insert(tk.END, output + '\n')
                    output_text.update_idletasks()
                    output_text.see(tk.END)

                    output = net_connect.send_command('reload', expect_string='[confirm]', delay_factor=4, max_loops=1000, read_timeout=120)
                    output_text.insert(tk.END, output + '\n')
                    output_text.update_idletasks()
                    output_text.see(tk.END)

                    # Confirm reload
                    output = net_connect.send_command_timing('yes', delay_factor=4, max_loops=1000)
                    output_text.insert(tk.END, output + '\n')
                    output_text.update_idletasks()
                    output_text.see(tk.END)

                    net_connect.disconnect()
                    output_text.insert(tk.END, 'Switch is rebooting, Reconnecting. . . ')
                    output_text.see(tk.END)

                    reconnected = False
                    while not reconnected:
                      try:
                        with ConnectHandler(**cisco_device) as net_connect:
                          output_text.insert(tk.END, 'Reconnected successfully.\n')
                          output_text.update_idletasks()
                          output_text.see(tk.END)
                          reconnected = True

                          shupdatever = net_connect.send_command_timing('show ver', delay_factor=4, max_loops=1000)
                          updatever = shupdatever.strip().split('\n')[0]
                          output_text.insert(tk.END, 'After Update Ver: ' + updatever)
                          output_text.insert(tk.END, '\n')
                          output_text.update_idletasks()
                          output_text.see(tk.END)

                          if updatever != currentver:
                            output_text.insert(tk.END, 'Successfully Updated Device Firmware' + '\n')
                            output_text.update_idletasks()
                            output_text.see(tk.END)

                            output_text.insert(tk.END, 'Verifying Configurations...' + '\n')
                            output_text.update_idletasks()
                            output_text.see(tk.END)

                            updateconfig = net_connect.send_command('show run', read_timeout=300)
                            
                            updateconf_lines = updateconfig.strip().split('\n')
                            currentconf_lines = currentconfig.strip().split('\n')

                            confdiff = difflib.unified_diff(currentconf_lines, updateconf_lines)
                            # Check difference in running config
                            if any(confdiff):
                              # If differences exist, show diff
                              output_text.insert(tk.END, 'Differences found in configuration:\n')
                              for line in confdiff:
                                output_text.insert(tk.END, line + '\n')
                            else:
                              # If no differences, show verification
                              output_text.insert(tk.END, 'Configuration Verified!\n')
                           
                            output_text.update_idletasks()
                            output_text.see(tk.END)

                            output_text.insert(tk.END, 'Verifying Interface Status...\n')
                            output_text.update_idletasks() 
                            output_text.see(tk.END)

                            updateint = net_connect.send_command('show ip int br', read_timeout=300)
                            updateint_lines = updateint.strip().split('\n')
                            currentint_lines = currentint.strip().split('\n')
                            
                            intdiff = difflib.unified_diff(currentint_lines, updateint_lines)
                            # Check difference in interface status
                            if any(intdiff):
                              # If differences exist, show diff
                              output_text.insert(tk.END, 'Differences found in interfaces info:\n')
                              for line in intdiff:
                                output_text.insert(tk.END, line + '\n')
                            else:
                              # If no differences, show verification
                              output_text.insert(tk.END, 'Interfaces Verified!\n')
                            
                            output_text.insert(tk.END, 'Verifying VLANs...\n')
                            output_text.update_idletasks() 
                            output_text.see(tk.END)

                            updatevlan = net_connect.send_command('show vlan', read_timeout=300)
                            updatevlan_lines = updatevlan.strip().split('\n')
                            currentvlan_lines = currentvlan.strip().split('\n')

                            vlandiff = difflib.unified_diff(updatevlan_lines, currentvlan_lines)

                            # Check difference in vlan 
                            if any(vlandiff):
                              # If differences exist, show diff
                              output_text.insert(tk.END, 'Differences found in VLAN configuration:\n')
                              for line in vlandiff:
                                output_text.insert(tk.END, line + '\n')
                            else:
                              # If no differences, show verification
                              output_text.insert(tk.END, 'VLAN Configuration Verified!\n')

                            net_connect.disconnect()
                          else:
                            output_text.insert(tk.END, 'Firmware not upgraded, please try again..' + '\n')
                            output_text.update_idletasks()
                            output_text.see(tk.END)
                            net_connect.disconnect()

                      except Exception as e:
                        output_text.insert(tk.END, '. ')
                        output_text.update_idletasks()
                        output_text.see(tk.END)
                        time.sleep(3)
                  else:
                    output_text.insert(tk.END, 'Failed to verify MD5 Hash, Please check your file again')
                    output_text.update_idletasks()
                    output_text.see(tk.END)
                    net_connect.disconnect()

                else:
                  choice = messagebox.askquestion('File Transfer Failed', 'Failed to copy file. Do you want to try again?')
                  output_text.insert(tk.END, 'Fail to copy file, do you want to try again? (yes/no): ' + choice + '\n')
                  if choice.lower() != 'yes':
                    return
                  else:
                    # Continue to try tftp/ftp agane
                    continue

            elif free_bytes < size:
              output_text.insert(tk.END, 'Flash is not enough for upgrade, please free up')
              net_connect.disconnect()
          else:
            output_text.insert(tk.END,'Error Retrieving Flash Information')
            net_connect.disconnect()
                 
      except Exception as e:
        error_message = f'Error: {e}\n'
        output_text.insert(tk.END, error_message)
      
    else:
      # Start SSH for IOS XE
      try:
        output_text.insert(tk.END,'Connecting to Cisco ' + switch_type + ' install XE' + '\n') 
        output_text.update_idletasks() 
        output_text.insert(tk.END, str(size) + '\n')
        output_text.update_idletasks() 

        
        with ConnectHandler(**cisco_device) as net_connect:
          isenable = net_connect.check_enable_mode()
          if isenable == False:
            output_text.insert(tk.END, 'Currently in user exec mode, enabling...')
            output_text.update_idletasks() 
            output_text.see(tk.END)
            net_connect.enable()
            output_text.insert(tk.END, 'Entered privileged exec mode')
            output_text.update_idletasks() 
            output_text.see(tk.END)
            device_prompt = net_connect.find_prompt()
          else:
            device_prompt = net_connect.find_prompt()
            output_text.insert(tk.END, 'Currently in privileged exec mode already')
            output_text.update_idletasks() 
            output_text.see(tk.END)
            
          output_text.insert(tk.END, net_connect.find_prompt())
          shcurrentver = net_connect.send_command_timing('show ver', delay_factor=4, max_loops=1000)
          currentver = shcurrentver.strip().split('\n')[0]
          output_text.insert(tk.END, 'Current Ver: ' + currentver + '\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)

          output_text.insert(tk.END, 'Getting existing configuration...\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)
          currentconfig = net_connect.send_command('show run', read_timeout=300)
          output_text.insert(tk.END, currentconfig + '\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)

          output_text.insert(tk.END, 'Getting existing interface info...\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)
          currentint = net_connect.send_command('show ip int br', read_timeout=300)
          output_text.insert(tk.END, currentint + '\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)

          output_text.insert(tk.END, 'Getting existing vlan configuration...\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)
          currentvlan = net_connect.send_command('show vlan', read_timeout=300)
          output_text.insert(tk.END, currentvlan + '\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)

          # Check Flash Storage Switch
          output_text.insert(tk.END, 'Checking Flash Storage....' + '\n')
          output_text.update_idletasks() 
          output_text.see(tk.END)
          output = net_connect.send_command('dir flash:')
          print("Raw output from 'dir flash:':\n", output)
          output_text.insert(tk.END, f'Raw output from "dir flash:":\n{output}\n')
          output_text.update_idletasks()
          output_text.see(tk.END)
          bytes_free_pattern = r'\((\d+) bytes free\)'
          matches = re.search(bytes_free_pattern, output)
          free_bytes = int(matches.group(1))
        
          if matches:
            free_bytes = int(matches.group(1))
            if free_bytes > size:
              output_text.insert(tk.END, 'Flash available for upgrade' + '(' + str(free_bytes) + ')' + ', proceeds for upgrading....' + '\n')
              output_text.update_idletasks() 
              output_text.see(tk.END)

              while True:
                device_prompt = net_connect.find_prompt()

                if protocol == 'tftp':
                  output = net_connect.send_command_timing('copy ' + protocol + '://' + tftp_server + '/' + path + ' flash:', read_timeout=5)
                  output_text.insert(tk.END,'copy ' + protocol + '://' + tftp_server + '/' + path + ' flash:' + '\n' )
                  output_text.insert(tk.END, output + '\n')
                  output_text.update_idletasks() 
                  output_text.see(tk.END)
                else:
                  output = net_connect.send_command_timing('copy ' + protocol + '://' + 'compnet:C0mpn3t!@' + tftp_server + '/' + path + ' flash:', read_timeout=5)
                  output_text.insert(tk.END,'copy ' + protocol + '://' + 'compnet:C0mpn3t!@' + tftp_server + '/' + path + ' flash:' + '\n' )
                  output_text.insert(tk.END, output + '\n')
                  output_text.update_idletasks() 
                  output_text.see(tk.END)

                # confirmation prompt enter empty string biar enter
                output = net_connect.send_command('\n', expect_string='Accessing ' + protocol + '://', read_timeout=100)
                output_text.insert(tk.END, output + '\n')
                output_text.update_idletasks() 
                output_text.see(tk.END)
                
                while True:
                  output_part = net_connect.read_channel()
                  
                  if output_part:
                    output_text.insert(tk.END, output_part)  
                    output_text.update_idletasks()
                    output_text.see(tk.END)
                  
                  if device_prompt in output_part:
                    break

                  time.sleep(3)

                # confirm apakah copy tftp success or not, kalau ad lanjut cek flash di switch
                output = net_connect.send_command_timing('dir flash:*.bin', delay_factor=4, max_loops=1000)
                output_text.insert(tk.END, output + '\n')
                output_text.see(tk.END)

                # confirm apakah file udh ad di flash or not, kalau ad kita ganti system boot ke firmware yg ud dicopy
                if firmware in output:
                  output = net_connect.send_command('verify /md5 flash:' + firmware + ' ' + hash_value ,expect_string='...')
                  output_text.insert(tk.END, output + '\n')
                  output_text.update_idletasks()
                  output_text.see(tk.END)

                  verified = False

                  while True:
                    output_part = net_connect.read_channel()
                
                    if output_part:
                      output_text.insert(tk.END, output_part)  
                      output_text.update_idletasks()
                      output_text.see(tk.END)
                    
                    if 'Verified' in output_part:
                      verified = True
                      break

                    if device_prompt in output_part:
                      break

                    time.sleep(3)

                  if verified == True:
                    output = net_connect.send_config_set('no boot system')
                    output_text.insert(tk.END, output + '\n')
                    output_text.update_idletasks()
                    output_text.see(tk.END)

                    output = net_connect.send_config_set('boot system flash:packages.conf')
                    output_text.insert(tk.END, output + '\n')
                    output_text.update_idletasks()
                    output_text.see(tk.END)

                    output = net_connect.send_config_set('no boot manual')
                    output_text.insert(tk.END, output + '\n')
                    output_text.update_idletasks()
                    output_text.see(tk.END)

                    output = net_connect.send_command_timing('write memory', delay_factor=4, max_loops=1000)
                    output_text.insert(tk.END, output + '\n')
                    output_text.update_idletasks()
                    output_text.see(tk.END)

                    output = net_connect.send_command('install add file flash:' + firmware + ' activate commit',expect_string='install_add_activate_commit:')
                    output_text.insert(tk.END, output + '\n')
                    output_text.update_idletasks()
                    output_text.see(tk.END)

                    while True:
                      output_part = net_connect.read_channel()
                      if output_part:
                        output_text.insert(tk.END, output_part)  
                        output_text.update_idletasks()
                        output_text.see(tk.END)
              
                      if "[y/n]" in output_part:
                        output += net_connect.send_command_timing("y", strip_prompt=False, strip_command=False)

                      if device_prompt in output_part:
                        break

                      time.sleep(3)

                    net_connect.disconnect()
                    output_text.insert(tk.END, 'Switch is rebooting, reconnecting. . . ')
                    output_text.see(tk.END)

                    reconnected = False
                    while not reconnected:
                      try:
                        with ConnectHandler(**cisco_device) as net_connect:
                          output_text.insert(tk.END, 'Reconnected successfully.\n')
                          output_text.update_idletasks()
                          output_text.see(tk.END)
                          reconnected = True

                          output_text.insert(tk.END,'Showing new .pkg & .conf files...\n')
                          output_text.update_idletasks()
                          output_text.see(tk.END)

                          output = net_connect.send_command_timing('dir flash:*.pkg', delay_factor=4, max_loops=1000)
                          output_text.insert(tk.END, output + '\n')
                          output_text.update_idletasks()
                          output_text.see(tk.END)

                          output = net_connect.send_command_timing('dir flash:*.conf', delay_factor=4, max_loops=1000)
                          output_text.insert(tk.END, output + '\n')
                          output_text.update_idletasks()
                          output_text.see(tk.END)

                          output_text.insert(tk.END, 'Checking version. . .\n')
                          output_text.update_idletasks()
                          output_text.see(tk.END)

                          # Check version, udah update/belum
                          shupdatever = net_connect.send_command_timing('show ver', delay_factor=4, max_loops=1000)
                          updatever = shupdatever.strip().split('\n')[0]
                          output_text.insert(tk.END, 'After Update Ver: ' + updatever)
                          output_text.insert(tk.END, '\n')
                          output_text.update_idletasks()
                          output_text.see(tk.END)

                          if updatever != currentver:
                            output_text.insert(tk.END, 'Successfully Updated Device Firmware' + '\n')
                            output_text.update_idletasks()
                            output_text.see(tk.END)

                            output_text.insert(tk.END, 'Verifying Configurations...' + '\n')
                            output_text.update_idletasks()
                            output_text.see(tk.END)

                            updateconfig = net_connect.send_command('show run', read_timeout=300)
                            
                            updateconf_lines = updateconfig.strip().split('\n')
                            currentconf_lines = currentconfig.strip().split('\n')

                            confdiff = difflib.unified_diff(currentconf_lines, updateconf_lines)
                            # Check difference in running config
                            if any(confdiff):
                              # If differences exist, show diff
                              output_text.insert(tk.END, 'Differences found in configuration:\n')
                              for line in confdiff:
                                output_text.insert(tk.END, line + '\n')
                            else:
                              # If no differences, show verification
                              output_text.insert(tk.END, 'Configuration Verified!\n')

                            output_text.update_idletasks()
                            output_text.see(tk.END)

                            output_text.insert(tk.END, 'Verifying Interface Status...\n')
                            output_text.update_idletasks() 
                            output_text.see(tk.END)

                            updateint = net_connect.send_command('show ip int br', read_timeout=300)
                            updateint_lines = updateint.strip().split('\n')
                            currentint_lines = currentint.strip().split('\n')
                            
                            intdiff = difflib.unified_diff(currentint_lines, updateint_lines)
                            # Check difference in interface status
                            if any(intdiff):
                              # If differences exist, show diff
                              output_text.insert(tk.END, 'Differences found in interfaces info:\n')
                              for line in intdiff:
                                output_text.insert(tk.END, line + '\n')
                            else:
                              # If no differences, show verification
                              output_text.insert(tk.END, 'Interfaces Verified!\n')
                            
                            output_text.insert(tk.END, 'Verifying VLANs...\n')
                            output_text.update_idletasks() 
                            output_text.see(tk.END)

                            updatevlan = net_connect.send_command('show vlan', read_timeout=300)
                            updatevlan_lines = updatevlan.strip().split('\n')
                            currentvlan_lines = currentvlan.strip().split('\n')

                            vlandiff = difflib.unified_diff(updatevlan_lines, currentvlan_lines)

                            # Check difference in vlan
                            if any(vlandiff):
                              # If differences exist, show diff
                              output_text.insert(tk.END, 'Differences found in VLAN configuration:\n')
                              for line in vlandiff:
                                output_text.insert(tk.END, line + '\n')
                            else:
                              # If no differences, show verification
                              output_text.insert(tk.END, 'VLAN Configuration Verified!\n')

                            net_connect.disconnect()
                            
                          else:
                            output_text.insert(tk.END, 'Firmware not upgraded, please try again..' + '\n')
                            output_text.update_idletasks()
                            output_text.see(tk.END)
                            net_connect.disconnect()

                      except Exception as e:
                        output_text.insert(tk.END, '. ')
                        output_text.update_idletasks()
                        output_text.see(tk.END)
                        time.sleep(3)
                
                  else:
                    output_text.insert(tk.END, 'Failed to verify MD5 Hash, Check your file again')
                    output_text.update_idletasks()
                    output_text.see(tk.END)
                    net_connect.disconnect()
                    
                else:
                  choice = messagebox.askquestion('File Transfer Failed', 'Failed to copy file. Do you want to try again?')
                  output_text.insert(tk.END, 'Fail to copy file, do you want to try again? (yes/no): ' + choice + '\n')
                  if choice.lower() != 'yes':
                    return
                  else:
                    # Continue retry tftp/ftp agane
                    continue

            elif free_bytes < size:
              output_text.insert(tk.END, 'Flash is not enough for upgrade, deleting inactive installation files')
              output_text.update_idletasks()
              output = net_connect.send_command('install remove inactive',expect_string='install_remove:')
              output_text.insert(tk.END, output + '\n')
              output_text.update_idletasks()
              output_text.see(tk.END)

              while True:
                output_part = net_connect.read_channel()
                if output_part:
                  output_text.insert(tk.END, output_part)  
                  output_text.update_idletasks()
                  output_text.see(tk.END)  

                if '[y/n]' in output_part:
                  output += net_connect.send_command_timing("y")

                if device_prompt in output_part:
                  break

                time.sleep(3)

              output_text.insert(tk.END, 'Done Cleaning, please start the program again..\n')
              output_text.update_idletasks()
              output_text.see(tk.END)
              net_connect.disconnect()

          else:
            output_text.insert(tk.END,'Error Retrieving Flash Information')
            net_connect.disconnect()

      except Exception as e:
        error_message = f'Error: {e}\n'
        output_text.insert(tk.END, error_message)

  # Switch type model selection dropdown menu
  switch_type_label = ttk.Label(single_frame, text='Select Switch Type:')
  switch_type_label.grid(row=1, column=0, padx=10, pady=3, sticky=tk.W)
  switch_type_var = tk.StringVar()
  switch_type_dropdown = ttk.Combobox(single_frame, textvariable=switch_type_var, state='readonly')
  switch_type_dropdown.grid(row=1, column=1,pady=3)
  switch_type_dropdown.bind('<<ComboboxSelected>>', fetch_versions)

  # OS Selection dropdown menu
  version_label = ttk.Label(single_frame, text='Select Version:')
  version_label.grid(row=2, column=0, padx=10, pady=3, sticky=tk.W)
  version_var = tk.StringVar()
  version_dropdown = ttk.Combobox(single_frame, textvariable=version_var,state='disabled')
  version_dropdown.grid(row=2, column=1, pady=3)
  version_dropdown.bind('<<ComboboxSelected>>', retrieve_data)

  # input field buat IP, user, pass, server tftp
  ip_label = ttk.Label(single_frame, text='Device IP:')
  ip_label.grid(row=3, column=0, padx=10, pady=3, sticky=tk.W)
  ip_entry = ttk.Entry(single_frame, width=23)
  ip_entry.grid(row=3, column=1, pady=3)

  username_label = ttk.Label(single_frame, text='Username:')
  username_label.grid(row=4, column=0, padx=10, pady=3, sticky=tk.W)
  username_entry = ttk.Entry(single_frame, width=23)
  username_entry.grid(row=4, column=1, pady=3)

  password_label = ttk.Label(single_frame, text='Password:')
  password_label.grid(row=5, column=0, padx=10, pady=3, sticky=tk.W)
  password_entry = ttk.Entry(single_frame, show='*', width=23)
  password_entry.grid(row=5, column=1, pady=3)
  
  secret_label = ttk.Label(single_frame, text='Secret (if needed):')
  secret_label.grid(row=6, column=0, padx=10, pady=3, sticky=tk.W)
  secret_entry = ttk.Entry(single_frame, width=23)
  secret_entry.grid(row=6, column=1, pady=3)

  select_transfer_label = ttk.Label(single_frame, text='Select TFTP/FTP:')
  select_transfer_label.grid(row=7, column=0, padx=10, pady=3, sticky=tk.W)
  select_transfer_var = tk.StringVar()
  select_transfer_dropdown = ttk.Combobox(single_frame, textvariable=select_transfer_var, values=['tftp', 'ftp'])
  select_transfer_dropdown.grid(row=7, column=1, pady=3)

  tftp_label = ttk.Label(single_frame, text='TFTP/FTP Server IP:')
  tftp_label.grid(row=8, column=0, padx=10, pady=3, sticky=tk.W)
  tftp_entry = ttk.Entry(single_frame, width=23)
  tftp_entry.grid(row=8, column=1, pady=3)

  add_ver = ttk.Button(single_frame, text='Add Version to existing', command=add_new_version)
  add_ver.grid(row=9, column=0,padx=(0,295),pady=2)

  delete_ver = ttk.Button(single_frame, text='Delete Existing version', command=delete_version)
  delete_ver.grid(row=10, column=0,padx=(0,298),pady=2)

  add_device = ttk.Button(single_frame, text='Add Device', command=add_new_device)
  add_device.grid(row=9, column=0, pady=2)

  delete_device = ttk.Button(single_frame, text='Delete Device', command=delete_switch_type)
  delete_device.grid(row=10, column=0, pady=2)
  
  delete_device = ttk.Button(single_frame, text='Show Device List', command=show_update_db_popup)
  delete_device.grid(row=11, column=0,padx=(0,330),pady=2)

  # Start button execute firmware up
  start_button = ttk.Button(single_frame, text='Start SSH', command=start_ssh)
  start_button.grid(row=12, column=0,padx=(0,350), pady=2)

  output_frame = tk.Frame(single_frame)
  output_frame.grid(row=13, column=0,columnspan=2, padx=10, pady=5)

  # Create a scrollbar for the version_text
  output_scrollbar = tk.Scrollbar(output_frame, orient="vertical")
  output_scrollbar.pack(side="right", fill="y")

  # Create the version_text widget
  output_text = tk.Text(output_frame, height=18, width=70, yscrollcommand=output_scrollbar.set)
  output_text.pack(side="left", fill="both", expand=True)
  output_scrollbar.config(command=output_text.yview)

  fetch_available_switch_types()

  single_frame.pack()
