# ==============================================================================
# Estágio 1: Build da aplicação com Maven e Quarkus
# ==============================================================================
FROM maven:3.9.6-eclipse-temurin-17 AS build
WORKDIR /build

# 1. Copia o pom.xml e baixa as dependências
COPY pom.xml .
RUN mvn dependency:go-offline

# 2. Cria a estrutura de diretórios padrão do Quarkus Camel
RUN mkdir -p src/main/resources/camel
RUN mkdir -p src/main/resources/schema

# 3. Copia os arquivos para os locais EXATOS de auto-descoberta
COPY application.properties src/main/resources/
COPY public.pem src/main/resources/
COPY paciente-route.camel.yaml src/main/resources/camel/  
COPY schema/paciente.xsd src/main/resources/schema/

# 4. Compila o projeto
RUN mvn clean package -DskipTests

# ==============================================================================
# Estágio 2: Imagem final otimizada (JVM)
# ==============================================================================
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app

COPY --from=build /build/target/quarkus-app/lib/ /app/lib/
COPY --from=build /build/target/quarkus-app/*.jar /app/
COPY --from=build /build/target/quarkus-app/app/ /app/app/
COPY --from=build /build/target/quarkus-app/quarkus/ /app/quarkus/

EXPOSE 8080
ENV JAVA_OPTS="-Xms128m -Xmx256m"

ENTRYPOINT ["java", "-jar", "/app/quarkus-run.jar"]