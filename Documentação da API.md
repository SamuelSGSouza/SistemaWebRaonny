# Documentação da API

## Visão Geral

Esta documentação detalha os endpoints da API para gerenciamento de clientes e propostas. A API é construída com Django e utiliza autenticação baseada em token.

## Autenticação

A autenticação é realizada através de um token enviado no cabeçalho `token` de cada requisição. O token é um hash SHA256 do nome de usuário.

```python
def verifica_token(token:str):
    users = User.objects.filter()
    for user in users:
        user_token = hashlib.sha256(user.username.encode()).hexdigest()
        if user_token == token:
            return user
    return None
```

## Funções Auxiliares

### `valida_recebimento(request, campos_obrigatorios:list, required_method=None, schema:dict=None)`

Esta função valida as requisições recebidas, verificando o método HTTP, a presença de um token válido, os campos obrigatórios no corpo da requisição e o tipo de dado de cada campo.

### `gera_numero_proposta(user)`

Esta função gera um número de proposta único com base no usuário e na data atual.

## Endpoints

A seguir, são detalhados os endpoints disponíveis na API.

### Clientes

#### `POST /cadastrar_cliente`

Cadastra um novo cliente no sistema.

**Corpo da Requisição:**

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `nome` | string | Sim | Nome do cliente. |
| `cnpj` | string | Sim | CNPJ do cliente. |
| `telefone` | string | Sim | Telefone de contato do cliente. |
| `cidade` | string | Sim | Cidade do cliente. |
| `uf` | string | Sim | UF do cliente. |
| `nome_responsavel` | string | Sim | Nome do responsável pelo cliente. |
| `email_responsavel` | string | Sim | Email do responsável. |
| `tratamento_responsavel` | string | Sim | Forma de tratamento do responsável (e.g., Sr., Sra.). |
| `status` | string | Sim | Status do cliente. |

**Exemplo de Resposta (Sucesso):**

```json
{
    "status": "success",
    "message": "Cliente criado com sucesso!"
}
```

#### `POST /atualizar_cliente`

Atualiza os dados de um cliente existente com base no CNPJ.

**Corpo da Requisição:**

Mesmo corpo da requisição de `cadastrar_cliente`.

**Exemplo de Resposta (Sucesso):**

```json
{
    "status": "success",
    "message": "Cliente {nome_do_cliente} atualizado com sucesso!"
}
```

#### `POST /deletar_cliente`

Deleta um cliente com base no CNPJ, desde que não haja propostas associadas a ele.

**Corpo da Requisição:**

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `cnpj` | string | Sim | CNPJ do cliente a ser deletado. |

**Exemplo de Resposta (Sucesso):**

```json
{
    "status": "success",
    "message": "Cliente deletado com sucesso!"
}
```

### Propostas

#### `POST /criar_proposta`

Cria uma nova proposta no sistema.

**Corpo da Requisição:**

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `titulo` | string | Sim | Título da proposta (mínimo 8 caracteres). |
| `nome_do_modelo` | string | Sim | Nome de um modelo de proposta existente. |
| `cnpj_cliente` | string | Sim | CNPJ do cliente associado à proposta. |
| `tempo_de_contrato_em_meses` | integer | Sim | Duração do contrato em meses. |
| `valor_dolar` | float/integer | Sim | Valor do dólar a ser utilizado na proposta. |
| `observacoes_equipamento` | string | Sim | Observações sobre os equipamentos. |
| `observacoes_adicionais` | string | Sim | Observações adicionais. |
| `observacoes_servicos` | string | Sim | Observações sobre os serviços. |
| `servicos` | list | Sim | Lista de objetos de serviço. |
| `equipamentos` | list | Sim | Lista de objetos de equipamento. |
| `adicionais` | list | Sim | Lista de objetos adicionais. |

**Exemplo de Resposta (Sucesso):**

```json
{
    "status": "success",
    "message": "Proposta criada com sucesso!"
}
```

#### `POST /baixar_proposta`

Retorna a URL para download de uma proposta em formato PDF.

**Corpo da Requisição:**

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `titulo_proposta` | string | Sim | Título da proposta a ser baixada. |

**Exemplo de Resposta (Sucesso):**

```json
{
    "status": "success",
    "message": "{url_para_download}"
}
```

#### `POST /deletar_proposta`

Deleta uma proposta com base no seu título.

**Corpo da Requisição:**

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `titulo_proposta` | string | Sim | Título da proposta a ser deletada. |

**Exemplo de Resposta (Sucesso):**

```json
{
    "status": "success",
    "message": "Proposta - {titulo_da_proposta}- deletada com sucesso"
}
```
