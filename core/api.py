from django.http import HttpResponse, JsonResponse
from .forms import *
import json, re, traceback,hashlib
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .views import gera_numero_proposta
from datetime import datetime
from django.urls import reverse


def verifica_token(token:str):
    users = User.objects.filter()
    for user in users:
        user_token = hashlib.sha256(user.username.encode()).hexdigest()
        if user_token == token:
            return user
    return None


def valida_recebimento(request, campos_obrigatorios:list, required_method=None, schema:dict=None):
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
    
    if schema:
        data=body
        for campo, tipo in schema.items():
            if not isinstance(data[campo], tipo):
                return JsonResponse({"status": "error", "message": f"Campo '{campo}' deve ser do tipo {tipo}, recebido {type(data[campo])}"}, status=400), None

    return body,usuario_validado

def gera_numero_proposta(user):
    user_atual = user
    hoje = datetime.today()
    propostas_dia = Proposta.objects.filter(usuario_responsavel=user_atual,criacao__gte=hoje.strftime("%Y-%m-%d") ).count()
    hoje_proposta = hoje.strftime("%Y%m%d")
    numero_proposta = f"{hoje_proposta}-{propostas_dia + 1}-{str(user.first_name)[0] if user.first_name else 'q'}"
    return numero_proposta

@csrf_exempt
def cadastrar_cliente(request,):
    campos_obrigatorios = ["nome", "cnpj", "telefone", "cidade", "uf", "nome_responsavel", "email_responsavel", "tratamento_responsavel", "status"]

    body_or_error, usuario_validado  =  valida_recebimento(request, campos_obrigatorios, "POST")
    if isinstance(body_or_error, JsonResponse):
        return body_or_error

    form = ClienteForm(body_or_error)

    if form.is_valid():
        cliente = form.save()
        salva_log(f"Cliente criado: {usuario_validado.username} - API",usuario_validado.username)
        return JsonResponse({"status": "success", "message": "Cliente criado com sucesso!"})
    else:
        return JsonResponse({"status": "error", "message": form.errors}, status=400)
    
@csrf_exempt
def atualizar_cliente(request,):
    campos_obrigatorios = ["nome", "cnpj", "telefone", "cidade", "uf", "nome_responsavel", "email_responsavel", "tratamento_responsavel", "status"]

    body_or_error, usuario_validado  =  valida_recebimento(request, campos_obrigatorios, "POST")
    if isinstance(body_or_error, JsonResponse):
        return body_or_error


    cnpj = re.sub(r"\D+","",body_or_error["cnpj"])

    try:
        cliente = Cliente.objects.get(cnpj=cnpj)
    except:
        return JsonResponse(
            {
                "status": "error",
                "message": "Cliente não encontrado."
            },
            status=400
        )

    form = ClienteForm(body_or_error, instance=cliente)

    if form.is_valid():
        cliente = form.save()
        salva_log(acao=f"Cliente {cliente.nome} atualizado - API", username=usuario_validado.username)
        return JsonResponse({"status": "success", "message": f"Cliente {cliente.nome} atualizado com sucesso!"})
    else:
        return JsonResponse({"status": "error", "message": form.errors}, status=400)
    

@csrf_exempt
def deletar_cliente(request,):
    campos_obrigatorios = ["cnpj", ]

    body_or_error, usuario_validado  =  valida_recebimento(request, campos_obrigatorios, "POST")
    if isinstance(body_or_error, JsonResponse):
        return body_or_error
    
    cnpj = re.sub(r"\D+","",body_or_error["cnpj"])
    
    try:
        cliente = Cliente.objects.get(cnpj=cnpj)
    except:
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
        f"Cliente {cliente.nome} deletado com sucesso! - API",
        usuario_validado.username
    )

    cliente.delete()

    return JsonResponse(
        {"status": "success", "message": "Cliente deletado com sucesso!"}
    )

