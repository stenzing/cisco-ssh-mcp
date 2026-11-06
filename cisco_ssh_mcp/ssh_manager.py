import paramiko

class SSHSessionManager:
    def __init__(self):
        self.sessions: dict[str, paramiko.SSHClient] = {}

    def connect(self, host: str, username: str, password: str, connection_id: str) -> str:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=host,
                port=22,
                username=username,
                password=password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            self.sessions[connection_id] = client
            return f"Successfully connected to {host} under session ID '{connection_id}'."
        except Exception as e:
            return f"Connection error: {str(e)}"

    def execute(self, connection_id: str, command: str) -> str:
        client = self.sessions.get(connection_id)
        if not client:
            return f"Error: No active session found for ID '{connection_id}'."
        
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=15)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            result = output if output else ""
            if error:
                result += f"\nStderr:\n{error}"
                
            return result if result.strip() else "Command executed with no output."
        except Exception as e:
            return f"Execution error: {str(e)}"

ssh_manager = SSHSessionManager()