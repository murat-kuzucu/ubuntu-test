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

# Connect to the server and run the commands
try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=credentials["host"], username=credentials["username"], password=credentials["password"])
    print("SSH connection established.")

    # Delete the existing HTML file if it exists
    stdin, stdout, stderr = ssh.exec_command(delete_command)
    delete_err = stderr.read().decode()
    if delete_err:
        print("Error deleting existing file:", delete_err)
    else:
        print("Existing HTML file deleted (if any).")

    # Execute the GoAccess command to generate a new HTML file
    stdin, stdout, stderr = ssh.exec_command(goaccess_command)
    goaccess_stdout = stdout.read().decode()
    goaccess_err = stderr.read().decode()
    if goaccess_err:
        print("Error executing GoAccess command:", goaccess_err)
    else:
        print("GoAccess command executed successfully.")
        print("GoAccess output:", goaccess_stdout)

    # Download the generated HTML file
    sftp = ssh.open_sftp()
    sftp.get(output_file, os.path.basename(output_file))
    sftp.close()
    print("HTML file successfully downloaded.")

except paramiko.SSHException as e:
    print(f"SSH error: {e}")
    exit(1)
except FileNotFoundError:
    print(f"File not found: {output_file}")
    exit(1)
finally:
    ssh.close()
    print("SSH session closed.")
