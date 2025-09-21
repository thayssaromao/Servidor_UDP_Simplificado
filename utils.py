import os

class FileChecker:
    def __init__(self, filename):
        self.filename = filename

    def file_exists(self):
        return os.path.exists(self.filename)

    def file_size_mb(self):
        if not self.file_exists():
            return 0
        return os.path.getsize(self.filename) / (1024 * 1024)

    def read_file(self):
        if not self.file_exists():
            print(f"O arquivo '{self.filename}' não existe.")
            return

        size_mb = self.file_size_mb()

        if size_mb < 1:
            print(f"O arquivo '{self.filename}' deve ser maior que 1MB")
            return

        print(f"O arquivo '{self.filename}' tem {size_mb:.2f} MB")

        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                print("Conteúdo do arquivo:")
                for line in lines:
                    print(line.strip())
        except Exception as e:
            print(f"ERRO ao ler o arquivo: {str(e)}")

class FileSegmenter:
    """Funções auxiliares para manipulação de arquivos em blocos."""

    @staticmethod
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
