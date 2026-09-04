import os
import time
import logging
import requests
import jwt
from datetime import datetime, timezone

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | [legacy-simulator] %(message)s'
)
logger = logging.getLogger("legacy-simulator")

# Configurações via variáveis de ambiente
CAMEL_URL = os.getenv("CAMEL_URL", "http://camel-middleware:8080/pacientes")
JWT_SECRET = os.getenv("JWT_SECRET", "minha-chave-secreta-super-complexa-para-o-portfolio")
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "10"))
RUN_ONCE = os.getenv("RUN_ONCE", "false").lower() == "true"

# Dados simulados de pacientes (em um legado real viria de um banco Oracle/DB2)
PATIENTS_DATA = [
    {
        "nomeCompleto": "Etevaldo Antunes",
        "documento": "001223098BE098",
        "dataNasc": "1990-01-15",
        "codMunicipio": "3550308"
    },
    {
        "nomeCompleto": "Carlos João Pedro Candiatilo",
        "documento": "001223098LA098",
        "dataNasc": "1985-07-22",
        "codMunicipio": "3304557"
    },
    {
        "nomeCompleto": "José Bala",
        "documento": "001223098UG098",
        "dataNasc": "1978-12-03",
        "codMunicipio": "4106902" 
    },
]


# Caminho para a chave privada dentro do container
PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH", "legacy-private.pem")

def generate_jwt() -> str:
    """Gera um JWT assinado com RSA (RS256)"""
    # Lê a chave privada do arquivo
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        private_key = key_file.read()

    payload = {
        "sub": "legacy-system-v1",
        "iss": "legacy-system",              # Deve bater com mp.jwt.verify.issuer
        "aud": "camel-middleware",           # Deve bater com mp.jwt.verify.audiences
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(datetime.now(timezone.utc).timestamp()) + 300,
        "system": "legacy-core"
    }
    
    # Usa o algoritmo RS256 e a chave privada
    return jwt.encode(payload, private_key, algorithm="RS256")


def build_xml_payload(patient: dict) -> str:
    """Converte os dados do paciente em XML (formato do legado)"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<paciente>
    <nomeCompleto>{patient['nomeCompleto']}</nomeCompleto>
    <documento>{patient['documento']}</documento>
    <dataNasc>{patient['dataNasc']}</dataNasc>
    <codMunicipio>{patient['codMunicipio']}</codMunicipio>
</paciente>"""


def send_patient(patient: dict) -> None:
    """Envia um paciente para o Camel Middleware"""
    request_id = f"LEG-{int(time.time() * 1000)}"
    xml_payload = build_xml_payload(patient)
    token = generate_jwt()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/xml",
        "X-Request-Id": request_id
    }

    logger.info(f"[{request_id}]  Enviando paciente: {patient['nomeCompleto']}")
    logger.debug(f"[{request_id}] Payload XML:\n{xml_payload}")

    try:
        response = requests.post(CAMEL_URL, data=xml_payload, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            logger.info(f"[{request_id}] ✅ Sucesso! Resposta: {response.text.strip()}")
        elif response.status_code == 401:
            logger.error(f"[{request_id}] Não autorizado (JWT inválido ou expirado)")
        elif response.status_code == 400:
            logger.error(f"[{request_id}] Erro de validação: {response.text}")
        else:
            logger.error(f"[{request_id}] Erro {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        logger.error(f"[{request_id}] Não foi possível conectar ao Camel Middleware em {CAMEL_URL}")
    except requests.exceptions.Timeout:
        logger.error(f"[{request_id}] Timeout ao conectar com o Camel Middleware")
    except Exception as e:
        logger.error(f"[{request_id}] Erro inesperado: {str(e)}")


def main():
    """Loop principal do simulador legado"""
    logger.info("=" * 60)
    logger.info("Legacy Simulator iniciado")
    logger.info(f" Destino: {CAMEL_URL}")
    logger.info(f" Intervalo: {INTERVAL_SECONDS}s")
    logger.info(f" Modo: {'Única execução' if RUN_ONCE else 'Contínuo'}")
    logger.info("=" * 60)

    patient_index = 0
    
    while True:
        patient = PATIENTS_DATA[patient_index % len(PATIENTS_DATA)]
        send_patient(patient)
        patient_index += 1

        if RUN_ONCE:
            logger.info("✅ Execução única finalizada.")
            break

        logger.info(f"⏳ Aguardando {INTERVAL_SECONDS}s para próximo envio...\n")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()