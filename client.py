import socket
import zlib
from protocol import (
    interpretar_mensagem,
    construir_mensagem,
    construir_pedido_retransmissao,
    CMD_GET_FILE,
    CMD_OK,
    CMD_SEGMENT,
    CMD_HELLO,
    CMD_BYE,
    CMD_END)
import time

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 65536
SEPARADOR = b'|||'  

def requisitar_arquivo(host, port, nome_arquivo):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(5.0)

    # Passo 1: Esperar o servidor estar pronto
    print("Enviando HELLO para o servidor...")
    client.sendto(construir_mensagem(CMD_HELLO).encode(), (host, port))
    try:
        resposta, _ = client.recvfrom(BUFFER_SIZE)
        comando, _ = interpretar_mensagem(resposta.decode())
        if comando != CMD_OK:
            print("Resposta inesperada do servidor. Encerrando.")
            return
        print("Servidor respondeu com OK. Continuando...")
    except socket.timeout:
        print("Erro: O servidor não respondeu ao HELLO.")
        return
    
    # Passo 2: Enviar pedido 
    pedido_inicial = construir_mensagem(CMD_GET_FILE, nome_arquivo)
    print(f"Enviando pedido inicial para o servidor: {pedido_inicial}")
    client.sendto(pedido_inicial.encode(), (host, port))

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

            partes_header = header_bytes.decode().split("|")
            comando_seg = partes_header[0]

            if comando_seg != CMD_SEGMENT:
                # Tratar pacotes de controle como CMD_END
                if comando_seg == CMD_END:
                    print("Sinal de fim de transmissão recebido.")
                    break
                continue

            seq_num = int(partes_header[1])
            check_recebido = int(partes_header[2])

            checksum_calculado = zlib.adler32(dados_segmento)
            if check_recebido != checksum_calculado:
                print(f" -> Aviso! Segmento {seq_num} corrompido. Descartando.")
                #O cliente agora extrai o checksum do cabeçalho de cada segmento recebido, valida a integridade dos dados e descarta o pacote se o checksum não corresponder.
                continue

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

    # Defina quantas vezes o cliente tentará pedir retransmissão antes de desistir
    MAX_TENTATIVAS_RETX = 5

    # Dicionário para rastrear tentativas por segmento
    tentativas_retx = {seq: 0 for seq in range(total_segmentos)}

    # Ciclo de retransmissão
    while True:
        numeros_recebidos = set(buffer_recepcao.keys())
        numeros_esperados = set(range(total_segmentos))
        numeros_faltantes = sorted(list(numeros_esperados - numeros_recebidos))

        if not numeros_faltantes:
            break

        #Verifica se algum segmento excedeu o limite de tentativas
        if all(tentativas_retx[seq] >= MAX_TENTATIVAS_RETX for seq in numeros_faltantes):
            print("Erro: Servidor indisponível ou segmentos não chegam. Transferência abortada.")
            return

        # Atualiza tentativas para os faltantes
        for seq in numeros_faltantes:
            tentativas_retx[seq] += 1

        print(f"CICLO DE RECUPERAÇÃO: Faltando {len(numeros_faltantes)} segmentos: {numeros_faltantes[:10]}...")

        pedido_retx = construir_pedido_retransmissao(numeros_faltantes)
        client.sendto(pedido_retx.encode(), (host, port))

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

    # Passo 3: Enviar o BYE após a conclusão (cliente depende exclusivamente de saber o número total de segmentos para encerrar a transmissão.)
    print("Enviando BYE para encerrar a sessão...")
    client.sendto(construir_mensagem(CMD_BYE).encode(), (host, port))
    
    client.close()

def coletar_dados_requisicao():
    """
    Coleta interativamente o IP, a porta e o nome do arquivo do usuário.
    Inclui tratamento de erro para a porta.
    """
    print("=== Coletando dados da requisição ===")
    host = input("Digite o IP do servidor (ex: 127.0.0.1): ").strip() or '127.0.0.1'
    
    while True:
        try:
            port_str = input("Digite a porta do servidor (ex: 12345): ").strip() or '12345'
            port = int(port_str)
            
             # Evita portas bem conhecidas
            if port < 1024:
                print("Portas abaixo de 1024 são reservadas. Escolha outra.")
                continue
            break
            
        except ValueError:
            print("Entrada inválida. A porta deve ser um número inteiro.")

    nome_arquivo = input("Digite o nome do arquivo a ser requisitado (ex: files/arquivo_grande.txt): ").strip() or 'files/arquivo_grande.txt'
    
    return host, port, nome_arquivo

if __name__ == "__main__":
    print("=== Cliente UDP: Iniciando ===")
    HOST, PORT, arquivo_alvo = coletar_dados_requisicao()
    
    print(f"\n=== Cliente UDP: Iniciando a requisição para {arquivo_alvo} ===\n")
    requisitar_arquivo(HOST, PORT, arquivo_alvo)
    print("\n=== Cliente UDP: Missão concluída ===")
