import socket
from protocol import (
    interpretar_mensagem,
    construir_mensagem,
    construir_pedido_retransmissao,
    CMD_OK,
    CMD_SEGMENT,
)
HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 4096

def requisitar_arquivo(nome_arquivo):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # ================== 1. ENVIAR PEDIDO INICIAL ==================
    comando = f"GET|{nome_arquivo}"
    print(f"Enviando pedido inicial para o servidor: {comando}")
    client.sendto(comando.encode(), (HOST, PORT))

    # ================== 2. AGUARDAR CONFIRMAÇÃO ==================
    try:
        client.settimeout(5.0)
        resposta_inicial, _ = client.recvfrom(BUFFER_SIZE)
        comando_resp, args_resp = interpretar_mensagem(resposta_inicial.decode())

        print(f"Recebida resposta do servidor: {resposta_inicial.decode()}")

        if comando_resp != CMD_OK:
            print(f"Erro do servidor: {' '.join(args_resp)}")
            return

        # Extrai número total de segmentos da mensagem "OK"
        try:
            total_segmentos = int(args_resp[1])
        except IndexError:
            print("Erro: total de segmentos não especificado pelo servidor.")
            return

        print(f"Servidor confirmou. Total de segmentos a receber: {total_segmentos}")

    except socket.timeout:
        print("Erro: O servidor não respondeu ao pedido inicial.")
        return

    # ================== 3. PREPARAÇÃO PARA RECEPÇÃO ==================
    buffer_recepcao = {}

    # Defina aqui quais segmentos simular como "perdidos"
    segmentos_a_perder = {5, 10, 15}  # Exemplo
    print(f"Simulação de perda: segmentos {segmentos_a_perder} serão descartados.")

    # ================== 4. LOOP DE RECEPÇÃO ==================
    client.settimeout(2.0)
    while len(buffer_recepcao) < total_segmentos:
        try:
            pacote, _ = client.recvfrom(BUFFER_SIZE)

            # Separar header e dados
            try:
                header_bytes, dados_segmento = pacote.split(b'|', 1)
            except ValueError:
                print("Pacote mal formado recebido, ignorando.")
                continue

            header = header_bytes.decode()
            comando_seg, args_seg = interpretar_mensagem(header)

            if comando_seg == CMD_SEGMENT:
                seq_num = int(args_seg[0])

                # Simular perda
                if seq_num in segmentos_a_perder:
                    print(f" -> Descartando segmento {seq_num} (simulação).")
                    segmentos_a_perder.remove(seq_num)
                    continue

                print(f" -> Recebido segmento {seq_num}")
                buffer_recepcao[seq_num] = dados_segmento

        except socket.timeout:
            print("Timeout de recepção inicial atingido.")
            break

    # ================== 5. RETRANSMISSÃO ==================
    while len(buffer_recepcao) < total_segmentos:
        numeros_esperados = set(range(total_segmentos))
        numeros_recebidos = set(buffer_recepcao.keys())
        numeros_faltantes = sorted(list(numeros_esperados - numeros_recebidos))

        if not numeros_faltantes:
            break

        print(f"Solicitando retransmissão de segmentos faltantes: {numeros_faltantes}")

        pedido_retx = construir_pedido_retransmissao(numeros_faltantes)
        if pedido_retx:
            client.sendto(pedido_retx.encode(), (HOST, PORT))

        try:
            while True:
                pacote, _ = client.recvfrom(BUFFER_SIZE)
                try:
                    header_bytes, dados_segmento = pacote.split(b'|', 1)
                except ValueError:
                    print("Pacote mal formado recebido, ignorando.")
                    continue

                header = header_bytes.decode()
                comando_seg, args_seg = interpretar_mensagem(header)

                if comando_seg == CMD_SEGMENT:
                    seq_num = int(args_seg[0])
                    if seq_num in numeros_faltantes:
                        print(f" -> Reforço recebido: segmento {seq_num}")
                        buffer_recepcao[seq_num] = dados_segmento
                    else:
                        print(f" -> Segmento duplicado ou inesperado {seq_num}, ignorando.")

        except socket.timeout:
            print("Timeout após retransmissão. Reavaliando segmentos faltantes.")

    # ================== 6. MONTAR ARQUIVO ==================
    print("Todos os segmentos recebidos. Montando arquivo...")
    caminho_saida = "recebido_" + nome_arquivo.split('/')[-1]
    with open(caminho_saida, "wb") as f:
        for i in range(total_segmentos):
            f.write(buffer_recepcao[i])

    print(f"Arquivo '{caminho_saida}' montado com sucesso!")

    client.close()


if __name__ == "__main__":
    arquivo_alvo = "files/test.txt"
    print(f"=== Cliente UDP: Iniciando a requisição para {arquivo_alvo} ===")
    requisitar_arquivo(arquivo_alvo)
    print("=== Cliente UDP: Missão concluída ===")
