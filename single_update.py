import tkinter as tk
import db_connection as couch
import couchdb
import threading
import time
import difflib
import re
from netmiko import ConnectHandler
from tkinter import ttk,simpledialog,messagebox

def create_single_gui(single_frame):

  def decide_protocol(event=None):
    global protocol
    protocol = select_transfer_var.get()

  def fetch_available_switch_types(event=None):
    if not couch.db_connection:
        output_text.insert(tk.END, "Cannot access database. Not connected.\n")
        return
      
    try:
      all_docs = couch.db.view('_all_docs')
      switch_types = [row.id for row in all_docs]
      switch_type_dropdown['values'] = switch_types
    except couchdb.http.ResourceNotFound:
      output_text.insert(tk.END,"Database not found")

  def fetch_versions(event=None):
    version_var.set("")
    global switch_type
    switch_type = switch_type_var.get()
    if not couch.db_connection:
        output_text.insert(tk.END, "Cannot access database. Not connected.\n")
        return
    try:
      data = couch.db[switch_type]
      versions = [version["name"] for version in data["versions"]]
      version_dropdown.config(values=versions)
      version_dropdown.config(state="readonly")
    except couchdb.http.ResourceNotFound:
      output_text.insert(tk.END,"Document not found in CouchDB")
  
  def retrieve_data(event=None):
    global version_name, hash_value, firmware, size, path
    version_name = version_var.get()
    if not couch.db_connection:
        output_text.insert(tk.END, "Cannot access database. Not connected.\n")
        return
    try:
      data = couch.db[switch_type]
      for version in data["versions"]:
        if version["name"] == version_name:
          hash_value = version["hash"]
          firmware = version["firmware"]
          size = version["size"]
          path = version["path"]
          output_text.delete('1.0', tk.END)
          output_text.insert(tk.END,f"Hash: {hash_value}\nFirmware: {firmware}\nSize: {size}\nPath: {path}")
          # You can assign these values to variables if needed
          break
    except couchdb.http.ResourceNotFound:
      output_text.insert(tk.END,"Document not found in CouchDB")
  
  def add_new_device(event=None):
    output_text.delete('1.0', tk.END)
    global switch_type, version_name, hash_value, firmware, size, path
    if not couch.db_connection:
        output_text.insert(tk.END, "Cannot access database. Not connected.\n")
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
        "_id": switch_type,
        "versions": [{
          "name": version_name,
          "firmware": firmware,
          "hash": hash_value,
          "size": size,
          "path": path
        }]
      }
      couch.db.save(new_document)
      output_text.insert(tk.END,"New device added to the database.")
      fetch_available_switch_types()
      new_window.destroy()

    add_button = tk.Button(new_window, text="Add Device", command=add_device)
    add_button.grid(row=6, column=0, columnspan=2)

  def add_new_version(event=None):
    output_text.delete('1.0', tk.END)
    global switch_type
    if not couch.db_connection:
        output_text.insert(tk.END, "Cannot access database. Not connected.\n")
        return
    new_window = tk.Toplevel(single_frame)
    new_window.title("Add New Version")

    switch_type_label = tk.Label(new_window, text="Select Switch Type:")
    switch_type_label.grid(row=0, column=0)

    switch_type_var = tk.StringVar()
    switch_type_dropdown = ttk.Combobox(new_window, textvariable=switch_type_var, state="readonly")
    switch_type_dropdown.grid(row=0, column=1)

    # Fetch available switch types from the database
    try:
      all_docs = couch.db.view('_all_docs')
      switch_types = [row.id for row in all_docs]
      switch_type_dropdown['values'] = switch_types
    except couchdb.http.ResourceNotFound:
      output_text.insert(tk.END,"Database not found")

    def add_version():
      selected_switch_type = switch_type_var.get()
      if selected_switch_type:
        new_version_name = version_name_entry.get()
        new_firmware = firmware_entry.get()
        new_hash = hash_entry.get()
        new_size = size_entry.get()
        new_path = path_entry.get()

        # Update existing document with new version
        try:
          existing_doc = couch.db[selected_switch_type]
          existing_doc["versions"].append({
            "name": new_version_name,
            "firmware": new_firmware,
            "hash": new_hash,
            "size": new_size,
            "path": new_path
          })
          couch.db.save(existing_doc)
          output_text.insert(tk.END,"New version added to the existing document.")
          version_var.set("")
          fetch_versions()
          new_window.destroy()
        except couchdb.http.ResourceNotFound:
          output_text.insert(tk.END,"Document not found in CouchDB")
      else:
        output_text.insert(tk.END,"Please select a switch type first.")

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
  
  def delete_switch_type(event=None):
    output_text.delete('1.0', tk.END)
    switch_type = switch_type_var.get()
    if not couch.db_connection:
        output_text.insert(tk.END, "Cannot access database. Not connected.\n")
        return
    if switch_type:
      confirm = simpledialog.askstring("Confirmation", f"Are you sure you want to delete {switch_type}? (yes/no)")
      if confirm and confirm.lower() == "yes":
        try:
          del couch.db[switch_type]
          output_text.insert(tk.END, f"Switch type '{switch_type}' deleted from the database.")
          version_var.set("")
          switch_type_var.set("")
          fetch_available_switch_types()
          fetch_versions()
        except couchdb.http.ResourceNotFound:
          output_text.insert(tk.END, f"Switch type '{switch_type}' not found in CouchDB.")
    else:
      output_text.insert(tk.END,"Please select switch type to delete.")

  def delete_version(event=None):
    output_text.delete('1.0', tk.END)
    switch_type = switch_type_var.get()
    version_name = version_var.get()
    if switch_type and version_name:
      confirm = simpledialog.askstring("Confirmation", f"Are you sure you want to delete version '{version_name}' of {switch_type}? (yes/no)")
      if confirm and confirm.lower() == "yes":
        try:
          doc = couch.db[switch_type]
          versions = doc["versions"]
          for version in versions:
            if version["name"] == version_name:
              versions.remove(version)
              couch.db.save(doc)
              output_text.insert(tk.END,f"Version '{version_name}' deleted from the document '{switch_type}'.")
              version_var.set("")
              fetch_versions()  # Refresh version dropdown
              return
          output_text.insert(tk.END,f"Version '{version_name}' not found in the document '{switch_type}'.")
        except couchdb.http.ResourceNotFound:
          output_text.insert(tk.END,f"Document '{switch_type}' not found in CouchDB.")
    else:
      output_text.insert(tk.END,"Please select both switch type and version to delete.")

  def start_ssh():
    output_text.delete('1.0', tk.END)
    threading.Thread(target=cisco_ssh).start()

  def cisco_ssh():
    global output_part
    # Ambil data dr input field GUI
    host = ip_entry.get()
    username = username_entry.get()
    password = password_entry.get()
    tftp_server = tftp_entry.get()

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
        output_text.insert(tk.END,'Connecting to Cisco ' + switch_type +'\n') 
        output_text.update_idletasks() 
        output_text.insert(tk.END, str(size) + '\n')
        output_text.update_idletasks() 
        
        with ConnectHandler(**cisco_device) as net_connect:
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
          bytes_free_pattern = r'(\d+) bytes free'
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
                  # Capture the output incrementally
                  output_part = net_connect.read_channel()
                  
                  if output_part:
                    output_text.insert(tk.END, output_part)  
                    output_text.update_idletasks()
                    output_text.see(tk.END)
                  
                  if device_prompt in output_part:
                    break

                  # Sleep to avoid overwhelming the device with continuous reads
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

                    # Sleep to avoid overwhelming the device with continuous reads
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
                            # Check if there are differences
                            if any(confdiff):
                              # If differences exist, display the differing lines
                              output_text.insert(tk.END, 'Differences found in configuration:\n')
                              for line in confdiff:
                                output_text.insert(tk.END, line + '\n')
                            else:
                              # If no differences, display confirmation message
                              output_text.insert(tk.END, 'Configuration Verified!\n')
                            # Update the text box and ensure the last line is visible
                            output_text.update_idletasks()
                            output_text.see(tk.END)

                            output_text.insert(tk.END, 'Verifying Interface Status...\n')
                            output_text.update_idletasks() 
                            output_text.see(tk.END)

                            updateint = net_connect.send_command('show ip int br', read_timeout=300)
                            updateint_lines = updateint.strip().split('\n')
                            currentint_lines = currentint.strip().split('\n')
                            
                            intdiff = difflib.unified_diff(currentint_lines, updateint_lines)
                            # Check if there are differences
                            if any(intdiff):
                              # If differences exist, display the differing lines
                              output_text.insert(tk.END, 'Differences found in interfaces info:\n')
                              for line in intdiff:
                                output_text.insert(tk.END, line + '\n')
                            else:
                              # If no differences, display confirmation message
                              output_text.insert(tk.END, 'Interfaces Verified!\n')
                            
                            output_text.insert(tk.END, 'Verifying VLANs...\n')
                            output_text.update_idletasks() 
                            output_text.see(tk.END)

                            updatevlan = net_connect.send_command('show vlan', read_timeout=300)
                            updatevlan_lines = updatevlan.strip().split('\n')
                            currentvlan_lines = currentvlan.strip().split('\n')

                            vlandiff = difflib.unified_diff(updatevlan_lines, currentvlan_lines)

                            # Check if there are differences
                            if any(vlandiff):
                              # If differences exist, display the differing lines
                              output_text.insert(tk.END, 'Differences found in VLAN configuration:\n')
                              for line in vlandiff:
                                output_text.insert(tk.END, line + '\n')
                            else:
                              # If no differences, display confirmation message
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
                    # Continue to the beginning of the outer while loop for retry
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
          bytes_free_pattern = r'(\d+) bytes free'
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
                  # Capture the output incrementally
                  output_part = net_connect.read_channel()
                  
                  if output_part:
                    output_text.insert(tk.END, output_part)  
                    output_text.update_idletasks()
                    output_text.see(tk.END)
                  
                  if device_prompt in output_part:
                    break

                  # Sleep to avoid overwhelming the device with continuous reads
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

                    # Sleep to avoid overwhelming the device with continuous reads
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
                      # Capture the output incrementally
                      output_part = net_connect.read_channel()
                      if output_part:
                        output_text.insert(tk.END, output_part)  
                        output_text.update_idletasks()
                        output_text.see(tk.END)
              
                      if "[y/n]" in output_part:
                        output += net_connect.send_command_timing("y", strip_prompt=False, strip_command=False)

                      # Check for the expected prompt to know the command is complete
                      if device_prompt in output_part:
                        break

                      # Sleep to avoid overwhelming the device with continuous reads
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
                            # Check if there are differences
                            if any(confdiff):
                              # If differences exist, display the differing lines
                              output_text.insert(tk.END, 'Differences found in configuration:\n')
                              for line in confdiff:
                                output_text.insert(tk.END, line + '\n')
                            else:
                              # If no differences, display confirmation message
                              output_text.insert(tk.END, 'Configuration Verified!\n')
                            # Update the text box and ensure the last line is visible
                            output_text.update_idletasks()
                            output_text.see(tk.END)

                            output_text.insert(tk.END, 'Verifying Interface Status...\n')
                            output_text.update_idletasks() 
                            output_text.see(tk.END)

                            updateint = net_connect.send_command('show ip int br', read_timeout=300)
                            updateint_lines = updateint.strip().split('\n')
                            currentint_lines = currentint.strip().split('\n')
                            
                            intdiff = difflib.unified_diff(currentint_lines, updateint_lines)
                            # Check if there are differences
                            if any(intdiff):
                              # If differences exist, display the differing lines
                              output_text.insert(tk.END, 'Differences found in interfaces info:\n')
                              for line in intdiff:
                                output_text.insert(tk.END, line + '\n')
                            else:
                              # If no differences, display confirmation message
                              output_text.insert(tk.END, 'Interfaces Verified!\n')
                            
                            output_text.insert(tk.END, 'Verifying VLANs...\n')
                            output_text.update_idletasks() 
                            output_text.see(tk.END)

                            updatevlan = net_connect.send_command('show vlan', read_timeout=300)
                            updatevlan_lines = updatevlan.strip().split('\n')
                            currentvlan_lines = currentvlan.strip().split('\n')

                            vlandiff = difflib.unified_diff(updatevlan_lines, currentvlan_lines)

                            # Check if there are differences
                            if any(vlandiff):
                              # If differences exist, display the differing lines
                              output_text.insert(tk.END, 'Differences found in VLAN configuration:\n')
                              for line in vlandiff:
                                output_text.insert(tk.END, line + '\n')
                            else:
                              # If no differences, display confirmation message
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
                    # Continue to the beginning of the outer while loop for retry
                    continue

            elif free_bytes < size:
              output_text.insert(tk.END, 'Flash is not enough for upgrade, deleting inactive installation files')
              output_text.update_idletasks()
              output = net_connect.send_command('install remove inactive',expect_string='install_remove:')
              output_text.insert(tk.END, output + '\n')
              output_text.update_idletasks()
              output_text.see(tk.END)

              while True:
                # Capture the output incrementally
                output_part = net_connect.read_channel()
                if output_part:
                  output_text.insert(tk.END, output_part)  
                  output_text.update_idletasks()
                  output_text.see(tk.END)  
                
                # This part handles the real-time printing of ongoing process like !!!!
                if '[y/n]' in output_part:
                  output += net_connect.send_command_timing("y")
                    
                # Check for the expected prompt to know the command is complete
                if device_prompt in output_part:
                  break

                # Sleep to avoid overwhelming the device with continuous reads
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
  switch_type_dropdown.grid(row=1, column=1, padx=(120,0), pady=3)
  switch_type_dropdown.bind('<<ComboboxSelected>>', fetch_versions)

  # OS Selection dropdown menu
  version_label = ttk.Label(single_frame, text='Select Version:')
  version_label.grid(row=2, column=0, padx=10, pady=3, sticky=tk.W)
  version_var = tk.StringVar()
  version_dropdown = ttk.Combobox(single_frame, textvariable=version_var,state='disabled')
  version_dropdown.grid(row=2, column=1, padx=(120,0), pady=3)
  version_dropdown.bind('<<ComboboxSelected>>', retrieve_data)

  # input field buat IP, user, pass, server tftp
  ip_label = ttk.Label(single_frame, text='Device IP:')
  ip_label.grid(row=3, column=0, padx=10, pady=3, sticky=tk.W)
  ip_entry = ttk.Entry(single_frame, width=23)
  ip_entry.grid(row=3, column=1, padx=(120,0), pady=3)

  username_label = ttk.Label(single_frame, text='Username:')
  username_label.grid(row=4, column=0, padx=10, pady=3, sticky=tk.W)
  username_entry = ttk.Entry(single_frame, width=23)
  username_entry.grid(row=4, column=1, padx=(120,0), pady=3)

  password_label = ttk.Label(single_frame, text='Password:')
  password_label.grid(row=5, column=0, padx=10, pady=3, sticky=tk.W)
  password_entry = ttk.Entry(single_frame, show='*', width=23)
  password_entry.grid(row=5, column=1, padx=(120,0), pady=3)

  select_transfer_label = ttk.Label(single_frame, text='Select TFTP/FTP:')
  select_transfer_label.grid(row=6, column=0, padx=10, pady=3, sticky=tk.W)
  select_transfer_var = tk.StringVar()
  select_transfer_dropdown = ttk.Combobox(single_frame, textvariable=select_transfer_var, values=['tftp', 'ftp'])
  select_transfer_dropdown.grid(row=6, column=1, padx=(120,0), pady=3)
  select_transfer_dropdown.bind('<<ComboboxSelected>>', decide_protocol)

  tftp_label = ttk.Label(single_frame, text='TFTP/FTP Server IP:')
  tftp_label.grid(row=7, column=0, padx=10, pady=3, sticky=tk.W)
  tftp_entry = ttk.Entry(single_frame, width=23)
  tftp_entry.grid(row=7, column=1, padx=(120,0), pady=3)

  add_ver = ttk.Button(single_frame, text='Add Version to existing', command=add_new_version)
  add_ver.grid(row=8, column=0, padx=(0,242), pady=2)

  delete_ver = ttk.Button(single_frame, text='Delete Existing version', command=delete_version)
  delete_ver.grid(row=9, column=0, padx=(0,247),pady=2)

  add_device = ttk.Button(single_frame, text='Add Device', command=add_new_device)
  add_device.grid(row=10, column=0, padx=(0,300), pady=2)

  delete_device = ttk.Button(single_frame, text='Delete Device', command=delete_switch_type)
  delete_device.grid(row=11, column=0, padx=(0,295), pady=2)

  # Start button execute firmware up
  start_button = ttk.Button(single_frame, text='Start SSH', command=start_ssh)
  start_button.grid(row=12, column=0, padx=(0,300),pady=2)

  output_frame = tk.Frame(single_frame)
  output_frame.grid(row=13, column=0,columnspan=2, padx=10, pady=5)

  # Create a scrollbar for the version_text
  output_scrollbar = tk.Scrollbar(output_frame, orient="vertical")
  output_scrollbar.pack(side="right", fill="y")

  # Create the version_text widget
  output_text = tk.Text(output_frame, height=18, width=80, yscrollcommand=output_scrollbar.set)
  output_text.pack(side="left", fill="both", expand=True)
  output_scrollbar.config(command=output_text.yview)

  fetch_available_switch_types()

  single_frame.pack()
