from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.views.generic import TemplateView, ListView, UpdateView, CreateView
from .models import *
from django.contrib.auth.models import User
from datetime import datetime
from django.utils import timezone
from django.db.models import Q, CharField, TextField
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
import re, os
from django.db import transaction
from motores.pptx_v1_3 import gerador_modelo_2 as motor_2
from django.http import HttpResponse, JsonResponse
from io import BytesIO
from .forms import *
from django.core import serializers
import json
from django.contrib.auth.mixins import LoginRequiredMixin
import hashlib



@csrf_protect
def login_view(request):
    """
    View de login simples usando o sistema padrão de autenticação do Django.
    """
    if request.user.is_authenticated:
        return redirect('home') # ajuste para sua rota principal


    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')


        user = authenticate(request, username=username, password=password)


        if user is not None:
            login(request, user)


            # tempo limite da sessão (em segundos)
            request.session.set_expiry(getattr(settings, 'SESSION_COOKIE_AGE', 3600))


            return redirect('home')
        else:
            messages.error(request, 'Usuário ou senha inválidos')


    return render(request, 'auth/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

class Home(LoginRequiredMixin,ListView):
    model = Log
    context_object_name = "logs"
    paginate_by = 500
    ordering = ["-momento"]
    template_name = "home.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        search_value = (
            self.request.POST.get("search_value")
            or self.request.GET.get("search_value")
        )

        if search_value:
            filtros = Q()

            for field in self.model._meta.fields:
                if isinstance(field, (CharField, TextField)):
                    filtros |= Q(**{f"{field.name}__icontains": search_value})

            queryset = queryset.filter(filtros)

        return queryset

    def post(self, request, *args, **kwargs):
        # permite POST funcionar como GET
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["total_users"] = User.objects.count()
        ctx["propostas_ativas"] = Proposta.objects.filter(status="ATIVA").count()
        ctx["propostas"] = Proposta.objects.count()

        hoje = timezone.now().date()
        ctx["logs_hoje"] = Log.objects.filter(momento__date=hoje).count()

        # mantém o valor pesquisado no template
        ctx["search_value"] = (
            self.request.POST.get("search_value")
            or self.request.GET.get("search_value")
            or ""
        )
        ctx["home_active"] = "active"

        return ctx
    
class PropostasView(LoginRequiredMixin, ListView):
    model = Proposta
    context_object_name = "propostas"
    paginate_by = 500
    ordering = ["-atualizacao"]
    template_name = "propostas.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        # pega search_value tanto do POST quanto do GET (fallback)
        search_value = (
            self.request.POST.get("search_value")
            or self.request.GET.get("search_value")
        )

        if search_value:
            filtros = Q()

            # percorre todos os campos do model
            for field in self.model._meta.fields:
                # filtra apenas campos de texto
                if isinstance(field, (CharField, TextField)):
                    filtros |= Q(**{f"{field.name}__icontains": search_value})

            queryset = queryset.filter(filtros)

        return queryset

    def post(self, request, *args, **kwargs):
        # permite POST funcionar como GET na ListView
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["propostas_ativas"] = Proposta.objects.filter(status="ATIVA").count()
        ctx["propostas_suspensas"] = Proposta.objects.filter(status="SUSPENSA").count()
        ctx["propostas_rejeitadas"] = Proposta.objects.filter(status="REJEITADA").count()
        ctx["total_propostas"] = Proposta.objects.count()

        # mantém o valor pesquisado no template
        ctx["search_value"] = (
            self.request.POST.get("search_value")
            or self.request.GET.get("search_value")
            or ""
        )
        ctx["propostas_active"] = "active"
        return ctx
    
class PrePropostaView(LoginRequiredMixin, TemplateView):
    template_name = "pre_proposta.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["clientes"] = Cliente.objects.all()
        ctx["modelos"] = Modelo.objects.all()

        # mantém dados caso volte com erro
        ctx["dados"] = self.request.POST or self.request.GET
        ctx["propostas_active"] = "active"
        return ctx

    def post(self, request, *args, **kwargs):
        titulo = request.POST.get("titulo")
        modelo = request.POST.get("modelo")
        cnpj = request.POST.get("cliente")
        ctx = self.get_context_data()
        ctx["titulo"] = titulo
        ctx["modelo"] = modelo
        ctx["cnpj"] = cnpj
        print("Título: ", titulo)

        # valida se o CNPJ existe
        cliente_existe = Cliente.objects.filter(cnpj=cnpj).exists()
        modelo_existe = Modelo.objects.filter(titulo=modelo).exists()

        if not cliente_existe:
            messages.error(request, "Cliente com o CNPJ informado não foi encontrado.")
            return render(request, self.template_name,context=ctx )
        if not modelo_existe:
            messages.error(request, "Modelo com o título informado não foi encontrado.")
            return render(request, self.template_name,context=ctx )

        # se existir, redireciona para a view de proposta
        url = (
            reverse("criar_proposta")
            + f"?titulo={titulo}&modelo={modelo}&cliente={cnpj}"
        )
        return redirect(url)
    
