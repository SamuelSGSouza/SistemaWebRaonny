from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Log(models.Model):
    acao = models.CharField(max_length=55, verbose_name= "Ação Realizada")
    user = models.CharField(max_length=255, verbose_name="Usuário da Ação")
    momento = models.DateTimeField(auto_now_add=True)

def salva_log(acao, username):
    Log.objects.create(
        acao = acao,
        user = username
    )

class InfosUser(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="info")
    cargo = models.CharField(
        max_length=255,
        choices=(
            ("Comercial Manager", "Comercial Manager"),
            ("Assistente Comercial", "Assistente Comercial"),
            ("Diretor Comercial", "Diretor Comercial"),
            ("Diretor", "Diretor"),
            ("CEO", "CEO"),
        ),
        default="Comercial Manager"
    )

class Proposta(models.Model):
    usuario_responsavel = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)

    cliente = models.ForeignKey(
        "Cliente",
        on_delete=models.PROTECT,
        related_name="propostas"
    )

    modelo = models.CharField(max_length=255)

    status = models.CharField(
        max_length=14,
        choices=(
            ("ATIVA", "ATIVA"),
            ("SUSPENSA", "SUSPENSA"),
            ("REJEITADA", "REJEITADA"),
        ),
        default="ATIVA"
    )
    tempo_de_contrato = models.IntegerField(default=24)
    valor_dolar = models.CharField(max_length=24, default="0,00")
    numero_proposta = models.CharField(max_length=25, default="")
    observacoes_equipamento = models.TextField(default="")
    observacoes_servicos = models.TextField(default="")
    observacoes_adicionais = models.TextField(default="")
    tipo_cobranca_equipamento = models.BooleanField(default=False)
    tipo_cobranca_servico = models.BooleanField(default=False)
    tipo_cobranca_adicional = models.BooleanField(default=False)
    user = models.CharField(max_length=255)
    criacao = models.DateTimeField(auto_now_add=True)
    atualizacao = models.DateTimeField(auto_now=True)

class ServicoProposta(models.Model):
    proposta = models.ForeignKey(
        Proposta,
        on_delete=models.CASCADE,
        related_name="servicos"
    )

    quantidade = models.PositiveIntegerField()
    descricao = models.TextField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=55,
                              choices=(
                                ("Serviço", "Serviço"),
                                ("Equipamento", "Locação de Equipamentos / SaaS"),
                                ("Adicional", "Adicional"),

                              ), default="Serviço")

    def subtotal(self):
        return self.quantidade * self.preco_unitario

class Cliente(models.Model):
    nome = models.CharField(max_length=255, )
    cnpj = models.CharField(max_length=18, unique=True)
    telefone = models.CharField(max_length=255, default="")
    cidade = models.CharField(max_length=255, default="")
    uf = models.CharField(
        max_length=2,
        default="AC",
        choices=(
            ("AC", "AC - Acre"),
            ("AL", "AL - Alagoas"),
            ("AP", "AP - Amapá"),
            ("AM", "AM - Amazonas"),
            ("BA", "BA - Bahia"),
            ("CE", "CE - Ceará"),
            ("DF", "DF - Distrito Federal"),
            ("ES", "ES - Espírito Santo"),
            ("GO", "GO - Goiás"),
            ("MA", "MA - Maranhão"),
            ("MT", "MT - Mato Grosso"),
            ("MS", "MS - Mato Grosso do Sul"),
            ("MG", "MG - Minas Gerais"),
            ("PA", "PA - Pará"),
            ("PB", "PB - Paraíba"),
            ("PR", "PR - Paraná"),
            ("PE", "PE - Pernambuco"),
            ("PI", "PI - Piauí"),
            ("RJ", "RJ - Rio de Janeiro"),
            ("RN", "RN - Rio Grande do Norte"),
            ("RS", "RS - Rio Grande do Sul"),
            ("RO", "RO - Rondônia"),
            ("RR", "RR - Roraima"),
            ("SC", "SC - Santa Catarina"),
            ("SP", "SP - São Paulo"),
            ("SE", "SE - Sergipe"),
            ("TO", "TO - Tocantins"),
        ),
    )
    nome_responsavel = models.CharField(max_length=255, default="")
    email_responsavel = models.CharField(max_length=255, default="")
    tratamento_responsavel = models.CharField(max_length=3, choices=(
        ("Sr", "Sr"),
        ("Sra", "Sra")
    ),default="Sr")
    status = models.CharField(max_length=14,
                              choices=(
                                  ("ATIVA", "ATIVA"),
                                  ("SUSPENSA", "SUSPENSA"),
                                  ("REJEITADA", "REJEITADA"),
                              ), default="ATIVA")
    criacao = models.DateTimeField(auto_now=True )
    atualizacao = models.DateTimeField(auto_now=True)


class Modelo(models.Model):
    titulo = models.CharField(max_length=255)
    numero_pagina_servicos = models.IntegerField(default=0)
    numero_pagina_adicionais = models.IntegerField(default=0)
    numero_pagina_equipamentos = models.IntegerField(default=0)
    filename = models.CharField(max_length=255, default="")
    criacao = models.DateTimeField(auto_now_add=True, )
    atualizacao = models.DateTimeField(auto_now=True)

class Servico(models.Model):
    titulo = models.CharField(max_length=255, unique=True)
    descricao=models.TextField()
    valor_servico= models.FloatField()
    tipo = models.CharField(max_length=14,
                              choices=(
                                  ("Equipamento", "Locação de Equipamentos / SaaS"),
                                  ("Serviço", "Serviço"),
                                  ("Adicional", "Variavel"),
                              ), default="Serviço")
    status = models.CharField(max_length=14,
                              choices=(
                                  ("ATIVA", "ATIVA"),
                                  ("SUSPENSA", "SUSPENSA"),
                              ), default="ATIVA")
    criacao = models.DateTimeField(auto_now_add=True, )
    atualizacao = models.DateTimeField(auto_now=True)