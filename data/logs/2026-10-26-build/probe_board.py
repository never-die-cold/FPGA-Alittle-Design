import paramiko, sys
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    c.connect("192.168.50.99", username="xilinx", password="xilinx", timeout=8, banner_timeout=8, auth_timeout=8, allow_agent=False, look_for_keys=False)
    stdin, stdout, stderr = c.exec_command("uptime; ip -4 addr show eth0 | grep inet; dmesg | grep -c 'mmc0: Timeout'", timeout=15)
    print("SSH_OK")
    print(stdout.read().decode(errors="replace"))
    print(stderr.read().decode(errors="replace"))
    print("rc", stdout.channel.recv_exit_status())
except Exception as e:
    print("SSH_FAIL", repr(e))
finally:
    try: c.close()
    except Exception: pass
