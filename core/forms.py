from django import forms
from django.contrib.auth.models import User
from .models import *


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nome",
            "cnpj",
            "telefone",
            "cidade",
            "uf",
            "nome_responsavel",
            "email_responsavel",
            "tratamento_responsavel",
            "status",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "cnpj": forms.TextInput(attrs={"class": "form-control", "placeholder": "00.000.000/0000-00"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "cidade": forms.TextInput(attrs={"class": "form-control"}),
            "uf": forms.Select(attrs={"class": "form-control"}),
            "nome_responsavel": forms.TextInput(attrs={"class": "form-control"}),
            "email_responsavel": forms.EmailInput(attrs={"class": "form-control"}),
            "tratamento_responsavel": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "nome": "Nome do Cliente",
            "cnpj": "CNPJ",
            "nome_responsavel": "Responsável",
            "email_responsavel": "E-mail do Responsável",
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data["cnpj"]
        # remove caracteres não numéricos
        cnpj = "".join(filter(str.isdigit, cnpj))

        if len(cnpj) != 14:
            raise forms.ValidationError("CNPJ inválido.")

        return cnpj

class UsuarioCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Senha"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirmar senha"
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name",]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "password": forms.PasswordInput(attrs={"class": "form-control"}),
            "password_confirm": forms.PasswordInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("password_confirm"):
            raise forms.ValidationError("As senhas não coincidem.")
        return cleaned_data


class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "is_active"]



class ServicoCreateForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = [
            "titulo",
            "descricao",
            "valor_servico",
            "tipo",
            "status",
        ]

        widgets = {
            "titulo": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Título do serviço"
            }),
            "descricao": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Descrição do serviço"
            }),
            "valor_servico": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "placeholder": "Valor"
            }),
            "tipo": forms.Select(attrs={
                "class": "form-control"
            }),
            "status": forms.Select(attrs={
                "class": "form-control"
            }),
        }

        labels = {
            "titulo": "Título",
            "descricao": "Descrição",
            "valor_servico": "Valor do Serviço",
            "tipo": "Tipo",
            "status": "Status",
        }
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("valor_servico"):
            try:
                float(cleaned_data.get("valor_servico"))
            except:
                raise forms.ValidationError("Valor do serviço deve ser um Número float")
        return cleaned_data
    

class ModeloCreateForm(forms.ModelForm):
    class Meta:
        model = Modelo
        fields = [
            "titulo",
            "numero_pagina_servicos",
            "numero_pagina_adicionais",
            "numero_pagina_equipamentos",
        ]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "numero_pagina_servicos": forms.NumberInput(attrs={"class": "form-control"}),
            "numero_pagina_adicionais": forms.NumberInput(attrs={"class": "form-control"}),
            "numero_pagina_equipamentos": forms.NumberInput(attrs={"class": "form-control"}),
        }