def lista_dados(request):
    tipo = request.GET.get("tipo").replace("equipamento", "Equipamento").replace("adicional", "Adicional").replace("servico", "Serviço")
    print(f"Tipo: {tipo}")
    servicos = Servico.objects.filter(status="ATIVA", tipo=tipo)
    servicos_json = serializers.serialize("json", servicos)
    return HttpResponse(servicos_json, content_type="application/json")


class PropostaCreateView(LoginRequiredMixin,TemplateView):
    template_name = "criar_proposta.html"

    def gera_numero_proposta(self, ):
        user_atual = self.request.user
        hoje = datetime.today()
        propostas_dia = Proposta.objects.filter(usuario_responsavel=user_atual,criacao__gte=hoje.strftime("%Y-%m-%d") ).count()
        hoje_proposta = hoje.strftime("%Y%m%d")
        numero_proposta = f"{hoje_proposta}-{propostas_dia + 1}-{str(self.request.user.first_name)[0] if self.request.user.first_name else 'q'}"
        return numero_proposta

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        pre_proposta = self.request.GET
        ctx["titulo"] = pre_proposta.get("titulo")
        ctx["modelo"] = Modelo.objects.filter(titulo=pre_proposta.get("modelo"))[0]
        ctx["cliente"] = pre_proposta.get("cliente")

        cliente = Cliente.objects.filter(cnpj=ctx["cliente"]).first()
        ctx["nome_cliente"] = cliente.nome if cliente else ""

        servicos = Servico.objects.filter(status="ATIVA", tipo="Serviço")
        servicos_json = serializers.serialize('json', servicos)
        servicos_list = list(servicos.values('id', 'titulo', 'descricao', 'valor_servico', 'tipo', 'status'))
        servicos_json = json.dumps(servicos_list)
        ctx["servicos_json"] = servicos_json

        ctx["blocos"] = []
        ctx["form"] = ServicoCreateForm
        ctx["propostas_active"] = "active"

        if ctx["modelo"].numero_pagina_servicos > 0:
            ctx["blocos"].append("servico") 

        if ctx["modelo"].numero_pagina_adicionais > 0:
            ctx["blocos"].append("adicional") 

        if ctx["modelo"].numero_pagina_equipamentos > 0:
            ctx["blocos"].append("equipamento") 

        return ctx

    @transaction.atomic
    def post(self, *args, **kwargs):
        data = self.request.POST
        
        items = {
            "Serviço": eval(data.get("servicos_selecionados", "[]")),
            "Equipamento": eval(data.get("equipamentos_selecionados", "[]")),
            "Adicional": eval(data.get("adicionals_selecionados", "[]"))
        }

        tipo_cobranca_equipamento = self.request.POST.get("tipo_cobranca_equipamento",None)
        tipo_cobranca_servico = self.request.POST.get("tipo_cobranca_servico",None)
        tipo_cobranca_adicional = self.request.POST.get("tipo_cobranca_adicional", None)
        
        cliente = Cliente.objects.get(cnpj=data.get("cliente"))

        proposta = Proposta.objects.create(
            titulo=data.get("titulo"),
            cliente=cliente,
            modelo=data.get("modelo"),
            numero_proposta=self.gera_numero_proposta(),
            tempo_de_contrato=data.get("tempo_de_contrato"),
            valor_dolar=data.get("valor_dolar"),
            observacoes_equipamento=data.get("observacoes_equipamento", ""),
            observacoes_adicionais=data.get("observacoes_adicional", ""),
            observacoes_servicos=data.get("observacoes_servico", ""),
            tipo_cobranca_equipamento=tipo_cobranca_equipamento == "on" ,
            tipo_cobranca_servico=tipo_cobranca_servico == "on" ,
            tipo_cobranca_adicional=tipo_cobranca_adicional == "on",
            usuario_responsavel=self.request.user,
        )

        # --- Parse dinâmico dos serviços ---
        servicos = {}

        for key, value in data.items():
            match = re.match(r"servicos\[(\d+)\]\[(\w+)\]", key)
            if not match or not value:
                continue

            index, field = match.groups()
            servicos.setdefault(index, {})[field] = value

        for tipo, lista in items.items():
            for servico in lista:
                serv_data = Servico.objects.get(id=servico["id"])
                preco_unitario = serv_data.valor_servico
                descricao = serv_data.descricao
                quantidade = int(servico["quantidade"])
                ServicoProposta.objects.create(
                    proposta=proposta,
                    quantidade=quantidade,
                    descricao=descricao,
                    preco_unitario=preco_unitario,
                    tipo= tipo
                )
        Log.objects.create(
            acao=f"Criação de Proposta com ID {proposta.id}",
            user=self.request.user.username
        )

        

        #gerando o arquivo da proposta
        

        return redirect("propostas") 



