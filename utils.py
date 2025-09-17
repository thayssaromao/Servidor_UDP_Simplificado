import os

class FileChecker:
    def __init__(self, filename):
        self.filename = filename

    def file_exists(self):
        return os.path.exists(self.filename)

    def file_size_mb(self):
        if not self.file_exists():
            return 0
        size_bytes = os.path.getsize(self.filename)
        return size_bytes / (1024 * 1024)

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

# checker = FileChecker('files/arquivo_grande.txt')
# print(f"{checker.file_exists()}")
# print(f"{checker.file_size_mb():.2f} MB")
