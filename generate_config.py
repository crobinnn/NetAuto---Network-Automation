import tkinter as tk
from tkinter import ttk,filedialog
import os
import re
import csv

def generate_config_gui(gen_frame):
  
  # Variables to store file paths
  template_file_path = ""
  csv_file_path = ""
  output_dir_path = ""

  def select_template_file():
    nonlocal template_file_path
    template_file_path = filedialog.askopenfilename(title="Select Template File", filetypes=[("Text files", "*.txt")])
    if template_file_path:
      template_label.config(text=f"Template File: {os.path.basename(template_file_path)}")

  def select_csv_file():
    nonlocal csv_file_path
    csv_file_path = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV files", "*.csv")])
    if csv_file_path:
      csv_label.config(text=f"CSV File: {os.path.basename(csv_file_path)}")

  def select_output_directory():
    nonlocal output_dir_path
    output_dir_path = filedialog.askdirectory(title="Select Output Directory")
    if output_dir_path:
      output_dir_label.config(text=f"Output Directory: {output_dir_path}")

  def generate_config():
    if template_file_path and csv_file_path and output_dir_path:
      if validate_parameters(template_file_path, csv_file_path):
        generate_config_files(template_file_path, csv_file_path, output_dir_path)
        tk.messagebox.showinfo("Success", "Configurations generated successfully!")
    else:
      tk.messagebox.showerror("Error", "Please select all files and directories.")

  def validate_parameters(template_file, csv_file):
    with open(template_file, 'r') as f:
        template = f.read()

    # Extract keys from template
    keys_with_braces = re.findall(r'{(.*?)}', template)

    with open(csv_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        csv_headers = reader.fieldnames

        # Find missing keys in CSV
        missing_in_csv = [key for key in keys_with_braces if key not in csv_headers]
        # Find missing keys in Template
        missing_in_template = [key for key in csv_headers if key not in keys_with_braces]

        if missing_in_csv or missing_in_template:
            error_message = "Parameter mismatch found:\n"
            if missing_in_csv:
                error_message += f"Missing in CSV: {', '.join(missing_in_csv)}\n"
            if missing_in_template:
                error_message += f"Missing in Template: {', '.join(missing_in_template)}\n"
            tk.messagebox.showerror("Parameter Mismatch", error_message)
            return False

    return True

  def generate_config_files(template_file, csv_file, output_dir):
    with open(template_file, 'r') as f:
      template = f.read()

    # Extract keys from template
    keys_with_braces = re.findall(r'{(.*?)}', template)

    with open(csv_file, 'r') as csvfile:
      reader = csv.DictReader(csvfile)
      for row in reader:
        config = template  # Start with the original template

        # Replace placeholders with values from CSV row
        for key_with_braces in keys_with_braces:
          placeholder = f'{{{key_with_braces}}}'
          key = key_with_braces  # Do not strip braces this time
          if key in row:
            value = row[key].strip('"')  # Remove double quotes
            config = config.replace(placeholder, value)

        # Remove braces from generated config (outside the loop)
        config = config.replace('{', '').replace('}', '')

        output_file_path = os.path.join(output_dir, f"{row['hostname']}_config.txt")
        with open(output_file_path, 'w') as outfile:
          outfile.write(config)

  # GUI Elements
  template_label = ttk.Label(gen_frame, text="Template File: Not Selected")
  template_label.grid(row=0, column=0, padx=10, pady=5)

  csv_label = ttk.Label(gen_frame, text="CSV File: Not Selected")
  csv_label.grid(row=1, column=0, padx=10, pady=5)

  output_dir_label = ttk.Label(gen_frame, text="Output Directory: Not Selected")
  output_dir_label.grid(row=2, column=0, padx=10, pady=5)

  select_template_button = ttk.Button(gen_frame, text="Select Template File", command=select_template_file)
  select_template_button.grid(row=0, column=1, padx=10, pady=5)

  select_csv_button = ttk.Button(gen_frame, text="Select CSV File", command=select_csv_file)
  select_csv_button.grid(row=1, column=1, padx=10, pady=5)

  select_output_button = ttk.Button(gen_frame, text="Select Output Directory", command=select_output_directory)
  select_output_button.grid(row=2, column=1, padx=10, pady=5)

  generate_button = ttk.Button(gen_frame, text="Generate Configurations", command=generate_config)
  generate_button.grid(row=3, columnspan=2, padx=10, pady=10)

