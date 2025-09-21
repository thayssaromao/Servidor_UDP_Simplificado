import socket
from protocol import (
    interpretar_mensagem,
    construir_mensagem,
    construir_pedido_retransmissao,
    CMD_GET_FILE,
    CMD_OK,
    CMD_SEGMENT,
    CMD_HELLO,
    CMD_BYE
)
import time

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 65536
SEPARADOR = b'|||'  # mesmo separador usado no server

def requisitar_arquivo(nome_arquivo):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(5.0)

    # Passo 1: Esperar o servidor estar pronto
    print("Enviando HELLO para o servidor...")
    client.sendto(construir_mensagem(CMD_HELLO).encode(), (HOST, PORT))
    try:
        resposta, _ = client.recvfrom(BUFFER_SIZE)
        comando, _ = interpretar_mensagem(resposta.decode())
        if comando != CMD_HELLO:
            print("Resposta inesperada do servidor. Encerrando.")
            return
        print("Servidor respondeu com HELLO. Continuando...")
    except socket.timeout:
        print("Erro: O servidor não respondeu ao HELLO.")
        return
    
    # Passo 2: Enviar pedido 
    pedido_inicial = construir_mensagem(CMD_GET_FILE, nome_arquivo)
    print(f"Enviando pedido inicial para o servidor: {pedido_inicial}")
    client.sendto(pedido_inicial.encode(), (HOST, PORT))

    # Receber confirmação do servidor
    client.settimeout(5.0)
    try:
        resposta_inicial, _ = client.recvfrom(BUFFER_SIZE)
        comando, args = interpretar_mensagem(resposta_inicial.decode())
        print(f"Recebida resposta do servidor: {resposta_inicial.decode()}")

        if comando != CMD_OK:
            print(f"Erro do servidor: {' '.join(args)}")
            return

        total_segmentos = int(args[0])
        print(f"Servidor confirmou. Esperando {total_segmentos} segmentos.")

    except socket.timeout:
        print("Erro: O servidor não respondeu ao pedido inicial.")
        return

    # Receber segmentos
    buffer_recepcao = {}
    segmentos_a_perder = {5, 10, 15}  # simulação de perda
    print(f"Simulação de perda: Segmentos {segmentos_a_perder} serão descartados.")

    client.settimeout(2.0)
    while len(buffer_recepcao) < total_segmentos:
        try:
            pacote, _ = client.recvfrom(BUFFER_SIZE)
            if SEPARADOR not in pacote:
                continue
            header_bytes, dados_segmento = pacote.split(SEPARADOR, 1)
            comando_seg, args_seg = interpretar_mensagem(header_bytes.decode())

            if comando_seg != CMD_SEGMENT or not args_seg:
                continue

            seq_num = int(args_seg[0])

            if seq_num in segmentos_a_perder:
                print(f" -> Descartando segmento {seq_num} (simulação de perda).")
                segmentos_a_perder.remove(seq_num)
                continue

            if seq_num not in buffer_recepcao:
                buffer_recepcao[seq_num] = dados_segmento
                #print(f" -> Recebido segmento {seq_num}")

        except socket.timeout:
            print("Timeout da transmissão inicial. Verificando faltantes...")
            break

    # Ciclo de retransmissão
    while True:
        numeros_recebidos = set(buffer_recepcao.keys())
        numeros_esperados = set(range(total_segmentos))
        numeros_faltantes = sorted(list(numeros_esperados - numeros_recebidos))

        if not numeros_faltantes:
            break

        print(f"CICLO DE RECUPERAÇÃO: Faltando {len(numeros_faltantes)} segmentos: {numeros_faltantes[:10]}...")

        pedido_retx = construir_pedido_retransmissao(numeros_faltantes)
        client.sendto(pedido_retx.encode(), (HOST, PORT))

        # Receber retransmissões
        client.settimeout(2.0)
        try:
            while True:
                pacote, _ = client.recvfrom(BUFFER_SIZE)
                if SEPARADOR not in pacote:
                    continue
                header_bytes, dados_segmento = pacote.split(SEPARADOR, 1)
                comando_seg, args_seg = interpretar_mensagem(header_bytes.decode())

                if comando_seg != CMD_SEGMENT or not args_seg:
                    continue

                seq_num = int(args_seg[0])
                if seq_num not in buffer_recepcao:
                    buffer_recepcao[seq_num] = dados_segmento
                    print(f" -> Reforço recebido: segmento {seq_num}")

        except socket.timeout:
            print("Timeout da rajada de retransmissão. Reavaliando faltantes...")

    # Montar arquivo final
    caminho_saida = "recebido_" + nome_arquivo.split('/')[-1]
    with open(caminho_saida, "wb") as f:
        for i in range(total_segmentos):
            f.write(buffer_recepcao[i])

    print(f"Todos os segmentos foram recebidos e arquivo '{caminho_saida}' montado com sucesso!")
    client.close()


if __name__ == "__main__":
    arquivo_alvo = "files/arquivo_grande.txt"
    print(f"=== Cliente UDP: Iniciando a requisição para {arquivo_alvo} ===")
    requisitar_arquivo(arquivo_alvo)
    print("=== Cliente UDP: Missão concluída ===")