@require_POST
def deletar_proposta(request, pk):
    proposta = get_object_or_404(Proposta, pk=pk)
    
    Log.objects.create(
        acao = f"Exclusão de Proposta: {proposta.titulo}",
        user = request.user.username
    )
    proposta.delete()
    return redirect("propostas")

### CLIENTES ###
class ClientesView(LoginRequiredMixin,ListView):
    model = Cliente
    context_object_name = "clientes"
    paginate_by = 40
    ordering = ["-atualizacao"]
    template_name = "clientes.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        # pega search_value tanto do POST quanto do GET (fallback)
        search_value = (
            self.request.POST.get("search_value")
            or self.request.GET.get("search_value")
        )

        if search_value:
            filtros = Q()

            # percorre todos os campos do model
            for field in self.model._meta.fields:
                # filtra apenas campos de texto
                if isinstance(field, (CharField, TextField)):
                    filtros |= Q(**{f"{field.name}__icontains": search_value})

            queryset = queryset.filter(filtros)

        return queryset

    def post(self, request, *args, **kwargs):
        # permite POST funcionar como GET na ListView
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["clientes_ativas"] = Cliente.objects.filter(status="ATIVA").count()
        ctx["clientes_suspensas"] = Cliente.objects.filter(status="SUSPENSA").count()
        ctx["clientes_rejeitadas"] = Cliente.objects.filter(status="REJEITADA").count()
        ctx["total_clientes"] = Cliente.objects.count()

        # mantém o valor pesquisado no template
        ctx["search_value"] = (
            self.request.POST.get("search_value")
            or self.request.GET.get("search_value")
            or ""
        )
        ctx["clientes_active"] = "active"

        return ctx
    
