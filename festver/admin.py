from django.contrib import admin

from .models import (
    Avaliacao,
    Categoria,
    Criterio,
    Evento,
    Inscricao,
    VotoPopular,
)


class CategoriaInline(admin.TabularInline):
    """Permite criar as categorias na MESMA tela do evento (RN01)."""
    model = Categoria
    extra = 1


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'inscricoes_abertas',
        'votacao_aberta',
        'resultados_publicados',
    )
    list_editable = (
        'inscricoes_abertas',
        'votacao_aberta',
        'resultados_publicados',
    )
    filter_horizontal = ('jurados',)
    inlines = [CategoriaInline]


class CriterioInline(admin.TabularInline):
    """Critérios são cadastrados dentro da própria categoria (RN02)."""
    model = Criterio
    extra = 2


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'evento')
    list_filter = ('evento',)
    inlines = [CriterioInline]


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = (
        'titulo_obra',
        'participante',
        'categoria',
        'status',
        'criada_em',
    )
    list_filter = ('status', 'categoria__evento', 'categoria')  # RF15
    search_fields = ('titulo_obra', 'participante__username')
    list_editable = ('status',)  # homologação rápida direto na lista
    date_hierarchy = 'criada_em'


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    """Somente leitura na prática: jurado avalia pela tela própria.
    Aqui o organizador apenas audita as notas lançadas."""
    list_display = ('inscricao', 'jurado', 'criterio', 'nota')
    list_filter = ('inscricao__categoria__evento', 'jurado')


@admin.register(VotoPopular)
class VotoPopularAdmin(admin.ModelAdmin):
    list_display = ('inscricao', 'eleitor', 'votado_em')
    list_filter = ('categoria__evento', 'categoria')