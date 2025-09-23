import socket
import threading
import time
import zlib
from utils import FileChecker, FileSegmenter
from protocol import (
    CMD_GET_FILE,
    interpretar_mensagem,
    construir_mensagem,
    MSG_ARQUIVO_NAO_ENCONTRADO,
    CMD_SEGMENT,
    CMD_OK,
    CMD_RETRANSMIT,
    CMD_BYE,
    CMD_HELLO,
    CMD_END
)

# Configuração do servidor
HOST = "localhost"
PORT = 12345
TAMANHO_PAYLOAD = 1400
SEPARADOR = b'|||'  # Separador seguro entre header e payload

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))
print("Servidor UDP esperando mensagens...\n")

clientes_ativos = {}

def enviar_arquivo_para_cliente(addr, nome_arquivo):
    checker = FileChecker(nome_arquivo)

    if not checker.file_exists():
        server_socket.sendto(MSG_ARQUIVO_NAO_ENCONTRADO.encode(), addr)
        print(f"Arquivo '{nome_arquivo}' não encontrado. Enviado para {addr}")
        return

    tamanho = checker.file_size_mb()
    if tamanho < 1:
        resposta = construir_mensagem("ERR", "Arquivo encontrado, mas menor que 1MB")
        server_socket.sendto(resposta.encode(), addr)
        print(f"Enviando resposta para {addr}: {resposta}")
        return

    segmentos = FileSegmenter.dividir_arquivo(nome_arquivo, TAMANHO_PAYLOAD)
    buffer_envio = {i: segmento for i, segmento in enumerate(segmentos)}
    clientes_ativos[addr] = buffer_envio

    # Confirmação inicial
    resposta = construir_mensagem(CMD_OK, len(buffer_envio))
    server_socket.sendto(resposta.encode(), addr)
    print(f"Enviando resposta para {addr}: {resposta}")

    # Envio inicial
    for seq_num, segmento_dados in sorted(buffer_envio.items()):
        checksum = zlib.adler32(segmento_dados)
        header = f"{CMD_SEGMENT}|{seq_num}|{checksum}".encode() + SEPARADOR
        pacote_completo = header + segmento_dados
        server_socket.sendto(pacote_completo, addr)
        time.sleep(0.001)

    # Sinal de fim
    resposta_fim = construir_mensagem(CMD_END, "Transmissão concluída")
    server_socket.sendto(resposta_fim.encode(), addr)
    print(f"Sinal de fim enviado para {addr}")


while True:
    data, addr = server_socket.recvfrom(65536)
    message = data.decode(errors="ignore")
    print(f"Mensagem recebida de {addr}: {message}")

    comando, args = interpretar_mensagem(message)

    if comando == CMD_HELLO:
        resposta = construir_mensagem(CMD_OK, "Servidor pronto")
        server_socket.sendto(resposta.encode(), addr)
        print(f"Enviando resposta para {addr}: {resposta}\n")
    elif comando == CMD_GET_FILE:
        nome_arquivo = args[0]
        # Cria uma thread para enviar o arquivo
        thread_envio = threading.Thread(target=enviar_arquivo_para_cliente, args=(addr, nome_arquivo))
        thread_envio.start()

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
                checksum = zlib.adler32(segmento)
                pacote = f"{CMD_SEGMENT}|{seq_num}|{checksum}".encode() + SEPARADOR + segmento
                server_socket.sendto(pacote, addr)
            else:
                print(f"Aviso: segmento {seq_num} não está no buffer de {addr}")
    elif comando == CMD_BYE:
        if addr in clientes_ativos:
            del clientes_ativos[addr]
            print(f"Sessão de {addr} encerrada e recursos liberados.")
        else:
            print(f"Aviso: BYE recebido de {addr} sem sessão ativa.")
    else:
        server_socket.sendto("ERR|Comando inválido".encode(), addr)



