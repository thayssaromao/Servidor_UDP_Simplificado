import socket
import time
from protocol import (
    interpretar_mensagem,
    construir_mensagem,
    construir_pedido_retransmissao,
    CMD_OK,
    CMD_SEGMENT,
    CMD_GET_FILE  # Nome que você usou no seu protocolo
)

HOST = '127.0.0.1'  # ENDEREÇO DO SERVIDOR
PORT = 12345        # Porta usada pelo servidor
BUFFER_SIZE = 4096  # Tam. máximo de dados a serem recebidos

def requisitar_arquivo(nome_arquivo):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    comand = f"GET|{nome_arquivo}"
    client.sendto(comand.encode(), (HOST, PORT))

    # ================== 2. AGUARDAR CONFIRMAÇÃO ==================
    try:
        client.settimeout(5.0)
        resposta_inicial, _ = client.recvfrom(BUFFER_SIZE)
        comando, args = interpretar_mensagem(resposta_inicial.decode())

        if comando != CMD_OK:
            print(f"Erro do servidor: {' '.join(args)}")
            return

        total_segmentos = int(args[1])
        print(f"Servidor confirmou. Esperando {total_segmentos} segmentos.")

    except socket.timeout:
        print("Erro: O servidor não respondeu ao pedido inicial.")
        return

    # ================== 3. PREPARAÇÃO PARA RECEPÇÃO ==================
    buffer_recepcao = {}
    segmentos_a_perder = {5, 10, 15}
    print(f"Simulação de perda: Segmentos {segmentos_a_perder} serão descartados.")

    # ================== 4. LOOP DE RECEPÇÃO EM MASSA ==================
    client.settimeout(2.0)
    while len(buffer_recepcao) < total_segmentos:
        try:
            pacote, _ = client.recvfrom(BUFFER_SIZE)

            # 🔧 PARSING CORRIGIDO
            try:
                comando_bytes, seq_bytes, dados_segmento = pacote.split(b'|', 2)
                comando_seg = comando_bytes.decode()
                seq_num = int(seq_bytes.decode())
            except ValueError:
                print("Pacote mal formatado recebido. Ignorando.")
                continue

            if comando_seg == CMD_SEGMENT:
                if seq_num in segmentos_a_perder:
                    print(f" -> Descartando segmento {seq_num} (simulação de perda).")
                    segmentos_a_perder.remove(seq_num)
                    continue

                print(f" -> Recebido segmento {seq_num}")
                buffer_recepcao[seq_num] = dados_segmento

        except socket.timeout:
            print("Timeout! A transmissão inicial parece ter terminado ou estagnado.")
            break

    # ================== 6. VERIFICAR BAIXAS E PEDIR REFORÇOS ==================
    while len(buffer_recepcao) < total_segmentos:
        numeros_recebidos = set(buffer_recepcao.keys())
        numeros_esperados = set(range(total_segmentos))
        numeros_faltantes = sorted(list(numeros_esperados - numeros_recebidos))

        if not numeros_faltantes:
            break

        print(f"CICLO DE RECUPERAÇÃO. Faltando {len(numeros_faltantes)} segmentos: {numeros_faltantes[:10]}...")

        pedido_retx = construir_pedido_retransmissao(numeros_faltantes)
        if pedido_retx:
            client.sendto(pedido_retx.encode(), (HOST, PORT))

        try:
            while True:
                pacote, _ = client.recvfrom(BUFFER_SIZE)

                # 🔧 PARSING CORRIGIDO (retransmissões)
                try:
                    comando_bytes, seq_bytes, dados_segmento = pacote.split(b'|', 2)
                    comando_seg = comando_bytes.decode()
                    seq_num = int(seq_bytes.decode())
                except ValueError:
                    print("Pacote mal formatado recebido (retransmissão). Ignorando.")
                    continue

                if comando_seg == CMD_SEGMENT:
                    if seq_num in numeros_faltantes:
                        print(f" -> Reforço recebido: segmento {seq_num}")
                        buffer_recepcao[seq_num] = dados_segmento
                    else:
                        print(f" -> Recebido segmento duplicado ou inesperado {seq_num}. Ignorando.")

        except socket.timeout:
            print("Rajada de retransmissão terminada. Reavaliando o campo de batalha...")

    # ================== 7. RECONSTRUIR E DECLARAR VITÓRIA ==================
    print("Todos os segmentos foram recebidos com sucesso.")
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
    print("==========================================================")
    print("Cliente UDP: Missão (tentativa) concluída.")
