import socket
HOST = '127.0.0.1' #ENDEREÇO DO SERVIDOR
PORT = 12345 # Porta usada pelo servidor
BUFFER_SIZE = 4096 #tam maximo de dados a serem recebidos
    
def requisitar_arquivo(nome_arquivo):
    

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #cria um cliente usando protocolo udp

    comand = f"GET /{nome_arquivo}"
    client.sendto(comand.encode(), (HOST, PORT)) # transforma o txt e, bytes e enviar pro servidor

    respost, _ = client.recvfrom(BUFFER_SIZE) #aguarda uma resposta do servidor
    print("Resposta do servidor:\n")
    print(respost.decode(errors="ignore"))#Imprime a resposta do servidor e decodifica


requisitar_arquivo("test.txt")
