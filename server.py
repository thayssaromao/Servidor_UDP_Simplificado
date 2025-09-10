import socket

# Cria o socket UDP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Associa o socket ao IP local e porta 12345
server_socket.bind(("localhost", 12345))

print("Servidor UDP esperando mensagens...")

while True:
    data, addr = server_socket.recvfrom(1024)  # recebe até 1024 bytes
    print(f"Mensagem recebida de {addr}: {data.decode()}")
