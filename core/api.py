from django.http import HttpResponse, JsonResponse
from .forms import *
import json
from django.contrib.auth.models import User
import hashlib


def verifica_token(token:str):
    users = User.objects.filter()
    for user in users:
        user_token = hashlib.sha256(user.username.encode()).hexdigest()
        if user_token == token:
            return user
    return None

def cadastrar_cliente(request,):
    try:
        body = json.loads(request.body)
    except:
        return JsonResponse({"status": "error", "message": f"O body recebido não foi um json."}, status=400)

    token = request.headers.get("token")
    if not token:
        return JsonResponse({"status": "error", "message": f"Token de autorização não encontrado ou inválido."}, status=400)

    usuario_validado = verifica_token(token)
    if not usuario_validado:
        return JsonResponse({"status": "error", "message": f"Token passado não corresponde a nenhum usuário do sistema"}, status=400)


    campos_obrigatorios = ["nome", "cnpj", "telefone", "cidade", "uf", "nome_responsavel", "email_responsavel", "tratamento_responsavel", "status"]
    for c in campos_obrigatorios:
        if c not in body.keys():
            return JsonResponse({"status": "error", "message": f" O campo obrigatório {c} não foi encontrado na requisição."}, status=400)

    form = ClienteForm(body)

    if form.is_valid():
        cliente = form.save()
        return JsonResponse({"status": "success", "message": "Usuário criado com sucesso!"})
    else:
        return JsonResponse({"status": "error", "message": form.errors}, status=400)
    

    # body = {
    #     "nome": "Empresa X",
    #     "cnpj": "12.345.678/0001-99",
    #     "telefone": "47999999999",
    #     "cidade": "Jaraguá do Sul",
    #     "uf": "SC",
    #     "nome_responsavel": "João",
    #     "email_responsavel": "joao@email.com",
    #     "tratamento_responsavel": "SR",
    #     "status": "ATIVO"
    #     }
    


# atualizar_cliente

# deletar_cliente

# criar_proposta

# editar_proposta
# deletar_proposta
# baixar_proposta



