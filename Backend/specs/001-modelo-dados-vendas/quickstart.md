# Quickstart de Validacao do MVP

## Pre-requisitos

- Python 3.10+.
- Ambiente virtual ativo.
- Dependencias instaladas com `pip install -r requirements.txt`.

## Validacao automatizada

Na raiz do repositorio:

```powershell
pytest -q
```

Resultado esperado: testes unitarios e de integração verdes, incluindo constraints, calculo de credito, classificacao de vencimento/atraso, isolamento por cliente e bloqueio de escrita.

## Execucao local

Antes de iniciar a API pela primeira vez, a partir do diretorio `Backend`, ingira o playbook:

```powershell
python -m app.services.chromadb_service
```

O comando e seguro para repetir. Se o conteudo do playbook mudar, rode-o novamente para atualizar o indice. Para recriar a colecao explicitamente, use `python -m app.services.chromadb_service --force`.

O Chroma usa o embedding padrao `all-MiniLM-L6-v2`; a primeira ingestao pode baixar o modelo e exigir acesso a internet. A API expoe `GET /health/knowledge-base`, que retorna `ready` quando o indice corresponde ao Markdown atual e `503` quando precisa ser preparado/atualizado. Perguntas sobre politicas executam a recuperacao antes da chamada ao modelo; se nao houver trechos utilizaveis, o agente e instruido a nao afirmar regras nao verificadas.

```powershell
cd Backend
```

```powershell
uvicorn app.main:app --reload
```

Abrir `/docs` para verificar o contrato OpenAPI e executar as consultas GET descritas em [contracts/openapi.yaml](contracts/openapi.yaml).

## Cenarios minimos

1. Criar fixture de um cliente ativo com limite de `10000.00`, uma fatura aberta de `2500.00` e uma fatura vencida de `1000.00`; consultar credito e verificar exposição `3500.00` e saldo `6500.00`.
2. Criar pedido confirmado com um item; consultar o pedido e verificar total, status e previsão.
3. Criar faturas paga, cancelada, vencendo hoje e vencida; consultar vencidas e verificar que somente a última aparece.
4. Tentar qualquer método de escrita através do agente/rotas de consulta; verificar bloqueio e ausência de alteração no banco.
5. Consultar cliente inexistente, pedido inexistente e nome ambíguo; verificar respostas explícitas e ausência de vazamento de registros.

## Critério de aceite do MVP

Todos os cenarios acima devem passar, o banco deve ser criado pela migração inicial e nenhuma consulta deve conter SQL puro. O tempo de resposta de credito deve ser medido com uma fixture representativa e permanecer abaixo de 2 segundos em pelo menos 95% das execuções.
