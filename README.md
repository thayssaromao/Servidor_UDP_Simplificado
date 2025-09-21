## Transferência de Arquivos via sistema UDP

Este projeto é uma aplicação cliente-servidor para transferência de arquivos que opera sobre o protocolo UDP. O principal objetivo é demonstrar a implementação manual de mecanismos de controle e confiabilidade, como o gerenciamento de sessões, detecção de erros e retransmissão, que o protocolo TCP oferece nativamente.

### Funcionalidades Implementadas

  * **Comunicação UDP**: O projeto utiliza a API de sockets do Python para a comunicação cliente-servidor.
  * **Transferência de Arquivos**: Um arquivo é dividido em segmentos e transmitido do servidor para o cliente.
  * **Aperto de Mão (Handshake)**: A sessão é iniciada com um comando `HELLO` do cliente e uma resposta `OK` do servidor, estabelecendo a comunicação.
  * **Encerramento de Sessão**: O cliente envia um comando `BYE` ao final da transferência para sinalizar que o servidor pode liberar os recursos associados.
  * **Verificação de Integridade**: Cada segmento de dados inclui um checksum (`zlib.adler32`) no cabeçalho para que o cliente possa detectar e descartar pacotes corrompidos.
  * **Retransmissão**: O cliente identifica segmentos perdidos ou corrompidos e solicita a retransmissão ao servidor, garantindo a integridade do arquivo final.
  * **Interface Interativa**: O usuário pode especificar o IP, a porta do servidor e o nome do arquivo a ser baixado via entrada interativa no terminal.

### Tecnologias Utilizadas

  * **Linguagem**: Python 3.x
  * **Bibliotecas Padrão**: `socket`, `os`, `zlib`, `time`

### Estrutura do Projeto

  * `server.py`: O servidor UDP que aguarda requisições, divide e envia os arquivos em segmentos, e gerencia as retransmissões.
  * `client.py`: O cliente UDP que solicita o arquivo, recebe e monta os segmentos, e lida com a retransmissão de pacotes.
  * `protocol.py`: Define as constantes e as funções para construir e interpretar as mensagens do protocolo de aplicação (`HELLO`, `GET`, `SEG`, `RETX`, `BYE`, etc.).
  * `utils.py`: Contém funções utilitárias, como a verificação de arquivos, divisão do arquivo em blocos e cálculo de checksum.

### Como Executar o Projeto

1.  **Inicie o servidor**: Abra um terminal e execute o arquivo `server.py`.

    ```bash
    python3 server.py
    ```

    O servidor exibirá a mensagem "Servidor UDP esperando mensagens...".

2.  **Inicie o cliente**: Abra outro terminal e execute o arquivo `client.py`.

    ```bash
    python3 client.py
    ```

    O cliente solicitará interativamente o IP do servidor, a porta e o nome do arquivo a ser requisitado.

### Simulação de Falhas

Para testar os mecanismos de confiabilidade, o código já vem configurado com simulações de falhas:

  * **Simulação de Perda de Pacotes**: O `client.py` está configurado para descartar intencionalmente os segmentos de número **5, 10 e 15**. A retransmissão desses pacotes será solicitada e a mensagem "Descartando segmento X (simulação de perda)." será exibida no terminal.
  * **Simulação de Corrupção de Dados**: Você pode modificar o `server.py` para corromper um pacote específico. O cliente detectará a corrupção por meio do checksum e solicitará o reenvio do pacote correto, exibindo a mensagem "AVISO: Segmento X corrompido. Descartando.".