@csrf_exempt
def criar_proposta(request,):
    campos_obrigatorios = [
        "titulo","nome_do_modelo","cnpj_cliente","tempo_de_contrato_em_meses","valor_dolar","observacoes_equipamento","observacoes_adicionais","observacoes_servicos","servicos","equipamentos","adicionais"
    ]
    schema = {
        "titulo": str,
        "nome_do_modelo": str,
        "cnpj_cliente": str,
        "tempo_de_contrato_em_meses": int,
        "valor_dolar": (int, float),
        "observacoes_equipamento": str,
        "observacoes_adicionais": str,
        "observacoes_servicos": str,
        "servicos": list,
        "equipamentos": list,
        "adicionais": list,
    }

    body_or_error, usuario_validado  =  valida_recebimento(request, campos_obrigatorios, "POST", schema)
    if isinstance(body_or_error, JsonResponse):
        return body_or_error
    
    titulo = body_or_error["titulo"]
    if len(str(titulo).strip()) < 8:
        return JsonResponse({"status": "error", "message": f"O título da proposta deve conter ao menos 8 caracteres"}, status=400)

    nome_do_modelo = body_or_error["nome_do_modelo"]
    modelo_existente = Modelo.objects.filter(titulo=nome_do_modelo)
    if not modelo_existente.exists():
        return JsonResponse({"status": "error", "message": f"Não existe um modelo com o nome -{nome_do_modelo}-"}, status=400)


    cnpj_cliente = re.sub(r"\D+", "", body_or_error["cnpj_cliente"])
    possiveis_clientes = Cliente.objects.filter(cnpj=cnpj_cliente)
    if not possiveis_clientes.exists():
        return JsonResponse({"status": "error", "message": f"Cliente com o cnpj -{cnpj_cliente}- não foi encontrado"}, status=400)


    try:
        proposta = Proposta.objects.create(
            titulo=body_or_error["titulo"],
            cliente=possiveis_clientes[0],
            modelo=body_or_error["nome_do_modelo"],
            numero_proposta=gera_numero_proposta(usuario_validado),
            tempo_de_contrato=body_or_error["tempo_de_contrato_em_meses"],
            valor_dolar=body_or_error["valor_dolar"],
            observacoes_equipamento=body_or_error["observacoes_equipamento"],
            observacoes_adicionais=body_or_error["observacoes_adicionais"],
            observacoes_servicos=body_or_error["observacoes_servicos"],
            tipo_cobranca_equipamento=False ,
            tipo_cobranca_servico=False,
            tipo_cobranca_adicional=False,
            usuario_responsavel=usuario_validado,
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Não foi possível salvar a proposta pois {traceback.format_exc()}"}, status=400)

    for tipo in ["servicos", "equipamentos", "adicionais"]:
        servicos = body_or_error[tipo]
        dict_nomes = {
            "servicos": "Serviço",
            "equipamentos": "Equipamento",
            "adicionais": "Adicional"
        }
        nome_serv = dict_nomes[tipo]
        serv_props_criadas = []
        if servicos:
            for serv in servicos:
                servs = Servico.objects.filter(titulo=serv["titulo"])
                if not servs.exists():
                    proposta.delete()
                    return JsonResponse({"status": "error", "message": f"O {nome_serv} -{serv['titulo']}- não foi encontrado"}, status=400)

                try:
                    serv_prop = ServicoProposta.objects.create(
                        proposta=proposta,
                        quantidade=serv["quantidade"],
                        descricao=servs[0].descricao,
                        preco_unitario=servs[0].valor_servico,
                        tipo= dict_nomes[tipo]
                    )
                    serv_props_criadas.append(serv_prop)
                except Exception as e:
                    proposta.delete()
                    for serv_prop in serv_props_criadas:
                        serv_prop.delete()

                    return JsonResponse({"status": "error", "message": f"Erro desconhecido ao criar Proposta"}, status=400)
    Log.objects.create(
            acao=f"Criação de Proposta com ID {proposta.id}",
            user=usuario_validado
    )
    return JsonResponse( {"status": "success", "message": "Proposta criada com sucesso!"}, status=201)


@csrf_exempt
def baixar_proposta(request ):
    campos_obrigatorios = ["titulo_proposta", ]

    body_or_error, usuario_validado  =  valida_recebimento(request, campos_obrigatorios, "POST")
    if isinstance(body_or_error, JsonResponse):
        return body_or_error
    
    titulo_proposta = body_or_error["titulo_proposta"]
    possiveis_titulos = Proposta.objects.filter(titulo=titulo_proposta)
    if not possiveis_titulos.exists():
        return JsonResponse({"status": "error", "message": f"Proposta desejada não foi encontrada"}, status=400)
    
    url = reverse("download_docx")
    url_completa = f"{url}?id_proposta={possiveis_titulos[0].id}&formato=pdf"
    return JsonResponse( {"status": "success", "message": url_completa}, status=200)

# deletar_proposta
# baixar_proposta



