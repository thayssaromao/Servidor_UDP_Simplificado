import socket
import time
from protocol import (
    interpretar_mensagem,
    construir_mensagem,
    construir_pedido_retransmissao,
    CMD_OK,
    CMD_SEGMENT,
    CMD_GET_FILE # Nome que você usou no seu protocolo
)
HOST = '127.0.0.1' #ENDEREÇO DO SERVIDOR
PORT = 12345 # Porta usada pelo servidor
BUFFER_SIZE = 4096 #tam maximo de dados a serem recebidos
    
def requisitar_arquivo(nome_arquivo):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #cria um cliente usando protocolo udp

    comand = f"GET|{nome_arquivo}"
    client.sendto(comand.encode(), (HOST, PORT)) # transforma o txt e, bytes e enviar pro servidor

   # ================== 2. AGUARDAR CONFIRMAÇÃO ==================
    try:
        # Definir um timeout para a primeira resposta
        client.settimeout(5.0) # Espera por 5 segundos
        
        resposta_inicial, _ = client.recvfrom(BUFFER_SIZE)
        comando, args = interpretar_mensagem(resposta_inicial.decode())

        if comando != CMD_OK:
            print(f"Erro do servidor: {' '.join(args)}")
            return

        total_segmentos = int(args[1]) # Extrai o número total de segmentos da mensagem "OK"
        print(f"Servidor confirmou. Esperando {total_segmentos} segmentos.")

    except socket.timeout:
        print("Erro: O servidor não respondeu ao pedido inicial.")
        return

    # ================== 3. PREPARAÇÃO PARA RECEPÇÃO ==================
    buffer_recepcao = {}
    
    # Defina aqui quais segmentos simular como "perdidos"
    segmentos_a_perder = {5, 10, 15} # Exemplo: descartar segmentos 5, 10 e 15
    print(f"Simulação de perda: Segmentos {segmentos_a_perder} serão descartados.")

    # ================== 4. LOOP DE RECEPÇÃO EM MASSA ==================
    client.settimeout(2.0) # Timeout mais curto para detectar o fim da transmissão
    while len(buffer_recepcao) < total_segmentos:
        try:
            pacote, _ = client.recvfrom(BUFFER_SIZE)
            
            # Interpretação do pacote de dados (SEG|num_seq|dados)
            # A forma de separar o header dos dados depende do seu protocolo
            header_bytes, dados_segmento = pacote.split(b'|', 2)
            header = header_bytes.decode()
            comando_seg, args_seg = interpretar_mensagem(header)
            
            if comando_seg == CMD_SEGMENT:
                seq_num = int(args_seg[0])

                # 5. SIMULAR O CAOS
                if seq_num in segmentos_a_perder:
                    print(f" -> Descartando segmento {seq_num} (simulação de perda).")
                    segmentos_a_perder.remove(seq_num) # Descarte apenas uma vez
                    continue # Pula para a próxima iteração do loop

                print(f" -> Recebido segmento {seq_num}")
                buffer_recepcao[seq_num] = dados_segmento

        except socket.timeout:
            print("Timeout! A transmissão inicial parece ter terminado ou estagnado.")
            break # Sai do loop para verificar o que foi perdido

    # ================== 6. VERIFICAR BAIXAS E PEDIR REFORÇOS ==================
    # O loop externo persiste enquanto o arquivo não estiver completo.
    while len(buffer_recepcao) < total_segmentos:
    
        # 6.1. IDENTIFICAR AS BAIXAS
        numeros_recebidos = set(buffer_recepcao.keys())
        numeros_esperados = set(range(total_segmentos))
        numeros_faltantes = sorted(list(numeros_esperados - numeros_recebidos))

        if not numeros_faltantes:
            # Vitória! Nenhuma baixa a relatar. Saia do ciclo de guerra.
            break

        print(f"CICLO DE RECUPERAÇÃO. Faltando {len(numeros_faltantes)} segmentos: {numeros_faltantes[:10]}...") # Mostra apenas os 10 primeiros para não poluir
        
        # 6.2. PEDIR REFORÇOS (RETX)
        pedido_retx = construir_pedido_retransmissao(numeros_faltantes)
        if pedido_retx:
            client.sendto(pedido_retx.encode(), (HOST, PORT))

        # 6.3. RECEBER A ONDA DE REFORÇOS ATÉ O SILÊNCIO (TIMEOUT)
        try:
            # Loop interno para receber a rajada de retransmissões
            while True: 
                pacote, _ = client.recvfrom(BUFFER_SIZE)
                
                # A lógica de processamento de pacote é a mesma de antes
                header_bytes, dados_segmento = pacote.split(b'|', 2)
                header = header_bytes.decode()
                comando_seg, args_seg = interpretar_mensagem(header)
                
                if comando_seg == CMD_SEGMENT:
                    seq_num = int(args_seg[0])
                    
                    # Verifique se o pacote recebido é um dos que faltavam para evitar trabalho desnecessário.
                    if seq_num in numeros_faltantes:
                        print(f" -> Reforço recebido: segmento {seq_num}")
                        buffer_recepcao[seq_num] = dados_segmento
                    else:
                        # Este é um pacote duplicado de uma transmissão anterior que chegou atrasado.
                        print(f" -> Recebido segmento duplicado ou inesperado {seq_num}. Ignorando.")

        except socket.timeout:
            # O timeout aqui é um SUCESSO. Significa que a rajada de retransmissão do servidor terminou.
            print("Rajada de retransmissão terminada. Reavaliando o campo de batalha...")

    # ================== 7. RECONSTRUIR E DECLARAR VITÓRIA ==================
    print("Todos os segmentos foram recebidos com sucesso.")
    
    # (Opcional: integre sua função montar_arquivo de utils.py aqui)
    caminho_saida = "recebido_" + nome_arquivo.split('/')[-1]
    with open(caminho_saida, "wb") as f:
        for i in range(total_segmentos):
            f.write(buffer_recepcao[i])
    print(f"Arquivo '{caminho_saida}' montado com sucesso!")

    client.close()

    # ================== A ORDEM DE EXECUÇÃO ==================
# Este bloco é executado quando você digita "python client.py"
if __name__ == "__main__":
    # O nome do arquivo a ser buscado. Pode ser fixo ou pedido ao usuário.
    # Vamos usar o do seu projeto para o teste.
    arquivo_alvo = "files/test.txt" 
    
    print(f"=== Cliente UDP: Iniciando a requisição para {arquivo_alvo} ===")
    
    # A CHAMADA DE FUNÇÃO. ESTA É A ORDEM PARA ATACAR.
    requisitar_arquivo(arquivo_alvo)
    
    print("==========================================================")
    print("Cliente UDP: Missão (tentativa) concluída.")
