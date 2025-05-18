# Use uma imagem base oficial do Python
FROM python:3.9-slim

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copie o arquivo de requisitos e instale as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante do código da aplicação para o contêiner
COPY .

# O arquivo .env não deve ser copiado diretamente para a imagem por questões de segurança.
# Considere montar o arquivo .env como um volume ou passá-lo como variáveis de ambiente ao executar o contêiner.

# Comando para executar o script principal quando o contêiner iniciar
CMD ["python", "main.py"]