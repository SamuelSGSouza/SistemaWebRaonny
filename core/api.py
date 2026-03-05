from django.http import HttpResponse, JsonResponse
from .forms import *
import json, re
from django.contrib.auth.models import User
import hashlib
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

def verifica_token(token:str):
    users = User.objects.filter()
    for user in users:
        user_token = hashlib.sha256(user.username.encode()).hexdigest()
        if user_token == token:
            return user
    return None


def valida_recebimento(request, campos_obrigatorios:list, required_method=None):
    if required_method:
        if required_method != request.method:
            return JsonResponse({"status": "error", "message": f"Método inválido."}, status=400), None
    try:
        body = json.loads(request.body)
    except:
        return JsonResponse({"status": "error", "message": f"O body recebido não foi um json."}, status=400), None

    token = request.headers.get("token")
    if not token:
        return JsonResponse({"status": "error", "message": f"Token de autorização não encontrado ou inválido."}, status=400), None

    usuario_validado = verifica_token(token)
    if not usuario_validado:
        return JsonResponse({"status": "error", "message": f"Token passado não corresponde a nenhum usuário do sistema"}, status=400), None


    campos_obrigatorios = campos_obrigatorios
    for c in campos_obrigatorios:
        if c not in body.keys():
            return JsonResponse({"status": "error", "message": f" O campo obrigatório {c} não foi encontrado na requisição."}, status=400), None

    return body,usuario_validado

@csrf_exempt
def cadastrar_cliente(request,):
    campos_obrigatorios = ["nome", "cnpj", "telefone", "cidade", "uf", "nome_responsavel", "email_responsavel", "tratamento_responsavel", "status"]

    body_or_error, usuario_validado  =  valida_recebimento(request, campos_obrigatorios, "POST")
    if isinstance(body_or_error, JsonResponse):
        return body_or_error

    form = ClienteForm(body_or_error)

    if form.is_valid():
        cliente = form.save()
        salva_log(f"Usuário criado: {usuario_validado.username}",usuario_validado.username)
        return JsonResponse({"status": "success", "message": "Usuário criado com sucesso!"})
    else:
        return JsonResponse({"status": "error", "message": form.errors}, status=400)
    
@csrf_exempt
def deletar_cliente(request,):
    campos_obrigatorios = ["cnpj", ]

    body_or_error, usuario_validado  =  valida_recebimento(request, campos_obrigatorios, "POST")
    if isinstance(body_or_error, JsonResponse):
        return body_or_error
    
    cnpj = re.sub(r"\D+","",body_or_error["cnpj"])

    cliente = Cliente.objects.filter(cnpj=cnpj)
    if not cliente.exists():
        return JsonResponse(
            {
                "status": "error",
                "message": "Cliente não encontrado."
            },
            status=400
        )

    propostas = Proposta.objects.filter(cliente=cliente)
    if propostas.exists():
        return JsonResponse(
            {
                "status": "error",
                "message": "Não foi possível excluir o cliente pois ainda existem propostas em seu nome."
            },
            status=400
        )

    salva_log(
        f"Exclusão de Cliente {cliente.nome}",
        usuario_validado.username
    )

    cliente.delete()

    return JsonResponse(
        {"status": "success", "message": "Cliente deletado com sucesso!"}
    )

# atualizar_cliente

# deletar_cliente

# criar_proposta

# editar_proposta
# deletar_proposta
# baixar_proposta



