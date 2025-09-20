import socket
import time
from utils import FileChecker, dividir_arquivo
from protocol import (
    interpretar_mensagem,
    construir_mensagem,
    MSG_ARQUIVO_NAO_ENCONTRADO,
    CMD_SEGMENT,
    CMD_OK,
    CMD_RETRANSMIT,
    DELIMITADOR
)

# Configuração do servidor
HOST = "localhost"
PORT = 12345
TAMANHO_PAYLOAD = 1400

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))
print("Servidor UDP esperando mensagens...")

clientes_ativos = {}

while True:
    data, addr = server_socket.recvfrom(2048)
    message = data.decode()
    print(f"Mensagem recebida de {addr}: {message}")

    comando, args = interpretar_mensagem(message)

    if comando == "GET":
        nome_arquivo = args[0]
        checker = FileChecker(nome_arquivo)

        if checker.file_exists():
            tamanho = checker.file_size_mb()
            if tamanho < 1:
                resposta = construir_mensagem("ERR", "Arquivo encontrado, mas menor que 1MB")
                server_socket.sendto(resposta.encode(), addr)
                print(f"Enviando resposta para {addr}: {resposta}")
                continue

            segmentos = dividir_arquivo(nome_arquivo, TAMANHO_PAYLOAD)
            buffer_envio = {i: segmento for i, segmento in enumerate(segmentos)}
            clientes_ativos[addr] = buffer_envio

            resposta = construir_mensagem(CMD_OK, len(buffer_envio))
            server_socket.sendto(resposta.encode(), addr)
            print(f"Enviando resposta para {addr}: {resposta}")
            print(f"Arquivo '{nome_arquivo}' dividido em {len(buffer_envio)} segmentos. Iniciando envio...")

            for seq_num, segmento_dados in sorted(buffer_envio.items()):
                header = construir_mensagem(CMD_SEGMENT, seq_num)
                pacote_completo = header.encode() + DELIMITADOR.encode() + segmento_dados
                server_socket.sendto(pacote_completo, addr)
                if seq_num % 1000 == 0:
                    print(f" -> Enviado segmento {seq_num}")
                time.sleep(0.001)

            print(f"Transmissão inicial para {addr} concluída.")

        else:
            server_socket.sendto(MSG_ARQUIVO_NAO_ENCONTRADO.encode(), addr)
            print(f"Arquivo '{nome_arquivo}' não encontrado. Enviado para {addr}")

    elif comando == CMD_RETRANSMIT:
        buffer_envio_cliente = clientes_ativos.get(addr)
        if not buffer_envio_cliente:
            print(f"Aviso: pedido RETX de cliente desconhecido {addr}. Ignorando.")
            continue

        try:
            numeros_seq_str = args[0].split(",")
            numeros_seq_para_reenviar = [int(s) for s in numeros_seq_str]
        except Exception:
            print(f"Erro: RETX mal formatado de {addr}. Ignorado")
            continue

        for seq_num in numeros_seq_para_reenviar:
            if seq_num in buffer_envio_cliente:
                segmento = buffer_envio_cliente[seq_num]
                pacote = construir_mensagem(CMD_SEGMENT, seq_num).encode() + DELIMITADOR.encode() + segmento
                server_socket.sendto(pacote, addr)
                #print(f" -> Reenviado segmento {seq_num} para {addr}")
            else:
                print(f"Aviso: segmento {seq_num} não está no buffer de {addr}")

    else:
        server_socket.sendto("ERR|Comando inválido".encode(), addr)
