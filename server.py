import socket
import time
from utils import FileChecker
from protocol import (
    interpretar_mensagem,
    construir_mensagem,
    MSG_CONEXAO_OK,
    MSG_ARQUIVO_NAO_ENCONTRADO,
    CMD_SEGMENT,
    DELIMITADOR,
)

# Cria o socket UDP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Associa o socket ao IP local e porta 12345
server_socket.bind(("localhost", 12345))

clientes_ativos = {}

print("\nServidor UDP esperando mensagens...")

while True:
    data, addr = server_socket.recvfrom(1024)  # recebe até 1024 bytes
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
            else:
                print(f"Arquivo '{nome_arquivo}' encontrado. Segmentando para envio para {addr}.")

                TAMANHO_PAYLOAD = 1400
                segmentos = checker.dividir_arquivo(nome_arquivo, TAMANHO_PAYLOAD)

                buffer_envio = {i: segmento for i, segmento in enumerate(segmentos)}
                print(f"Arquivo dividido em {len(buffer_envio)} segmentos.")

                clientes_ativos[addr] = buffer_envio

                resposta = construir_mensagem("OK", f"Arquivo pronto. Total de segmentos: {len(buffer_envio)}")
                server_socket.sendto(resposta.encode(), addr)

                for seq_num, segmento_dados in sorted(buffer_envio.items()):
                    header = construir_mensagem(CMD_SEGMENT, seq_num)
                    pacote_completo = header.encode() + DELIMITADOR.encode() + segmento_dados

                    server_socket.sendto(pacote_completo, addr)  # enviando pacote
                    print(f" -> Enviado segmento {seq_num}")

                    time.sleep(0.001)  # Pausa por 1 milissegundo entre os envios

                print(f"Transmissão inicial para {addr} concluída.")

        else:
            server_socket.sendto(MSG_ARQUIVO_NAO_ENCONTRADO.encode(), addr)

    elif comando == "RETX":  # caso seja a mensagem de retransmissão
        print(f"Recebido pedido de retransmissão de {addr}.")

        buffer_envio_cliente = clientes_ativos.get(addr)  # localiza o buffer de envio do cliente

        if not buffer_envio_cliente:
            print(f"Aviso: Pedido de RETX de um cliente desconhecido ou inativo {addr}. Ignorando.")
            continue

        # decodificando os números de sequência
        try:
            numeros_seq_str = args[0].split(",")
            numeros_seq_para_reenviar = [int(s) for s in numeros_seq_str]
        except (ValueError, IndexError):
            print(f"Erro: Pedido de RETX mal formatado de {addr}. Ignorado.")
            continue

        # reenviando os segmentos solicitados
        for seq_num in numeros_seq_para_reenviar:
            if seq_num in buffer_envio_cliente:
                segmento_para_reenviar = buffer_envio_cliente[seq_num]
                print(f"Reenviando segmento {seq_num} para {addr}.")

                pacote_a_reenviar = (
                    construir_mensagem(CMD_SEGMENT, seq_num).encode()
                    + DELIMITADOR.encode()
                    + segmento_para_reenviar
                )
                server_socket.sendto(pacote_a_reenviar, addr)
            else:
                print(f"Aviso: Cliente {addr} pediu segmento {seq_num} que não está no buffer.")

    else:
        server_socket.sendto("ERR|Comando inválido".encode(), addr)
