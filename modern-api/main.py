import os
import random
import logging
import re
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel, field_validator
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


# Configuração de Logs (essencial para produção)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("modern-api")

app = FastAPI(
    title="Modern Patients API",
    description="API moderna para cadastro de pacientes (consome JSON)",
    version="1.0.0"
)

# Variável de ambiente para simular falhas (testar a DLQ do Kafka)
SIMULATE_FAILURE = os.getenv("SIMULATE_FAILURE", "false").lower() == "true"
FAILURE_RATE = float(os.getenv("FAILURE_RATE", "0.5"))  # 50% de chance de falha

# "Banco de dados" em memória (em produção seria PostgreSQL, MongoDB, etc)
PATIENTS_DB = []


class Patient(BaseModel):
    """Schema de validação do paciente (JSON)"""
    nome: str
    bi: str
    nascimento: str
    municipio_codigo: str

    @field_validator("bi")
    @classmethod
    def validate_bi(cls, v: str) -> str:
        # Remove espaços em branco e garante maiúsculas
        v = v.strip().upper()

        # Valida tamanho exato de 14 caracteres
        if len(v) != 14:
            raise ValueError("O BI deve ter exatamente 14 caracteres.")

        # Expressão regular: 9 dígitos, 2 letras maiúsculas, 3 dígitos (Ex: 000842456BO019)
        padrao_bi = r"^\d{9}[A-Z]{2}\d{3}$"
        if not re.match(padrao_bi, v):
            raise ValueError(
            "Formato de BI inválido. Deve conter 9 dígitos, 2 letras e 3"
            " dígitos (ex: 123456789AA123)."
        )

        return v

    @field_validator("municipio_codigo")
    @classmethod
    def validate_municipioCode(cls, v: str) -> str:
        v = v.strip()

        # Valida tamanho exato de 7 caracteres
        if len(v) != 7:
            raise ValueError("O código do município deve ter exatamente 7 dígitos.")

        # Valida se são estritamente dígitos numéricos
        if not v.isdigit():
            raise ValueError("O código do município deve conter apenas números.")

        return v


@app.get("/health")
def health_check():
    """Endpoint para healthcheck do Kubernetes/Docker"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/pacientes")
def list_patients():
    """Lista todos os pacientes cadastrados (para debug)"""
    return {"total": len(PATIENTS_DB), "pacientes": PATIENTS_DB}


# Handler de exceções de validação
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Captura erros de validação do Pydantic e retorna detalhes"""
    logger.error(f" Erro de validação Pydantic: {exc.errors()}")
    logger.error(f" Corpo da requisição: {await request.body()}")
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors(), "body": (await request.body()).decode()},
    )
    
    
# Handler de exceções genéricas
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    body = await request.body()
    logger.error(f" Erro genérico: {str(exc)}")
    logger.error(f" Body recebido: {body.decode('utf-8', errors='replace')}")
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "received_body": body.decode('utf-8', errors='replace')
        },
    )

@app.post("/api/pacientes", status_code=201)
def create_patient(
    patient: Patient,
    x_request_id: Optional[str] = Header(None, alias="X-Request-Id")
):
    """
    Cadastra um novo paciente recebido via JSON.
    Simula falhas aleatórias para testar a Dead Letter Queue do Kafka.
    """
    request_id = x_request_id or "no-request-id"
    logger.info(f"[{request_id}] Recebendo paciente: {patient.nome} | bi: {patient.bi}")
    
    # VERIFICAÇÃO DE IDEMPOTÊNCIA: CPF já existe?
    if patient.bi in PATIENTS_DB:
        logger.warning(f"[{request_id}] ⚠️ Paciente {patient.bi} já cadastrado. Ignorando duplicata.")
        # Retorna 200 OK (não 201 Created) para indicar que a operação foi idempotente
        return JSONResponse(
            status_code=200,
            content={
                "message": "Paciente já processado.",
                "patient": PATIENTS_DB[patient.bi]
            }
        )

    # Simulação de falha controlada para testar a DLQ
    if SIMULATE_FAILURE:
        if random.random() < FAILURE_RATE:
            logger.error(f"[{request_id}] ❌ Falha simulada ao processar paciente {patient.bi}")
            raise HTTPException(
                status_code=500,
                detail="Erro interno simulado - mensagem será enviada para a DLQ"
            )

    # "Persiste" o paciente
    patient_data = patient.model_dump()
    patient_data["created_at"] = datetime.utcnow().isoformat()
    PATIENTS_DB.append(patient_data)

    logger.info(f"[{request_id}] ✅ Paciente {patient.bi} cadastrado com sucesso!")
    return {
        "message": "Paciente cadastrado com sucesso",
        "patient": patient_data
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9005)