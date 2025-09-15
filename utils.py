# - Recepção e Protocolo:
#     - Aguardar conexões/mensagens de clientes.
#     - Interpretar as requisições recebidas. É necessário definir e implementar um protocolo de aplicação simples sobre UDP para que o cliente requisite arquivos (Exemplo de formato de requisição: GET /nome_do_arquivo.ext).
# -Processamento da Requisição:
#     - Verificar se o arquivo solicitado existe.
#     - Se o arquivo não existir: Enviar uma mensagem de erro claramente definida pelo seu protocolo para o cliente.
# - Transmissão do Arquivo (se existir):
#     - O arquivo a ser transmitido deve ser relativamente grande (ex: > 1 MB) para justificar a segmentação.
#     - Segmentação: Dividir o arquivo em múltiplos segmentos/pedaços para envio em datagramas UDP.
#     - Cabeçalho Customizado: Cada segmento enviado deve conter informações de controle definidas pelo seu protocolo (ver “Considerações de Protocolo” abaixo).
#     - Retransmissão: Implementar lógica para reenviar segmentos específicos caso o cliente solicite (devido a perdas ou erros).


#Verificar se o arquivo solicitado existe.

def checkFile():
    filename = "test.txt"
    try:
        with open(filename, "r", encoding="utf-8") as file:
            lines = file.readlines()
            print('Conteúdo do arquivo:')  
            for li in lines:
                print(li.strip())
    except FileNotFoundError:
        print(f"Arquivo {file} não encontrado")
    except Exception as e:
        return f"ERRO: {str(e)}"
