import os, zlib

class FileChecker:
    def __init__(self, filename):
        self.filename = filename

    def file_exists(self):
        return os.path.exists(self.filename)

    def file_size_mb(self):
        if not self.file_exists():
            return 0
        return os.path.getsize(self.filename) / (1024 * 1024)

def dividir_arquivo(caminho: str, tamanho_bloco: int):
    """Divide um arquivo em blocos binários."""
    segmentos = []
    try:
        with open(caminho, "rb") as f:
            while bloco := f.read(tamanho_bloco):
                segmentos.append(bloco)
        return segmentos
    except FileNotFoundError:
        return []

def montar_arquivo(segmentos: dict, destino: str):
    """Monta arquivo a partir dos segmentos recebidos."""
    with open(destino, "wb") as f:
        for seq in sorted(segmentos):
            f.write(segmentos[seq])
