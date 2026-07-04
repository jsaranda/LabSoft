from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Usa o UserAdmin padrão do Django, que já traz a tela de
    usuários completa: troca de senha com hash, grupos,
    permissões e filtros. Se um dia adicionarmos campos ao
    Usuario (matrícula, vínculo), é aqui que os exibiremos.
    """
    pass