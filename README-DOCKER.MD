# 1. Derruba tudo

docker compose down

# 2. Reconstrói o middleware ignorando o cache antigo

docker compose build --no-cache camel-middleware

# Reconstrói ambos os serviços

docker compose up -d --build camel-middleware modern-api

# 3. Sobe tudo em segundo plano

docker compose up -d

# Ver logs de todos serviços

docker compose logs -f

# Ver logs de um unico serviço

docker compose logs -f camel-middleware

# Verificar as mensagens a consumir da DLQ

docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic camel-dlq-pacientes --from-beginning

# Conferir a configuração feita no docker-compose file

docker compose config
