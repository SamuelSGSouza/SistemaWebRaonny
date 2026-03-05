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
        salva_log(f"Usuário criado: {usuario_validado.username}",usuario_validado.username)
        return JsonResponse({"status": "success", "message": "Usuário criado com sucesso!"})
    else:
        return JsonResponse({"status": "error", "message": form.errors}, status=400)
    
def deletar_usuario(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método não permitido."}, status=405)

    try:
        body = json.loads(request.body)
    except:
        return JsonResponse({"status": "error", "message": "O body recebido não foi um json."}, status=400)

    token = request.headers.get("token")
    if not token:
        return JsonResponse({"status": "error", "message": "Token de autorização não encontrado ou inválido."}, status=400)

    usuario_validado = verifica_token(token)
    if not usuario_validado:
        return JsonResponse({"status": "error", "message": "Token passado não corresponde a nenhum usuário do sistema."}, status=400)

    if "username" not in body:
        return JsonResponse({"status": "error", "message": "O campo obrigatório username não foi encontrado na requisição."}, status=400)

    try:
        usuario = User.objects.get(username=body["username"])
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Usuário não encontrado."}, status=404)

    Log.objects.create(
        acao=f"Exclusão de Usuário {usuario.username}",
        user=usuario_validado.username
    )

    usuario.delete()

    return JsonResponse({"status": "success", "message": "Usuário deletado com sucesso!"})
    
    


# atualizar_cliente

# deletar_cliente

# criar_proposta

# editar_proposta
# deletar_proposta
# baixar_proposta



