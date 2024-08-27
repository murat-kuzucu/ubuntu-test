import os
import json
import paramiko

# SSH credentials file path
credentials_file = "credentials.json"

# Load or create SSH credentials
if not os.path.exists(credentials_file):
    credentials = {
        "host": input("SSH Host: "),
        "username": input("SSH Username: "),
        "password": input("SSH Password: ")
    }
    with open(credentials_file, 'w') as file:
        json.dump(credentials, file)
else:
    with open(credentials_file, 'r') as file:
        credentials = json.load(file)

# GoAccess command to generate HTML file on the remote server
log_file = "/var/log/nginx/access.log"
output_file = "/tmp/nginx_report.html"
goaccess_command = f"goaccess {log_file} -o {output_file} --log-format=COMBINED"
delete_command = f"rm -f {output_file}"

try:
    # Connect to the server
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=credentials["host"], username=credentials["username"], password=credentials["password"])
    print("SSH connection established.")

    # Delete the existing HTML file if it exists
    stdin, stdout, stderr = ssh.exec_command(delete_command)
    delete_err = stderr.read().decode().strip()
    if delete_err:
        print(f"Error deleting existing file: {delete_err}")
    else:
        print("Existing HTML file deleted (if any).")

    # Execute the GoAccess command to generate a new HTML file
    stdin, stdout, stderr = ssh.exec_command(goaccess_command)
    goaccess_stdout = stdout.read().decode().strip()
    print("GoAccess command executed successfully.")
    print(f"GoAccess output: {goaccess_stdout}")

    # Download the generated HTML file
    try:
        sftp = ssh.open_sftp()
        sftp.get(output_file, os.path.basename(output_file))
        print("HTML file successfully downloaded.")
    except FileNotFoundError as fnf_error:
        print(f"File not found on the server: {output_file}")
    except Exception as e:
        print(f"Error during SFTP operation: {e}")
    finally:
        if 'sftp' in locals():
            sftp.close()

except paramiko.SSHException as e:
    print(f"SSH error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    if 'ssh' in locals():
        ssh.close()
        print("SSH session closed.")
