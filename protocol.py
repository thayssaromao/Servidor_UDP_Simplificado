# Constantes
CMD_HELLO        = "HELLO"
CMD_GET_FILE     = "GET"
CMD_SEGMENT      = "SEG"
CMD_ACK          = "ACK"
CMD_RETRANSMIT   = "RETX"
CMD_BYE          = "BYE"
CMD_ERROR        = "ERR"
CMD_OK           = "OK"
CMD_END          = "END"


DELIMITADOR = "|"

# ================================
# Funções para construir mensagens
# ================================

def construir_mensagem(cmd, *args):
    """
    Constrói uma mensagem seguindo o protocolo:
    Ex: construir_mensagem("GET", "arquivo.txt") → "GET|arquivo.txt"
    """
    return DELIMITADOR.join([cmd] + list(map(str, args)))


# ===============================
# Funções para interpretar mensagens
# ===============================

def interpretar_mensagem(mensagem):
    """
    Interpreta uma mensagem recebida:
    Ex: "GET|arquivo.txt" → ("GET", ["arquivo.txt"])
    """
    partes = mensagem.strip().split(DELIMITADOR)
    comando = partes[0]
    argumentos = partes[1:]
    return comando, argumentos

def construir_pedido_retransmissao(numeros_faltantes: list) -> str:
    """
    Forja uma mensagem de RETX a partir de uma lista de números de sequência ausentes.
    Ex: [5, 10, 15] -> "RETX|5,10,15"
    """

    if not numeros_faltantes:
        return None

    # Converte cada número de sequência em uma string.
    numero_str = [str(seq) for seq in numeros_faltantes]

    # Une os números com uma vírgula, formando a carga útil da sua mensagem.
    payload = ",".join(numero_str)

    # Usa sua função já existente para construir o comando final.
    return construir_mensagem(CMD_RETRANSMIT, payload)
    
# ===============================
# Mensagens padronizadas
# ===============================

MSG_CONEXAO_OK = construir_mensagem(CMD_OK, "Conexão estabelecida\n")
MSG_DESCONEXAO = construir_mensagem(CMD_BYE, "Desconectado com sucesso")
MSG_ERRO_GERAL = construir_mensagem(CMD_ERROR, "Erro desconhecido")
MSG_ARQUIVO_NAO_ENCONTRADO = construir_mensagem(CMD_ERROR, "Arquivo não encontrado")
