from django.urls import path
from . import views
from . import api

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('home', views.Home.as_view(), name='home'),
    path('propostas', views.PropostasView.as_view(), name='propostas'),
    path('pre_propostas', views.PrePropostaView.as_view(), name='pre_proposta'),
    path('criar_proposta', views.PropostaCreateView.as_view(), name='criar_proposta'),
    path('download_docx', views.download_docx, name='download_docx'),
    path('deletar_proposta/<int:pk>/', views.deletar_proposta, name='deletar_proposta'),

    path('clientes', views.ClientesView.as_view(), name='clientes'),
    path('criar_clientes/', views.ClienteCreateView.as_view(), name='criar_clientes'),
    path('atualizar_clientes/<int:pk>/', views.ClienteUpdateView.as_view(), name='atualizar_clientes'),
    path('deletar_cliente/<int:pk>/', views.deletar_cliente, name='deletar_cliente'),

    path('usuarios', views.UsersView.as_view(), name='usuarios'),
    path('criar_usuario', views.UsuarioCreateView.as_view(), name='criar_usuario'),
    path('deletar_usuario/<int:pk>/', views.deletar_usuario, name='deletar_usuario'),
    path('alterar_usuario/<int:pk>/', views.alterar_usuario, name='alterar_usuario'),
    
    path('servicos', views.ServicosView.as_view(), name='servicos'),
    path('criar_servico', views.ServicoCreateView.as_view(), name='criar_servico'),
    path('url_ajax_servico', views.servico_create_ajax, name='url_ajax_servico'),
    path('deletar_servico/<int:pk>/', views.deletar_servico, name='deletar_servico'),
    path('lista_dados/', views.lista_dados, name='lista_dados'),

    path('modelos', views.ModelosView.as_view(), name='modelos'),
    path('criar_modelo', views.ModeloCreateView.as_view(), name='criar_modelo'),
    path('atualizar_modelos/<int:pk>/', views.ModeloUpdateView.as_view(), name='atualizar_modelos'),
    path('deletar_modelo/<int:pk>/', views.deletar_modelo, name='deletar_modelo'),
    path('download_modelo', views.download_modelo, name='download_modelo'),


    #URLS API
    path('api/cadastrar_cliente', api.cadastrar_cliente, name='api_cadastrar_cliente'),
    path('api/deletar_cliente', api.deletar_cliente, name='api_deletar_cliente'),
    path('api/atualizar_cliente', api.atualizar_cliente, name='api_atualizar_cliente'),


    path('api/criar_proposta', api.criar_proposta, name='api_criar_proposta'),
    path('api/baixar_proposta', api.baixar_proposta, name='api_baixar_proposta'),
    path('api/deletar_proposta', api.deletar_proposta, name='api_deletar_proposta'),


]