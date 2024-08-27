import paramiko
from ping3 import ping
import time
import json

def get_ssh_connection(host, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=username, password=password)
    except paramiko.AuthenticationException:
        print("Error! Invalid credentials.")
        return None
    except paramiko.SSHException as sshException:
        print(f"Error! Unable to establish SSH connection: {sshException}")
        return None
    except Exception as e:
        print(f"Error! Exception in connecting to the server: {str(e)}")
        return None
    return ssh

def get_system_stats(ssh):
    commands = {
        'IP Address': "hostname -I | awk '{print $1}'",
        'OS Name': "cat /etc/os-release | grep PRETTY_NAME | cut -d '\"' -f2",
        'Hostname': "hostname",
        'CPU Usage': "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'",
        'Memory Usage': "free -m | awk 'NR==2{printf \"%.2f\", $3*100/$2 }'",
        'Disk Usage': "df -h | awk '$NF==\"/\"{printf \"%s\", $5}'",
        'Uptime': "uptime -p"
    }

    stats = {}
    for key, command in commands.items():
        try:
            stdin, stdout, stderr = ssh.exec_command(command)
            stats[key] = stdout.read().decode().strip()
        except Exception as e:
            print(f"Error executing command '{command}': {str(e)}")
            stats[key] = "N/A"

    return stats

def save_credentials(file_path, host, username, password):
    credentials = {
        'host': host,
        'username': username,
        'password': password
    }
    with open(file_path, 'w') as file:
        json.dump(credentials, file)

def load_credentials(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def main():
    credentials_file = 'credentials.json'

    # If the credentials file doesn't exist, ask for credentials and save them
    try:
        credentials = load_credentials(credentials_file)
        host = credentials['host']
        username = credentials['username']
        password = credentials['password']
    except FileNotFoundError:
        host = input("SSH Host: ")
        username = input("Username: ")
        password = input("Password: ")
        save_credentials(credentials_file, host, username, password)

    log_file = f"system_stats_{host.replace('.', '_')}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    
    ssh = get_ssh_connection(host, username, password)
    if ssh is None:
        return

    stats = get_system_stats(ssh)
    ssh.close()

    # Ping operation
    try:
        ping_time = ping(host)
        if ping_time is None:
            ping_output = "Ping delay: Ping request failed."
        else:
            ping_output = f"Ping delay: {ping_time * 1000:.2f} ms"
    except Exception as e:
        ping_output = f"Ping delay: An error occurred - {str(e)}"

    with open(log_file, 'w') as file:
        for key, value in stats.items():
            output = f"{key}: {value}"
            print(output)
            file.write(output + '\n')
        
        print(ping_output)
        file.write(ping_output + '\n')

    print(f"Saved to log file: {log_file}")

if __name__ == "__main__":
    main()