class ClienteCreateView(LoginRequiredMixin,CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "criar_clientes.html"
    success_url = reverse_lazy("clientes")

    def form_valid(self, form):
        response = super().form_valid(form)

        Log.objects.create(
            acao="Cliente criado",
            user=self.request.user.username if self.request.user.is_authenticated else "Sistema"
        )

        return response
    
    def get_context_data(self, **kwargs):
        ctx =  super().get_context_data(**kwargs)
        ctx["clientes_active"] = "active"
        return ctx

class ClienteUpdateView(LoginRequiredMixin,UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "criar_clientes.html"
    success_url = reverse_lazy("clientes")

    def form_valid(self, form):
        response = super().form_valid(form)

        Log.objects.create(
            acao="Cliente atualizado",
            user=self.request.user.username if self.request.user.is_authenticated else "Sistema"
        )

        return response
    
    def get_context_data(self, **kwargs):
        ctx =  super().get_context_data(**kwargs)
        ctx["clientes_active"] = "active"

        cliente = ctx["object"]
        if cliente:
            ctx["propostas"] = Proposta.objects.filter(cliente=cliente)
        return ctx
    
@require_POST
def deletar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    propostas = Proposta.objects.filter(cliente=cliente)
    if propostas.exists():
        messages.error(request, 'Não foi possível excluir o cliente pois ainda existem propostas em seu nome.')
        return redirect("clientes")
    Log.objects.create(
        acao = f"Exclusão de Cliente {cliente.nome}",
        user = request.user.username
    )
    cliente.delete()
    return redirect("clientes")



### USUARIOS ###
class UsersView(LoginRequiredMixin,ListView):
    model = User
    context_object_name = "usuarios"
    paginate_by = 20
    template_name = "usuarios.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        # pega search_value tanto do POST quanto do GET (fallback)
        search_value = (
            self.request.POST.get("search_value")
            or self.request.GET.get("search_value")
        )

        if search_value:
            filtros = Q()

            # percorre todos os campos do model
            for field in self.model._meta.fields:
                # filtra apenas campos de texto
                if isinstance(field, (CharField, TextField)):
                    filtros |= Q(**{f"{field.name}__icontains": search_value})

            queryset = queryset.filter(filtros)

        return queryset

    def post(self, request, *args, **kwargs):
        # permite POST funcionar como GET na ListView
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for user in ctx["usuarios"]:
            user.status = "ativa" if user.is_active else "rejeitada"
            user.status_human = "ATIVO" if user.is_active else "DESATIVADO"

            user.is_staff_status = "ativa" if user.is_staff else "rejeitada"
            user.human_is_staff = "SIM" if user.is_staff else "NÃO"
            user.token = hashlib.sha256(user.username.encode()).hexdigest()



        ctx["usuarios_ativos"] = User.objects.filter(is_active=True).count()
        ctx["usuarios_desativados"] = User.objects.filter(is_active=False).count()
        ctx["total_usuarios"] = User.objects.count()

        # mantém o valor pesquisado no template
        ctx["search_value"] = (
            self.request.POST.get("search_value")
            or self.request.GET.get("search_value")
            or ""
        )
        ctx["usuarios_active"] = "active"
        return ctx
    

class UsuarioCreateView(LoginRequiredMixin,CreateView):
    model = User
    form_class = UsuarioCreateForm
    template_name = "criar_usuario.html"
    success_url = reverse_lazy("usuarios")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password"])
        user.save()

        InfosUser.objects.create(
            usuario=user,
            cargo = self.request.POST.get("cargo_usuario", "Comercial Manager")
        )

        Log.objects.create(
            acao=f"Usuário criado: {user.username}",
            user=self.request.user.username if self.request.user.is_authenticated else "Sistema"
        )

        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        ctx =  super().get_context_data(**kwargs)
        ctx["usuarios_active"] = "active"
        return ctx
    
@require_POST
def deletar_usuario(request, pk):
    print(f"Id usuário: {pk}")
    usuario = get_object_or_404(User, pk=int(pk))
    Log.objects.create(
        acao = f"Exclusão de Usuário {usuario.username}",
        user = request.user.username
    )
    usuario.delete()
    return redirect("usuarios")

@require_POST
def alterar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    Log.objects.create(
        acao = f"Alteração em Usuário {usuario.username}",
        user = request.user.username
    )
    usuario.is_staff = not usuario.is_staff
    usuario.save()
    return redirect("usuarios")
    
class ServicosView(LoginRequiredMixin,ListView):
    model = Servico
    context_object_name = "servicos"
    paginate_by = 200
    ordering = ["-atualizacao"]
    template_name = "servicos.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        # pega search_value tanto do POST quanto do GET (fallback)
        search_value = (
            self.request.POST.get("search_value")
            or self.request.GET.get("search_value")
        )

        if search_value:
            filtros = Q()

            # percorre todos os campos do model
            for field in self.model._meta.fields:
                # filtra apenas campos de texto
                if isinstance(field, (CharField, TextField)):
                    filtros |= Q(**{f"{field.name}__icontains": search_value})

            queryset = queryset.filter(filtros)

        return queryset

    def post(self, request, *args, **kwargs):
        # permite POST funcionar como GET na ListView
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["servicos_ativos"] = Servico.objects.filter(status="ATIVA")
        ctx["total_itens"] = Servico.objects.count()
        ctx["total_servicos"] = Servico.objects.filter(status="ATIVA", tipo="Serviço").count()
        ctx["total_equipamentos"] = Servico.objects.filter(status="ATIVA", tipo="Equipamento").count()
        ctx["total_adicionais"] = Servico.objects.filter(status="ATIVA", tipo="Adicional").count()

        # mantém o valor pesquisado no template
        ctx["search_value"] = (
            self.request.POST.get("search_value")
            or self.request.GET.get("search_value")
            or ""
        )
        ctx["servicos_active"] = "active"

        return ctx

class ServicoCreateView(LoginRequiredMixin, CreateView):
    model = Servico
    form_class = ServicoCreateForm
    template_name = "criar_servico.html"
    success_url = reverse_lazy("servicos")

    def form_valid(self, form):
        serv = form.save(commit=False)
        serv.save()

        Log.objects.create(
            acao=f"Serviço criado: {serv.titulo}",
            user=self.request.user.username if self.request.user.is_authenticated else "Sistema"
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx =  super().get_context_data(**kwargs)
        ctx["servicos_active"] = "active"
        return ctx

def servico_create_ajax(request):
    if request.method == "POST":
        form = ServicoCreateForm(request.POST)
        if form.is_valid():
            servico = form.save()
            return JsonResponse({
                "success": True,
                "message": "Item cadastrado com sucesso!",
                "id": servico.id,
                "titulo": servico.titulo
            }, status=200)
        else:
            # Retorna os erros do formulário em formato JSON
            errors = form.errors.as_json()
            return JsonResponse({"success": False, "errors": errors}, status=400)
    
    return JsonResponse({"success": False, "message": "Método não permitido"}, status=405)

@require_POST
def deletar_servico(request, pk):
    servico = get_object_or_404(Servico, pk=pk)
    Log.objects.create(
        acao = f"Exclusão de Serviço {servico.titulo}",
        user = request.user.username
    )
    servico.delete()
    return redirect("servicos")



#### MODELOS
class ModelosView(LoginRequiredMixin,ListView):
    model = Modelo
    context_object_name = "modelos"
    paginate_by = 20
    template_name = "modelos.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        # pega search_value tanto do POST quanto do GET (fallback)
        search_value = (
            self.request.POST.get("search_value")
            or self.request.GET.get("search_value")
        )

        if search_value:
            filtros = Q()

            # percorre todos os campos do model
            for field in self.model._meta.fields:
                # filtra apenas campos de texto
                if isinstance(field, (CharField, TextField)):
                    filtros |= Q(**{f"{field.name}__icontains": search_value})

            queryset = queryset.filter(filtros)

        return queryset

    def post(self, request, *args, **kwargs):
        # permite POST funcionar como GET na ListView
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["total_modelos"] = Modelo.objects.count()

        # mantém o valor pesquisado no template
        ctx["search_value"] = (
            self.request.POST.get("search_value")
            or self.request.GET.get("search_value")
            or ""
        )
        ctx["modelos_active"] = "active"
        return ctx
    
class ModeloCreateView(LoginRequiredMixin, CreateView):
    model = Modelo
    form_class = ModeloCreateForm
    template_name = "criar_modelo.html"
    success_url = reverse_lazy("modelos")

    def form_valid(self, form):
        modelo = form.save(commit=False)
        modelo.save()

        root = os.path.join(os.getcwd(), "models")
        os.makedirs
        arquivo = self.request.FILES.get("arquivo")
        if arquivo:
            ext = arquivo.name.split(".")[-1]
            filepath = os.path.join(root, f"modelo_{modelo.titulo}.{ext}")
            with open(filepath, "wb+") as destino:
                for chunk in arquivo.chunks():
                    destino.write(chunk)
            modelo.filename = filepath
            modelo.save()
            

        Log.objects.create(
            acao=f"Modelo criado: {modelo.titulo}",
            user=self.request.user.username if self.request.user.is_authenticated else "Sistema"
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx =  super().get_context_data(**kwargs)
        ctx["modelo_active"] = "active"
        return ctx

class ModeloUpdateView(LoginRequiredMixin,UpdateView):
    model = Modelo
    form_class = ModeloCreateForm
    template_name = "criar_modelo.html"
    success_url = reverse_lazy("modelos")

    def form_valid(self, form):
        response = super().form_valid(form)

        modelo = form.save(commit=False)
        modelo.save()

        file_to_remove = modelo.filename
        if os.path.exists(file_to_remove):
            os.remove(file_to_remove)

        root = os.path.join(os.getcwd(), "models")
        arquivo = self.request.FILES.get("arquivo")
        if arquivo:
            ext = arquivo.name.split(".")[-1]
            filepath = os.path.join(root, f"modelo_{modelo.titulo}.{ext}")
            with open(filepath, "wb+") as destino:
                for chunk in arquivo.chunks():
                    destino.write(chunk)
            modelo.filename = filepath
            modelo.save()


        Log.objects.create(
            acao="Modelo atualizado",
            user=self.request.user.username if self.request.user.is_authenticated else "Sistema"
        )

        return response
    
    def get_context_data(self, **kwargs):
        ctx =  super().get_context_data(**kwargs)
        ctx["modelos_active"] = "active"
        return ctx
    
@require_POST
def deletar_modelo(request, pk):
    modelo = get_object_or_404(Modelo, pk=pk)
    Log.objects.create(
        acao = f"Exclusão de Modelo {modelo.titulo}",
        user = request.user.username
    )
    modelo.delete()
    return redirect("modelos")



### download
def download_modelo(request):
    id_modelo = request.GET.get("id_modelo")
    modelo = Modelo.objects.get(id=id_modelo)
    file_path = modelo.filename
    formato = file_path.split(".")[-1]
    with open(file_path, "rb") as f:
        doc = f.read()

    response = HttpResponse(
        doc,
        content_type=f"application/{formato}"
    )
    response["Content-Disposition"] = f'attachment; filename="Modelo - {modelo.titulo}.{formato}"'

    return response


def download_docx(request):
    id_proposta = request.GET.get("id_proposta")
    proposta = Proposta.objects.get(id=id_proposta)
    cliente = proposta.cliente
    servicos_list = []
    equipamentos_list=[]
    adicionais_list=[]
    preco_final_servicos = 0
    preco_final_equipamentos = 0
    preco_final_adicionais = 0
    
    modelo = Modelo.objects.get(titulo=proposta.modelo)

    for servico in ServicoProposta.objects.filter(proposta=proposta):
        preco_unitario = servico.preco_unitario
        descricao = servico.descricao
        quantidade = servico.quantidade
        preco_total = round(float(preco_unitario) * quantidade, 2)
        human_preco_total = f"R$ {preco_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        if servico.tipo == "Serviço":
            preco_final_servicos += preco_total
            servico = [f"{quantidade:04d}", descricao, str(preco_unitario), human_preco_total]
            servicos_list.append(servico)
        elif servico.tipo == "Equipamento":
            preco_final_equipamentos += preco_total
            equipamento = [f"{quantidade:04d}", descricao, str(preco_unitario), human_preco_total]
            equipamentos_list.append(equipamento) 
        else:
            preco_final_adicionais += preco_total
            adicional = [f"{quantidade:04d}", descricao, str(preco_unitario), human_preco_total]
            adicionais_list.append(adicional) 
    
    human_preco_final_servicos = f"R$ {preco_final_servicos:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    servicos_list.append(["TOTAL", "Valor Total", "único", human_preco_final_servicos])
    
    human_preco_final_equipamentos = f"R$ {preco_final_equipamentos:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    equipamentos_list.append(["TOTAL", "Valor Total", "R$/mês" if not proposta.tipo_cobranca_equipamento else "Valor único", human_preco_final_equipamentos])
    
    human_preco_final_variaveis = f"R$ {preco_final_adicionais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    adicionais_list.append(["TOTAL", "Valor Total", "R$/mês" if not proposta.tipo_cobranca_adicional else "Valor único", human_preco_final_variaveis])

    formato_download = request.GET.get("formato", "pdf")

    usuario = User.objects.get(username=proposta.usuario_responsavel)
    cargo = InfosUser.objects.get(usuario=usuario).cargo
    print(f"CARGO: {cargo}")
    doc = motor_2(
        nome_empresa=cliente.nome, 
        cnpj_empresa=cliente.cnpj, 
        telefone_empresa=cliente.telefone, 
        cidade_empresa=cliente.cidade, 
        uf_empresa=cliente.uf, 
        nome_responsavel=cliente.nome_responsavel, 
        email_responsavel=cliente.email_responsavel,
        sexo_responsavel=cliente.tratamento_responsavel,
        numero_proposta=proposta.numero_proposta,
        valor_dolar=proposta.valor_dolar,
        servicos=servicos_list,
        adicionais=adicionais_list,
        equipamentos=equipamentos_list,
        formato_download=formato_download,
        pagina_adicionais=modelo.numero_pagina_adicionais,
        pagina_equipamentos=modelo.numero_pagina_equipamentos,
        pagina_servicos=modelo.numero_pagina_servicos,
        tempo_contrato=str(proposta.tempo_de_contrato),
        nome_usuario_responsavel=str(proposta.usuario_responsavel.first_name),
        telefone_usuario_responsavel=str(proposta.usuario_responsavel.last_name),
        email_usuario_responsavel=str(proposta.usuario_responsavel.email),
        cargo_responsavel=str(cargo),
        observacao_adicional=str(proposta.observacoes_adicionais),
        observacao_servico=str(proposta.observacoes_servicos),
        observacao_equipamento=str(proposta.observacoes_equipamento),
        modelo_path=modelo.filename
    )
        



    response = HttpResponse(
        doc,
        content_type=f"application/{formato_download}"
    )
    response["Content-Disposition"] = f'attachment; filename="Proposta - {cliente.nome}.{formato_download}"'

    return response