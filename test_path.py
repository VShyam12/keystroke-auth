import os
file_path = os.path.abspath(__file__)
config_file = 'backend/config.py'
base_dir = os.path.abspath(os.path.join(os.path.dirname(config_file), '..'))
db_path = os.path.join(base_dir, 'instance', 'keystroke_auth.db')
print(f"config file: {file_path}")
print(f"base_dir: {base_dir}")
print(f"db_path: {db_path}")