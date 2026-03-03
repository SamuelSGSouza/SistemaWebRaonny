from django.contrib import admin
from .models import *


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'momento')
    readonly_fields = ('momento',)
    search_fields = ('user',)

@admin.register(Proposta)
class PropostaAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'criacao')
    search_fields = ('user',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'criacao')
    search_fields = ('nome',)

@admin.register(Modelo)
class ModeloAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', )
    search_fields = ('titulo',)

@admin.register(InfosUser)
class InfosUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', )
    search_fields = ('usuario',)
# Register your models here.
