.PHONY: run

run:
	@echo "Iniciando servidor UDP..."
	python3 server.py &  # Roda em background
	sleep 1              # Espera 1 segundo para o servidor iniciar
	@echo "Iniciando cliente UDP..."
	python3 client.py
