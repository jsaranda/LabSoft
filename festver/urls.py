from django.urls import path

from . import views

app_name = 'festver'

urlpatterns = [
    path('', views.lista_eventos, name='lista_eventos'),
    path('evento/<int:evento_id>/', views.detalhe_evento, name='detalhe_evento'),
    path('evento/<int:evento_id>/inscrever/', views.inscrever, name='inscrever'),
    path('inscricao/<int:inscricao_id>/avaliar/', views.avaliar, name='avaliar'),
    path('inscricao/<int:inscricao_id>/votar/', views.votar, name='votar'),
    path('evento/<int:evento_id>/resultados/', views.resultados, name='resultados'),
]