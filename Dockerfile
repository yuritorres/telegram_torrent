# Use uma imagem base oficial do Python
FROM python:3.9-slim

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# Crie um usuário e grupo não root
RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup appuser

# Copie o arquivo de requisitos primeiro para otimizar o cache de camadas
COPY requirements.txt .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante do código da aplicação para o contêiner
# Assegure que o WORKDIR exista e tenha as permissões corretas antes de copiar
COPY . .

# Mude a propriedade do diretório de trabalho para o novo usuário
RUN chown -R appuser:appgroup /app

# Mude para o usuário não root
USER appuser

# O arquivo .env não deve ser copiado diretamente para a imagem por questões de segurança.
# Considere montar o arquivo .env como um volume ou passá-lo como variáveis de ambiente ao executar o contêiner.

# Comando para executar o script principal quando o contêiner iniciar
CMD ["python", "main.py"]