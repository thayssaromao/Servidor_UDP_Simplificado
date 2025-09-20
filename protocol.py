# Constantes
CMD_HELLO        = "HELLO"
CMD_GET_FILE     = "GET"
CMD_SEGMENT      = "SEG"
CMD_ACK          = "ACK"
CMD_RETRANSMIT   = "RETX"
CMD_BYE          = "BYE"
CMD_ERROR        = "ERR"
CMD_OK           = "OK"

DELIMITADOR = "|"

# ================================
# Funções para construir mensagens
# ================================

def construir_mensagem(cmd, *args):
    """Constrói uma mensagem seguindo o protocolo."""
    return DELIMITADOR.join([cmd] + list(map(str, args)))

# ===============================
# Funções para interpretar mensagens
# ===============================

def interpretar_mensagem(mensagem):
    """Interpreta uma mensagem recebida."""
    partes = mensagem.strip().split(DELIMITADOR)
    comando = partes[0]
    argumentos = partes[1:]
    return comando, argumentos

def construir_pedido_retransmissao(numeros_faltantes: list) -> str:
    """Forja uma mensagem RETX a partir de uma lista de sequências ausentes."""
    if not numeros_faltantes:
        return None
    numero_str = [str(seq) for seq in numeros_faltantes]
    payload = ",".join(numero_str)
    return construir_mensagem(CMD_RETRANSMIT, payload)

# ===============================
# Mensagens padronizadas
# ===============================

MSG_CONEXAO_OK = construir_mensagem(CMD_OK, "Conexão estabelecida")  # Ajuste conforme uso no servidor
MSG_DESCONEXAO = construir_mensagem(CMD_BYE, "Desconectado com sucesso")
MSG_ERRO_GERAL = construir_mensagem(CMD_ERROR, "Erro desconhecido")
MSG_ARQUIVO_NAO_ENCONTRADO = construir_mensagem(CMD_ERROR, "Arquivo não encontrado")
