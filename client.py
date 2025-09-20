import socket
from protocol import (
    interpretar_mensagem,
    construir_mensagem,
    construir_pedido_retransmissao,
    CMD_OK,
    CMD_SEGMENT,
    CMD_GET_FILE  # Nome do comando GET no seu protocolo
)

HOST = '127.0.0.1'  # Endereço do servidor
PORT = 12345        # Porta usada pelo servidor
BUFFER_SIZE = 4096  # Tamanho máximo de dados a serem recebidos


def requisitar_arquivo(nome_arquivo):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # ================== 1. PEDIDO INICIAL ==================
    comando_inicial = f"{CMD_GET_FILE}|{nome_arquivo}"
    print(f"Enviando pedido inicial para o servidor: {comando_inicial}")
    client.sendto(comando_inicial.encode(), (HOST, PORT))

    # ================== 2. AGUARDAR CONFIRMAÇÃO ==================
    try:
        client.settimeout(5.0)  # Espera até 5 segundos
        resposta_inicial, _ = client.recvfrom(BUFFER_SIZE)
        comando, args = interpretar_mensagem(resposta_inicial.decode())
        print(f"Recebida resposta do servidor: {resposta_inicial.decode()}")

        if comando != CMD_OK:
            print(f"Erro do servidor: {' '.join(args)}")
            return

        total_segmentos = int(args[0])  # Extrai o número total de segmentos
        print(f"Servidor confirmou. Esperando {total_segmentos} segmentos.")

    except socket.timeout:
        print("Erro: O servidor não respondeu ao pedido inicial.")
        return

    # ================== 3. PREPARAÇÃO PARA RECEPÇÃO ==================
    buffer_recepcao = {}
    segmentos_a_perder = {5, 10, 15}  # Simulação de perdas
    print(f"Simulação de perda: Segmentos {segmentos_a_perder} serão descartados.")

    client.settimeout(2.0)  # Timeout para detectar fim da transmissão inicial

    # ================== 4. LOOP DE RECEPÇÃO INICIAL ==================
    while len(buffer_recepcao) < total_segmentos:
        try:
            pacote, _ = client.recvfrom(BUFFER_SIZE)

            split_index = pacote.find(b'|')
            if split_index == -1:
                print(" -> Pacote malformado recebido, ignorando")
                continue

            header_bytes = pacote[:split_index + 2]
            dados_segmento = pacote[split_index + 2:]

            header_str = header_bytes.decode()
            comando_seg, args_seg = interpretar_mensagem(header_str)
            seq_num = int(args_seg[0])

            if seq_num in segmentos_a_perder:
                #print(f" -> Descartando segmento {seq_num} (simulação de perda).")
                segmentos_a_perder.remove(seq_num)
                continue

            #print(f" -> Recebido segmento {seq_num}")
            buffer_recepcao[seq_num] = dados_segmento

        except socket.timeout:
            print("Timeout! Transmissão inicial parece ter terminado.")
            break

    # ================== 5. VERIFICAR PERDAS E PEDIR RETRANSMISSÃO ==================
    while len(buffer_recepcao) < total_segmentos:
        numeros_recebidos = set(buffer_recepcao.keys())
        numeros_esperados = set(range(total_segmentos))
        numeros_faltantes = sorted(list(numeros_esperados - numeros_recebidos))

        if not numeros_faltantes:
            break

        print(f"CICLO DE RECUPERAÇÃO: Faltando {len(numeros_faltantes)} segmentos: {numeros_faltantes[:10]}...")

        pedido_retx = construir_pedido_retransmissao(numeros_faltantes)
        if pedido_retx:
            client.sendto(pedido_retx.encode(), (HOST, PORT))

        try:
            while True:
                pacote, _ = client.recvfrom(BUFFER_SIZE)

                split_index = pacote.find(b'|')
                if split_index == -1:
                    continue

                header_bytes = pacote[:split_index + 2]
                dados_segmento = pacote[split_index + 2:]

                header_str = header_bytes.decode()
                comando_seg, args_seg = interpretar_mensagem(header_str)
                seq_num = int(args_seg[0])

                if seq_num in numeros_faltantes:
                    #print(f" -> Reforço recebido: segmento {seq_num}")
                    buffer_recepcao[seq_num] = dados_segmento
                #else:
                    #print(f" -> Pacote duplicado ou inesperado {seq_num}, ignorando.")

        except socket.timeout:
            print("Timeout da rajada de retransmissão. Reavaliando...")

    # ================== 6. MONTAR ARQUIVO FINAL ==================
    caminho_saida = "recebido_" + nome_arquivo.split('/')[-1]
    with open(caminho_saida, "wb") as f:
        for i in range(total_segmentos):
            f.write(buffer_recepcao[i])
    print(f"Arquivo '{caminho_saida}' montado com sucesso!")

    client.close()


if __name__ == "__main__":
    arquivo_alvo = "files/arquivo_grande.txt"
    print(f"=== Cliente UDP: Iniciando a requisição para {arquivo_alvo} ===")
    requisitar_arquivo(arquivo_alvo)
    print("=== Cliente UDP: Missão concluída ===")
