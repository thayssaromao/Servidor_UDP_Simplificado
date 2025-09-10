import socket

# Cria o socket UDP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Mensagem que será enviada
message = "Hello World via UDP!"

# Envia para o servidor (localhost:12345)
client_socket.sendto(message.encode(), ("localhost", 12345))

print("Mensagem enviada!")
