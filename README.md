# Tutorial — Portal LABSOFT e Módulo FestVer (Django)

**LABSOFT — Laboratório de Desenvolvimento de Software — IFRS Campus Veranópolis**

Este tutorial reconstrói, passo a passo, o Portal LABSOFT e seu primeiro módulo: o
**FestVer**, sistema de inscrição e votação para apresentações estudantis, baseado na
Especificação de Requisitos elaborada pelas bolsistas do laboratório.

O objetivo não é só "fazer funcionar": cada passo explica **por que** a decisão foi
tomada, porque este módulo é o **exemplo** a partir do qual os próximos módulos do
portal serão construídos.

---

## Visão geral da arquitetura

```
labsoft_portal/          ← o PROJETO (portal)
├── config/              ← configurações (settings, urls principais)
├── core/                ← app compartilhado: usuário, home do portal
├── festver/             ← MÓDULO 1: sistema do FestVer
├── (proximos módulos…)  ← cada novo sistema = um novo app
├── templates/           ← templates globais (base.html) e de cada app
├── media/               ← arquivos enviados pelos usuários (uploads)
└── manage.py
```

**Regra de ouro da arquitetura:** um projeto (portal), vários apps (módulos).
Tudo que for comum aos módulos mora no `core`; cada módulo cuida só do seu assunto.

## Decisões de requisitos (registradas antes de codificar)

A especificação original deixou pontos em aberto. Estas foram as decisões tomadas —
em projeto real, decisões assim devem ser **documentadas**, como aqui:

| # | Decisão |
|---|---------|
| D1 | Usuário único do portal (`core.Usuario`), login local por enquanto; integração com Active Directory/LDAP do IFRS fica preparada para o futuro. |
| D2 | "Jurado" não é um tipo de usuário: é uma **associação** de um usuário a um evento. "Organizador" = usuário staff, que usa o Django admin. |
| D3 | Nota do jurado: **0 a 10 por critério**, média simples entre critérios e entre jurados (RN03). |
| D4 | Voto popular é **separado** da média do júri: dois rankings. Um voto por usuário por categoria, com possibilidade de trocar o voto. |
| D5 | Inscrição tem ciclo de vida: **Pendente → Homologada ou Rejeitada**. Só homologadas recebem avaliação, voto e aparecem publicamente. |
| D6 | O evento tem três "chaves" controladas pelo organizador: inscrições abertas, votação aberta e resultados publicados. |
| D7 | RF01, RF02, RF03, RF14, RF15 e RF16 são atendidos pelo **Django admin** — não há telas próprias para o organizador no MVP. |

---

# PARTE 1 — Fundação do Portal

## Passo 1 — Pasta do projeto e ambiente virtual

Abra o PowerShell, navegue até a pasta onde ficam seus projetos e rode:

```powershell
mkdir labsoft_portal
cd labsoft_portal
python -m venv venv
```

**Por quê:** o `venv` (ambiente virtual) isola as dependências deste projeto das dos
outros. Cada projeto tem o seu — usar um venv compartilhado funciona até o dia em que
o projeto A precisa do Django 5 e o projeto B está preso no Django 4.

Ative o ambiente:

```powershell
.\venv\Scripts\Activate.ps1
```

Você deve ver `(venv)` no início da linha do prompt.

> ⚠️ **Avisos importantes:**
> - A criação do venv demora alguns segundos e termina **sem mensagem nenhuma** — silêncio é sucesso.
> - Se o PowerShell reclamar de política de execução de scripts, rode uma única vez:
>   `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
> - Se aparecer `O termo '...Activate.ps1' não é reconhecido`, a pasta do venv não existe
>   nesse local — confira com `dir` se ela foi criada e se o nome bate.

## Passo 2 — Instalar o Django e registrar dependências

Com o `(venv)` ativo:

```powershell
python -m pip install --upgrade pip
pip install django
django-admin --version
pip freeze > requirements.txt
```

**Por quê:** o `requirements.txt` é a "receita" do ambiente. Quem clonar o projeto
recria tudo com `pip install -r requirements.txt`. **Hábito:** atualize esse arquivo
a cada novo `pip install`.

*(Este tutorial foi construído com Django 6.0.)*

## Passo 3 — Criar o projeto Django (o portal)

Ainda na pasta `labsoft_portal`:

```powershell
django-admin startproject config .
```

**Atenção ao ponto final** — ele faz parte do comando.

**Por quê (duas decisões embutidas):**

1. **O ponto final** diz "crie o projeto *nesta pasta*", evitando a famosa confusão de
   pastas duplicadas (`labsoft_portal/labsoft_portal/labsoft_portal/`).
2. **O nome `config`**: essa pasta contém só configuração (`settings.py`, `urls.py`,
   `wsgi.py`/`asgi.py`) — nenhuma funcionalidade. O nome deixa a estrutura
   autoexplicativa. É convenção comum em projetos Django profissionais.

Teste:

```powershell
python manage.py runserver
```

Abra `http://127.0.0.1:8000` — deve aparecer a página do foguete do Django.
Pare o servidor com `Ctrl+C`.

## Passo 4 — App `core` com Custom User (O PASSO MAIS IMPORTANTE)

Este é o único passo que **não dá para corrigir depois**. O modelo de usuário precisa
ser definido **antes da primeira migration**.

```powershell
python manage.py startapp core
```

Substitua o conteúdo de **`core/models.py`**:

```python
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    """
    Modelo de usuário do portal LABSOFT.

    Herda tudo do usuário padrão do Django (username, senha, e-mail,
    nomes, grupos e permissões). Por enquanto não adiciona nada, mas
    existir desde a PRIMEIRA migration nos permite, no futuro:
      - integrar com o Active Directory / LDAP do IFRS;
      - adicionar campos como matrícula/SIAPE ou vínculo com o campus;
    sem precisar refazer o banco de dados.

    Convenção: o username deve seguir o login de domínio do IFRS.
    """
    pass
```

Em **`config/settings.py`**, registre o app:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]
```

E **no final do arquivo**, adicione:

```python
AUTH_USER_MODEL = 'core.Usuario'
```

**Por quê:** o Django cria as tabelas de autenticação na primeira migration, e trocar
o modelo de usuário depois disso exige cirurgia no banco. Com o `Usuario` nosso desde o
início — mesmo vazio, só com `pass` — a porta fica aberta para o AD/LDAP (basta
instalar `django-auth-ldap` e configurar um backend, sem mexer em modelo nenhum).

Agora sim, as primeiras migrations:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Deve aparecer `core/migrations/0001_initial.py - Create model Usuario` e a criação do
arquivo `db.sqlite3`.

## Passo 5 — Usuario no admin e superusuário

Custom User **não aparece automaticamente** no admin. Substitua **`core/admin.py`**:

```python
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
```

**Por quê `UserAdmin` e não `ModelAdmin`:** ele traz a interface especializada de
usuários — principalmente o tratamento correto de senha, que nunca é editada como
texto simples.

Crie o superusuário:

```powershell
python manage.py createsuperuser
```

> ⚠️ A senha **não aparece** enquanto você digita — o teclado não travou!

Suba o servidor, acesse `http://127.0.0.1:8000/admin`, faça login. Devem aparecer
**Groups** (Autenticação) e **Users** (Core).

## Passo 6 — Template base do portal e página inicial

Crie as pastas:

```powershell
mkdir templates
mkdir templates\core
```

Em **`config/settings.py`**, na lista `TEMPLATES`, altere `'DIRS': []` para:

```python
'DIRS': [BASE_DIR / 'templates'],
```

Crie **`templates/base.html`** (versão inicial, simples — no Passo 13 ela ganhará
Bootstrap):

```html
{% load static %}
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block titulo %}Portal LABSOFT{% endblock %} — IFRS Veranópolis</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, sans-serif; background: #f4f6f8; color: #1a2733; }
        header { background: #1e5b3f; color: #fff; padding: 1rem 2rem;
                 display: flex; justify-content: space-between; align-items: center; }
        header a { color: #fff; text-decoration: none; }
        header .logo { font-weight: bold; font-size: 1.2rem; }
        nav a { margin-left: 1.5rem; }
        main { max-width: 960px; margin: 2rem auto; padding: 0 1rem; }
        footer { text-align: center; padding: 2rem; color: #6b7a89; font-size: 0.85rem; }
    </style>
</head>
<body>
    <header>
        <a href="/" class="logo">LABSOFT · IFRS Veranópolis</a>
        <nav>
            {% if user.is_authenticated %}
                <span>Olá, {{ user.first_name|default:user.username }}</span>
                {% if user.is_staff %}<a href="/admin/">Admin</a>{% endif %}
            {% else %}
                <a href="/admin/">Entrar</a>
            {% endif %}
        </nav>
    </header>

    <main>
        {% block conteudo %}{% endblock %}
    </main>

    <footer>
        Laboratório de Desenvolvimento de Software — IFRS Campus Veranópolis
    </footer>
</body>
</html>
```

Crie **`templates/core/home.html`**:

```html
{% extends 'base.html' %}

{% block titulo %}Início{% endblock %}

{% block conteudo %}
    <h1>Portal LABSOFT</h1>
    <p>Sistemas desenvolvidos pelo Laboratório de Desenvolvimento de
       Software do IFRS Campus Veranópolis.</p>

    <h2>Módulos</h2>
    <ul>
        <li>FestVer — Inscrições e Votação <em>(em construção)</em></li>
    </ul>
{% endblock %}
```

**Conceito-chave:** o `base.html` define o esqueleto com "buracos" (`{% block %}`);
cada página só preenche os buracos com `{% extends %}`. Você escreverá esse padrão em
**todas** as telas do portal.

A view, em **`core/views.py`**:

```python
from django.shortcuts import render


def home(request):
    """Página inicial do portal, que lista os módulos disponíveis."""
    return render(request, 'core/home.html')
```

E a rota, substituindo **`config/urls.py`**:

```python
from django.contrib import admin
from django.urls import path

from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.home, name='home'),
]
```

Suba o servidor e acesse `http://127.0.0.1:8000` — a home do portal deve aparecer com
o cabeçalho verde.

---
# PARTE 2 — O Módulo FestVer

## Passo 7 — Criar o app `festver` e os models

Com o servidor parado (`Ctrl+C`):

```powershell
python manage.py startapp festver
```

Registre em **`config/settings.py`**:

```python
INSTALLED_APPS = [
    # ... apps do django ...
    'core',
    'festver',
]
```

Como haverá upload de obras (RF05), adicione **no final do `settings.py`**:

```python
# Arquivos enviados pelos usuários (uploads de obras)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

Agora substitua o conteúdo de **`festver/models.py`** — são 6 models que implementam
as decisões D2 a D6:

```python
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Evento(models.Model):
    """
    Um evento do FestVer (ex.: 'FestVer 2026').
    Criado e gerenciado pelo organizador via admin (RF01).
    """
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    inscricoes_abertas = models.BooleanField(
        default=False,
        help_text='Marque para permitir novas inscrições (RF16).',
    )
    votacao_aberta = models.BooleanField(
        default=False,
        help_text='Marque para liberar avaliação dos jurados e voto popular.',
    )
    resultados_publicados = models.BooleanField(
        default=False,
        help_text='Marque para tornar o pódio visível ao público (RF10).',
    )
    jurados = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='eventos_como_jurado',
        help_text='Usuários que podem avaliar inscrições deste evento (RF03).',
    )

    class Meta:
        verbose_name = 'evento'
        verbose_name_plural = 'eventos'

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    """Categoria de um evento, ex.: 'Música', 'Poesia' (RF02, RN01)."""
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name='categorias'
    )
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'
        unique_together = [('evento', 'nome')]

    def __str__(self):
        return f'{self.nome} ({self.evento})'


class Criterio(models.Model):
    """
    Critério de avaliação de uma categoria (RN02).
    DECISÃO D3: nota de 0 a 10 por critério, média simples entre
    critérios e entre jurados. Pesos ficam como evolução futura.
    """
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, related_name='criterios'
    )
    nome = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'critério'
        verbose_name_plural = 'critérios'

    def __str__(self):
        return f'{self.nome} — {self.categoria.nome}'


class Inscricao(models.Model):
    """
    Inscrição de uma obra em uma categoria (RF04, RF05).
    DECISÃO D5: só inscrições HOMOLOGADAS recebem avaliação e votos.
    """
    class Status(models.TextChoices):
        PENDENTE = 'PEN', 'Pendente'
        HOMOLOGADA = 'HOM', 'Homologada'
        REJEITADA = 'REJ', 'Rejeitada'

    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name='inscricoes'
    )
    participante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='inscricoes_festver',
    )
    titulo_obra = models.CharField('título da obra', max_length=200)
    arquivo_obra = models.FileField(
        'arquivo da obra', upload_to='festver/obras/'
    )
    status = models.CharField(
        max_length=3, choices=Status.choices, default=Status.PENDENTE
    )
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'inscrição'
        verbose_name_plural = 'inscrições'

    def __str__(self):
        return f'{self.titulo_obra} ({self.participante})'

    @property
    def media_juri(self):
        """Média simples de todas as notas dos jurados (RN03, RF09)."""
        resultado = self.avaliacoes.aggregate(media=models.Avg('nota'))
        return resultado['media']

    @property
    def total_votos_populares(self):
        """Contagem de votos do público (RF08)."""
        return self.votos_populares.count()


class Avaliacao(models.Model):
    """
    Nota de UM jurado para UM critério de UMA inscrição (RF07).
    A restrição unique garante que o jurado não avalie duas vezes
    o mesmo critério da mesma obra.
    """
    inscricao = models.ForeignKey(
        Inscricao, on_delete=models.CASCADE, related_name='avaliacoes'
    )
    jurado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='avaliacoes_festver',
    )
    criterio = models.ForeignKey(Criterio, on_delete=models.CASCADE)
    nota = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text='Nota de 0 a 10.',
    )

    class Meta:
        verbose_name = 'avaliação'
        verbose_name_plural = 'avaliações'
        unique_together = [('inscricao', 'jurado', 'criterio')]

    def __str__(self):
        return f'{self.jurado} → {self.inscricao} [{self.criterio.nome}]: {self.nota}'


class VotoPopular(models.Model):
    """
    Voto do público em uma inscrição (RF08).
    DECISÃO D4: um voto por usuário POR CATEGORIA. O ranking popular
    é separado da média do júri (não entram na mesma conta).
    O campo 'categoria' é redundante (existe via inscricao), mas
    é ele que permite a restrição unique abaixo.
    """
    inscricao = models.ForeignKey(
        Inscricao, on_delete=models.CASCADE, related_name='votos_populares'
    )
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    eleitor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='votos_festver',
    )
    votado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'voto popular'
        verbose_name_plural = 'votos populares'
        unique_together = [('eleitor', 'categoria')]

    def save(self, *args, **kwargs):
        # Preenche a categoria automaticamente a partir da inscrição,
        # para a regra "um voto por categoria" nunca depender da view.
        self.categoria = self.inscricao.categoria
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.eleitor} → {self.inscricao}'
```

**Pontos importantes deste passo:**

- **`settings.AUTH_USER_MODEL`**, nunca importar o User direto — é o que mantém a
  porta do AD/LDAP aberta.
- **`on_delete=PROTECT`** nas inscrições: ninguém apaga uma categoria levando
  inscrições junto sem querer.
- As **`@property`** implementam a RN03 direto no modelo.
- **`unique_together`** faz o **banco** garantir as regras de negócio, em vez de
  confiar só nas views.

Gere e aplique:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Devem ser criados os 6 models.

## Passo 8 — O admin como ferramenta do organizador

Pela decisão D7, o organizador trabalha no Django admin. Substitua
**`festver/admin.py`**:

```python
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
```

**Pontos importantes:**

- **Inlines**: o organizador cria evento + categorias numa tela só, e critérios dentro
  da categoria — o admin espelhando a hierarquia da RN01/RN02.
- **`list_editable`** no status transforma a lista de inscrições num painel de
  homologação.
- **`list_filter` atravessando relações** (`categoria__evento`): o duplo underline
  navegando ForeignKey é um idioma do Django que você usará sempre — e implementa o RF15.
- **`filter_horizontal`** troca o select múltiplo padrão por um widget decente de duas
  colunas.

**Teste agora:** suba o servidor, entre no admin e crie um evento de teste com duas
categorias na mesma tela; abra uma categoria e adicione critérios (ex.: "Afinação",
"Presença de palco"); associe seu usuário como jurado do evento.

> ⚠️ **Pegadinha do `filter_horizontal`:** clicar no nome do usuário só o *seleciona* —
> é preciso clicar na setinha (→) para movê-lo para a coluna "Chosen/Escolhidos", e
> depois **salvar**.

## Passo 9 — Inscrição pública (RF04/RF05): o trio form → view → template

Este passo introduz o padrão que se repete em todo o módulo.

Crie o arquivo **`festver/forms.py`** (novo):

```python
from django import forms

from .models import Inscricao


class InscricaoForm(forms.ModelForm):
    """
    Formulário de inscrição (RF05).
    ModelForm: o Django gera os campos a partir do model,
    incluindo validação. Nome e identificação do participante
    vêm do usuário logado — por isso não aparecem aqui.
    """

    class Meta:
        model = Inscricao
        fields = ['categoria', 'titulo_obra', 'arquivo_obra']

    def __init__(self, *args, evento=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostra apenas as categorias DO EVENTO desta página,
        # não todas as categorias do banco.
        if evento is not None:
            self.fields['categoria'].queryset = evento.categorias.all()
        # Aplica as classes do Bootstrap a todos os campos
        # (o Bootstrap entra no Passo 13, mas já deixamos pronto)
        for nome, campo in self.fields.items():
            if nome == 'categoria':
                campo.widget.attrs['class'] = 'form-select'
            else:
                campo.widget.attrs['class'] = 'form-control'
```

Substitua o conteúdo de **`festver/views.py`**:

```python
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InscricaoForm
from .models import Evento


def lista_eventos(request):
    """Página inicial do módulo: lista os eventos (RF13)."""
    eventos = Evento.objects.all()
    return render(request, 'festver/lista_eventos.html', {'eventos': eventos})


def detalhe_evento(request, evento_id):
    """Página de um evento, com suas categorias e inscritos homologados (RF06)."""
    evento = get_object_or_404(Evento, pk=evento_id)
    return render(request, 'festver/detalhe_evento.html', {'evento': evento})


@login_required
def inscrever(request, evento_id):
    """Formulário de inscrição de obra (RF04/RF05)."""
    evento = get_object_or_404(Evento, pk=evento_id)

    if not evento.inscricoes_abertas:
        messages.error(request, 'As inscrições deste evento estão encerradas.')
        return redirect('festver:detalhe_evento', evento_id=evento.id)

    if request.method == 'POST':
        # request.FILES é obrigatório em forms com upload!
        form = InscricaoForm(request.POST, request.FILES, evento=evento)
        if form.is_valid():
            inscricao = form.save(commit=False)
            inscricao.participante = request.user
            inscricao.save()
            messages.success(
                request,
                'Inscrição enviada! Ela será analisada pela organização.',
            )
            return redirect('festver:detalhe_evento', evento_id=evento.id)
    else:
        form = InscricaoForm(evento=evento)

    return render(
        request,
        'festver/inscrever.html',
        {'evento': evento, 'form': form},
    )
```

Crie **`festver/urls.py`** (novo):

```python
from django.urls import path

from . import views

app_name = 'festver'

urlpatterns = [
    path('', views.lista_eventos, name='lista_eventos'),
    path('evento/<int:evento_id>/', views.detalhe_evento, name='detalhe_evento'),
    path('evento/<int:evento_id>/inscrever/', views.inscrever, name='inscrever'),
]
```

Conecte ao portal, substituindo **`config/urls.py`**:

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.home, name='home'),
    path('festver/', include('festver.urls')),
]

# Em desenvolvimento, o próprio Django serve os uploads.
# Em produção isso será papel do Nginx.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Crie a pasta dos templates do módulo:

```powershell
mkdir templates\festver
```

*(Os templates deste módulo estão adiante, no Passo 13, já na versão final com
Bootstrap — na construção original fizemos versões simples primeiro e estilizamos
depois, justamente para ver que trocar o visual não mexe em nenhuma view ou model.)*

**Conceitos-chave deste passo:**

- **`ModelForm`**: formulário e validação gerados a partir do model.
- **`commit=False`**: o form não sabe quem é o participante; a view completa o objeto
  com `request.user` antes de salvar. Padrão usado mil vezes em Django.
- **`enctype="multipart/form-data"` no template + `request.FILES` na view**: a dupla
  obrigatória do upload — esquecer qualquer um dos dois é o bug clássico de
  "o arquivo não chega".
- **`@login_required`**: só usuário logado se inscreve (parte do RNF08).
- **`app_name` + namespace** (`festver:detalhe_evento`): módulos diferentes podem ter
  URLs com nomes iguais sem conflito — essencial na arquitetura de portal.
- **Post/Redirect/Get**: após o POST bem-sucedido, redirecionamos. No log do
  runserver você verá `POST ... 302` seguido de `GET ... 200` — aprenda a ler isso!

## Passo 10 — Tela de avaliação do jurado (RF07)

Adicione ao **final** de **`festver/views.py`**:

```python
from django.core.exceptions import PermissionDenied

from .models import Avaliacao, Inscricao


@login_required
def avaliar(request, inscricao_id):
    """
    Tela em que o jurado dá notas por critério a uma inscrição (RF07).
    Regras: só jurados DO EVENTO, só com votação aberta,
    só inscrições homologadas.
    """
    inscricao = get_object_or_404(Inscricao, pk=inscricao_id)
    evento = inscricao.categoria.evento

    # Segurança primeiro: é jurado deste evento?
    if not evento.jurados.filter(pk=request.user.pk).exists():
        raise PermissionDenied('Você não é jurado deste evento.')

    if not evento.votacao_aberta:
        messages.error(request, 'A votação deste evento não está aberta.')
        return redirect('festver:detalhe_evento', evento_id=evento.id)

    if inscricao.status != Inscricao.Status.HOMOLOGADA:
        messages.error(request, 'Esta inscrição não está homologada.')
        return redirect('festver:detalhe_evento', evento_id=evento.id)

    criterios = inscricao.categoria.criterios.all()

    if request.method == 'POST':
        for criterio in criterios:
            valor = request.POST.get(f'nota_{criterio.id}')
            if valor:
                # update_or_create: se o jurado reenviar, ATUALIZA a
                # nota em vez de violar o unique_together do model.
                Avaliacao.objects.update_or_create(
                    inscricao=inscricao,
                    jurado=request.user,
                    criterio=criterio,
                    defaults={'nota': valor},
                )
        messages.success(request, f'Notas registradas para "{inscricao.titulo_obra}".')
        return redirect('festver:detalhe_evento', evento_id=evento.id)

    # Notas já dadas por ESTE jurado, para pré-preencher o formulário
    notas_existentes = {
        a.criterio_id: a.nota
        for a in inscricao.avaliacoes.filter(jurado=request.user)
    }
    linhas = [
        {'criterio': c, 'nota': notas_existentes.get(c.id, '')}
        for c in criterios
    ]

    return render(
        request,
        'festver/avaliar.html',
        {'inscricao': inscricao, 'linhas': linhas},
    )
```

Adicione a rota em **`festver/urls.py`** (dentro de `urlpatterns`):

```python
    path('inscricao/<int:inscricao_id>/avaliar/', views.avaliar, name='avaliar'),
```

**Conceitos-chave:**

- **Autorização ≠ autenticação**: `@login_required` garante que há *alguém* logado; o
  teste dos jurados com `PermissionDenied` (erro 403) garante que é a *pessoa certa*.
  Essa distinção é o RNF08 de verdade.
- **`update_or_create`**: o jurado pode revisar notas sem quebrar a restrição do
  banco — a view coopera com o `unique_together` do model.
- **Formulário manual** aqui, de propósito: o form é dinâmico (um input por critério),
  então o `ModelForm` não serve. Você conheceu os dois jeitos e quando usar cada um.
- **Validação em camadas**: `min/max` no HTML é cortesia para o usuário; quem garante
  mesmo são os validators do model.

## Passo 11 — Voto popular (RF08)

Adicione ao **final** de **`festver/views.py`**:

```python
from .models import VotoPopular


@login_required
def votar(request, inscricao_id):
    """
    Voto popular em uma inscrição (RF08).
    DECISÃO D4: um voto por usuário por categoria (unique no model).
    Se o usuário votar de novo NA MESMA categoria, o voto é
    TRANSFERIDO para a nova obra (atualiza em vez de recusar).
    """
    inscricao = get_object_or_404(Inscricao, pk=inscricao_id)
    evento = inscricao.categoria.evento

    if not evento.votacao_aberta:
        messages.error(request, 'A votação deste evento não está aberta.')
        return redirect('festver:detalhe_evento', evento_id=evento.id)

    if inscricao.status != Inscricao.Status.HOMOLOGADA:
        messages.error(request, 'Esta inscrição não está disponível para votação.')
        return redirect('festver:detalhe_evento', evento_id=evento.id)

    if request.method == 'POST':
        voto, criado = VotoPopular.objects.update_or_create(
            eleitor=request.user,
            categoria=inscricao.categoria,
            defaults={'inscricao': inscricao},
        )
        if criado:
            messages.success(request, f'Voto registrado em "{inscricao.titulo_obra}"!')
        else:
            messages.success(
                request,
                f'Seu voto na categoria {inscricao.categoria.nome} '
                f'foi transferido para "{inscricao.titulo_obra}".',
            )

    return redirect('festver:detalhe_evento', evento_id=evento.id)
```

Rota em **`festver/urls.py`**:

```python
    path('inscricao/<int:inscricao_id>/votar/', views.votar, name='votar'),
```

**Conceitos-chave:**

- **Votar só via POST**: se alguém acessar a URL por GET, apenas volta para o evento
  sem votar. **Ação que altera dados nunca acontece por GET** (senão até o preload do
  navegador "vota").
- **`update_or_create` de novo, com outra semântica**: aqui a chave é
  `(eleitor, categoria)` e o que muda é a inscrição — implementando "pode trocar o
  voto" em uma linha, com o `unique_together` como rede de segurança.
- No template (Passo 13), o botão de votar é um **formulário de uma linha** — o jeito
  correto de fazer "link que faz POST".

## Passo 12 — Resultados: média do júri e pódio (RF09, RF10, RF11)

Adicione ao **final** de **`festver/views.py`**:

```python
def resultados(request, evento_id):
    """
    Resultados do evento (RF09, RF10, RF11).
    DECISÃO D4: dois rankings separados por categoria —
    pódio do júri (média das notas, RN03/RN04) e
    ranking popular (contagem de votos). Não se misturam.
    Visível apenas quando o organizador publica (resultados_publicados).
    """
    evento = get_object_or_404(Evento, pk=evento_id)

    if not evento.resultados_publicados:
        messages.error(request, 'Os resultados deste evento ainda não foram publicados.')
        return redirect('festver:detalhe_evento', evento_id=evento.id)

    quadro = []
    for categoria in evento.categorias.all():
        homologadas = categoria.inscricoes.filter(
            status=Inscricao.Status.HOMOLOGADA
        )

        # Ranking do júri (RN04): maior média primeiro.
        # O truque da tupla: primeiro separa quem NÃO tem nota
        # (True vai para o fim), depois ordena pela média NEGATIVA
        # (que inverte para decrescente).
        ranking_juri = sorted(
            homologadas,
            key=lambda i: (i.media_juri is None, -(i.media_juri or 0)),
        )

        # Ranking popular: ordena pela contagem de votos, decrescente.
        ranking_popular = sorted(
            homologadas,
            key=lambda i: i.total_votos_populares,
            reverse=True,
        )

        quadro.append({
            'categoria': categoria,
            'ranking_juri': ranking_juri,
            'ranking_popular': ranking_popular,
        })

    return render(
        request,
        'festver/resultados.html',
        {'evento': evento, 'quadro': quadro},
    )
```

> ⚠️ **Armadilha clássica de Python:** a primeira versão desse ranking foi escrita com
> `key=lambda i: (i.media_juri is None, i.media_juri)` — que ordena **crescente** (a
> pior média em primeiro lugar!). Ordenação envolvendo `None` e ordem decrescente
> merece sempre um teste com dados de verdade, **com mais de uma obra**. Um pódio de
> uma obra só "funciona" com qualquer ordenação.

Rota em **`festver/urls.py`**:

```python
    path('evento/<int:evento_id>/resultados/', views.resultados, name='resultados'),
```

**Conceitos-chave:**

- **A view monta a estrutura, o template só exibe**: a lista `quadro` é preparada em
  Python, onde a lógica é testável; o template fica "burro" de propósito.
- **Honestidade técnica**: ordenar com `sorted` em Python funciona perfeitamente na
  escala do FestVer (dezenas de obras). Num sistema grande, isso seria feito no banco
  com `annotate(Avg('avaliacoes__nota'))` e `order_by` — fica como evolução (é o
  "jeito profissional").

---

# PARTE 3 — Visual com Bootstrap 5 e navegação

## Passo 13 — Bootstrap via CDN + todos os templates finais

Bootstrap via CDN não adiciona complexidade de build: uma linha no `<head>`.
E aqui está a grande lição de arquitetura: **nenhuma view mudou, nenhum model mudou —
só templates**. O visual troca inteiro sem tocar na lógica. Isso é o padrão MTV
(Model-Template-View) do Django se provando na prática.

### `templates/base.html` (substituir TODO o conteúdo)

```html
{% load static %}
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block titulo %}Portal LABSOFT{% endblock %} — IFRS Veranópolis</title>

    <!-- Bootstrap 5 via CDN: sem instalação, sem build -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
        /* Só o que o Bootstrap não dá: a identidade do portal */
        :root { --labsoft-verde: #1e5b3f; }
        .navbar-labsoft { background-color: var(--labsoft-verde); }
        body { background-color: #f4f6f8; display: flex; flex-direction: column; min-height: 100vh; }
        main { flex: 1; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark navbar-labsoft mb-4">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">LABSOFT · IFRS Veranópolis</a>
            <div class="d-flex align-items-center gap-3">
                {% if user.is_authenticated %}
                    <span class="text-white">Olá, {{ user.first_name|default:user.username }}</span>
                    {% if user.is_staff %}
                        <a class="btn btn-outline-light btn-sm" href="/admin/">Admin</a>
                    {% endif %}
                {% else %}
                    <a class="btn btn-outline-light btn-sm" href="/admin/">Entrar</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <main class="container">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{% if message.tags == 'error' %}danger{% else %}{{ message.tags }}{% endif %} alert-dismissible fade show">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endif %}

        {% block conteudo %}{% endblock %}
    </main>

    <footer class="text-center text-muted py-4 mt-5 small">
        Laboratório de Desenvolvimento de Software — IFRS Campus Veranópolis
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

**Detalhes que valem nota:**

- **Bloco de mensagens no base**: qualquer view de qualquer módulo que use
  `messages` ganha o feedback automaticamente — dividendo da herança de templates.
- **`alert-{{ message.tags }}`**: as tags do Django (`success`, `error`...) quase
  coincidem com as classes do Bootstrap — só `error` → `danger` precisa do `if`.
- **Truque do rodapé** (`flex` no body + `flex: 1` no main): sem isso, em páginas
  curtas o footer flutua no meio da tela.

### `templates/core/home.html` (substituir)

```html
{% extends 'base.html' %}

{% block titulo %}Início{% endblock %}

{% block conteudo %}
    <div class="p-5 mb-4 bg-white rounded-3 shadow-sm">
        <h1 class="display-5">Portal LABSOFT</h1>
        <p class="lead">Sistemas desenvolvidos pelo Laboratório de Desenvolvimento
           de Software do IFRS Campus Veranópolis.</p>
    </div>

    <h2 class="h4 mb-3">Módulos</h2>
    <div class="row">
        <div class="col-md-4">
            <div class="card shadow-sm">
                <div class="card-body">
                    <h5 class="card-title">🎭 FestVer</h5>
                    <p class="card-text text-muted">Inscrições e votação para apresentações estudantis.</p>
                    <a href="{% url 'festver:lista_eventos' %}" class="btn btn-success">Acessar</a>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
```

### `templates/festver/lista_eventos.html`

```html
{% extends 'base.html' %}

{% block titulo %}FestVer — Eventos{% endblock %}

{% block conteudo %}
    <a href="{% url 'home' %}" class="btn btn-link btn-sm text-decoration-none px-0 mb-2">← Portal LABSOFT</a>
    <h1 class="mb-4">FestVer — Eventos</h1>

    <div class="row">
        {% for evento in eventos %}
            <div class="col-md-6 mb-3">
                <div class="card h-100 shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title">{{ evento.nome }}</h5>
                        <p class="card-text text-muted">{{ evento.descricao|truncatewords:20 }}</p>
                        {% if evento.inscricoes_abertas %}
                            <span class="badge bg-success mb-2">Inscrições abertas</span>
                        {% endif %}
                        {% if evento.votacao_aberta %}
                            <span class="badge bg-primary mb-2">Votação aberta</span>
                        {% endif %}
                        <div>
                            <a href="{% url 'festver:detalhe_evento' evento.id %}" class="btn btn-sm btn-outline-success">Ver evento</a>
                        </div>
                    </div>
                </div>
            </div>
        {% empty %}
            <p>Nenhum evento cadastrado ainda.</p>
        {% endfor %}
    </div>
{% endblock %}
```

### `templates/festver/detalhe_evento.html`

```html
{% extends 'base.html' %}

{% block titulo %}{{ evento.nome }}{% endblock %}

{% block conteudo %}
    <a href="{% url 'festver:lista_eventos' %}" class="btn btn-link btn-sm text-decoration-none px-0 mb-2">← Todos os eventos</a>
    <h1>{{ evento.nome }}</h1>
    <p class="text-muted">{{ evento.descricao }}</p>

    <div class="mb-4">
        {% if evento.inscricoes_abertas %}
            <a href="{% url 'festver:inscrever' evento.id %}" class="btn btn-success">➜ Inscreva sua obra</a>
        {% endif %}
        {% if evento.resultados_publicados %}
            <a href="{% url 'festver:resultados' evento.id %}" class="btn btn-warning">🏆 Ver resultados</a>
        {% endif %}
    </div>

    {% for categoria in evento.categorias.all %}
        <div class="card mb-4 shadow-sm">
            <div class="card-header fw-bold">{{ categoria.nome }}</div>
            <ul class="list-group list-group-flush">
                {% for inscricao in categoria.inscricoes.all %}
                    {% if inscricao.status == 'HOM' %}
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <span>
                                {{ inscricao.titulo_obra }}
                                <small class="text-muted">— {{ inscricao.participante.first_name|default:inscricao.participante.username }}</small>
                            </span>
                            <span class="d-flex gap-2">
                                {% if user in evento.jurados.all and evento.votacao_aberta %}
                                    <a href="{% url 'festver:avaliar' inscricao.id %}" class="btn btn-sm btn-outline-primary">Avaliar</a>
                                {% endif %}
                                {% if user.is_authenticated and evento.votacao_aberta %}
                                    <form method="post" action="{% url 'festver:votar' inscricao.id %}">
                                        {% csrf_token %}
                                        <button type="submit" class="btn btn-sm btn-primary">🗳 Votar</button>
                                    </form>
                                {% endif %}
                            </span>
                        </li>
                    {% endif %}
                {% empty %}
                    <li class="list-group-item text-muted">Nenhuma inscrição nesta categoria.</li>
                {% endfor %}
            </ul>
        </div>
    {% endfor %}
{% endblock %}
```

> ⚠️ **Atenção ao aninhamento!** O `{% if %}` do botão votar fica **dentro** do
> `<li>`, ao lado do link Avaliar. E o link/botão de cada inscrição fica dentro do
> `{% if inscricao.status == 'HOM' %}` — que fica dentro do `{% for %}` — nunca dentro
> do `{% empty %}` (que só roda quando a lista está **vazia**!). Em template Django a
> indentação não é obrigatória como em Python, mas é ela que deixa erros de
> aninhamento visíveis a olho nu.

### `templates/festver/inscrever.html`

```html
{% extends 'base.html' %}

{% block titulo %}Inscrição — {{ evento.nome }}{% endblock %}

{% block conteudo %}
    <a href="{% url 'festver:detalhe_evento' evento.id %}" class="btn btn-link btn-sm text-decoration-none px-0 mb-2">← Voltar ao evento</a>
    <div class="row justify-content-center">
        <div class="col-md-7">
            <div class="card shadow-sm">
                <div class="card-header fw-bold">Inscrição — {{ evento.nome }}</div>
                <div class="card-body">
                    <form method="post" enctype="multipart/form-data">
                        {% csrf_token %}
                        {% for campo in form %}
                            <div class="mb-3">
                                <label class="form-label" for="{{ campo.id_for_label }}">{{ campo.label }}</label>
                                {{ campo }}
                                {% if campo.errors %}
                                    <div class="text-danger small">{{ campo.errors }}</div>
                                {% endif %}
                            </div>
                        {% endfor %}
                        <button type="submit" class="btn btn-success">Enviar inscrição</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
```

### `templates/festver/avaliar.html`

```html
{% extends 'base.html' %}

{% block titulo %}Avaliar — {{ inscricao.titulo_obra }}{% endblock %}

{% block conteudo %}
    <a href="{% url 'festver:detalhe_evento' inscricao.categoria.evento.id %}" class="btn btn-link btn-sm text-decoration-none px-0 mb-2">← Voltar ao evento</a>
    <div class="row justify-content-center">
        <div class="col-md-7">
            <div class="card shadow-sm">
                <div class="card-header fw-bold">Avaliar: {{ inscricao.titulo_obra }}</div>
                <div class="card-body">
                    <p class="text-muted">
                        Categoria: {{ inscricao.categoria.nome }} —
                        Participante: {{ inscricao.participante.first_name|default:inscricao.participante.username }}
                    </p>
                    <p><a href="{{ inscricao.arquivo_obra.url }}" target="_blank" class="btn btn-sm btn-outline-secondary">📎 Ver obra enviada</a></p>

                    <form method="post">
                        {% csrf_token %}
                        {% for linha in linhas %}
                            <div class="mb-3">
                                <label class="form-label" for="nota_{{ linha.criterio.id }}">{{ linha.criterio.nome }}</label>
                                <input type="number" class="form-control" name="nota_{{ linha.criterio.id }}"
                                       id="nota_{{ linha.criterio.id }}"
                                       min="0" max="10" step="0.1"
                                       value="{{ linha.nota }}" required>
                            </div>
                        {% endfor %}
                        <button type="submit" class="btn btn-primary">Salvar notas</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
```

> Repare na navegação por relacionamentos no link de voltar:
> `inscricao.categoria.evento.id` — o mesmo "atravessar ForeignKeys" que vimos no
> admin com `categoria__evento`, só que com ponto em vez de duplo underline.
> E o motivo de usarmos links explícitos em vez de `javascript:history.back()`:
> o histórico do navegador é imprevisível; o link declarado leva sempre ao lugar
> certo da hierarquia.

### `templates/festver/resultados.html`

```html
{% extends 'base.html' %}

{% block titulo %}Resultados — {{ evento.nome }}{% endblock %}

{% block conteudo %}
    <a href="{% url 'festver:detalhe_evento' evento.id %}" class="btn btn-link btn-sm text-decoration-none px-0 mb-2">← Voltar ao evento</a>
    <h1 class="mb-4">🏆 Resultados — {{ evento.nome }}</h1>

    {% for bloco in quadro %}
        <h2 class="mt-4">{{ bloco.categoria.nome }}</h2>

        <div class="row">
            <div class="col-md-6">
                <div class="card shadow-sm mb-3">
                    <div class="card-header fw-bold">Júri técnico</div>
                    <ol class="list-group list-group-numbered list-group-flush">
                        {% for inscricao in bloco.ranking_juri %}
                            <li class="list-group-item d-flex justify-content-between align-items-center {% if forloop.first %}fw-bold{% endif %}">
                                <span>
                                    {% if forloop.first %}🥇{% elif forloop.counter == 2 %}🥈{% elif forloop.counter == 3 %}🥉{% endif %}
                                    {{ inscricao.titulo_obra }}
                                    <small class="text-muted">— {{ inscricao.participante.first_name|default:inscricao.participante.username }}</small>
                                </span>
                                {% if inscricao.media_juri is not None %}
                                    <span class="badge bg-primary rounded-pill">{{ inscricao.media_juri|floatformat:2 }}</span>
                                {% else %}
                                    <span class="badge bg-secondary rounded-pill">sem notas</span>
                                {% endif %}
                            </li>
                        {% empty %}
                            <li class="list-group-item text-muted">Nenhuma obra homologada.</li>
                        {% endfor %}
                    </ol>
                </div>
            </div>

            <div class="col-md-6">
                <div class="card shadow-sm mb-3">
                    <div class="card-header fw-bold">Voto popular</div>
                    <ol class="list-group list-group-numbered list-group-flush">
                        {% for inscricao in bloco.ranking_popular %}
                            <li class="list-group-item d-flex justify-content-between align-items-center {% if forloop.first %}fw-bold{% endif %}">
                                <span>
                                    {% if forloop.first %}🥇{% elif forloop.counter == 2 %}🥈{% elif forloop.counter == 3 %}🥉{% endif %}
                                    {{ inscricao.titulo_obra }}
                                    <small class="text-muted">— {{ inscricao.participante.first_name|default:inscricao.participante.username }}</small>
                                </span>
                                <span class="badge bg-success rounded-pill">{{ inscricao.total_votos_populares }} voto{{ inscricao.total_votos_populares|pluralize }}</span>
                            </li>
                        {% empty %}
                            <li class="list-group-item text-muted">Nenhuma obra homologada.</li>
                        {% endfor %}
                    </ol>
                </div>
            </div>
        </div>
    {% endfor %}
{% endblock %}
```

**Filtros de template usados:** `floatformat:2` (formata a média), `pluralize`
("1 voto", "2 votos"), `truncatewords`, `default`. Formatação é trabalho do template,
não da view.

## Passo 14 — Teste do fluxo completo

Roteiro de teste (ordem importa!):

1. **Admin** → criar evento com categorias e critérios; marcar `inscricoes_abertas`;
   associar um usuário como jurado (lembre da setinha → e de salvar!).
2. **Site** → `/festver/` → entrar no evento → **Inscrever obra** com um arquivo.
3. **Admin** → Inscrições → mudar status para **Homologada** (direto na lista).
4. **Admin** → marcar `votacao_aberta` no evento.
5. **Site** → página do evento → a obra aparece com os botões **Avaliar** e **Votar**.
6. **Avaliar** → dar notas nos critérios → salvar → reabrir e ver as notas
   pré-preenchidas (o `update_or_create` em ação).
7. **Votar** → primeira vez: "Voto registrado"; segunda vez em outra obra da mesma
   categoria: "voto transferido". No admin, conferir que existe **um único** voto.
8. **Admin** → marcar `resultados_publicados`.
9. **Site** → **🏆 Ver resultados** → pódio do júri com médias e ranking popular.

> 💡 **Dica de apresentação:** crie 3–4 inscrições com nomes realistas e vote/avalie
> de forma variada. Pódio com uma obra só não impressiona; com quatro obras disputando
> e medalhas 🥇🥈🥉, sim.

## Quadro de Troubleshooting (erros que REALMENTE aconteceram construindo isto)

| Sintoma | Causa | Lição |
|---|---|---|
| `O termo '...Activate.ps1' não é reconhecido` | O venv não foi criado nessa pasta, ou foi criado com outro nome. | `dir` para conferir; criação de venv termina em silêncio. |
| Link/botão não aparece na página | Alguma condição do `{% if %}` é falsa (votação fechada? jurado não associado? inscrição não homologada? logado com outro usuário?) | Checar cada condição do `if`, uma a uma, no admin. |
| Botão sumiu / lista mostra "nenhuma inscrição" com inscrição existindo | Bloco colado no lugar errado do template (ex.: dentro do `{% empty %}`, que só roda com lista vazia). | Template Django **não reclama de variável inexistente** — renderiza vazio em silêncio. Indentação revela aninhamento errado. |
| 404 numa URL que "deveria existir" | URL montada com o id errado (ex.: id do evento onde a rota pede id da inscrição). | A página de 404 do Django (com DEBUG=True) **lista todos os padrões de URL** — aprenda a ler essa lista. |
| Arquivo do upload "não chega" na view | Faltou `enctype="multipart/form-data"` no form OU `request.FILES` na view. | Os dois são obrigatórios, sempre juntos. |
| Edição no template não faz efeito | Arquivo não salvo no editor (bolinha na aba do VS Code). | `Ctrl+S` — ou ative o Auto Save. |
| Template quebra de formas estranhas após muitas edições | Edições acumuladas em cima de código quebrado. | Substituir o arquivo inteiro por uma versão conhecida-boa é mais rápido que caçar o erro — é o "git checkout dos pobres". Melhor ainda: usar Git de verdade. |
| Pódio em ordem invertida | `sorted` crescente onde deveria ser decrescente; `None` no meio complica. | Testar ordenação **com mais de um item** e com itens sem nota. |

## Passo 15 — Git: pontos de restauração

```powershell
git init
```

Crie o arquivo **`.gitignore`** na raiz:

```
venv/
venv_labsoft/
__pycache__/
*.pyc
db.sqlite3
media/
.vscode/
```

**Por quê cada linha:** o venv se recria com o `requirements.txt`; o banco SQLite e os
uploads são dados locais de teste, não código; `__pycache__` é lixo de compilação.

```powershell
git add .
git commit -m "MVP do Portal LABSOFT com modulo FestVer"
```

A partir daqui, um commit a cada passo concluído = pontos de restauração para quando
um template quebrar "misteriosamente".

---

# PARTE 4 — Exercícios (com solução completa)

O desenvolvimento revelou requisitos que o documento original não previa e deixou
outros como pendência. Cada exercício abaixo indica **o que fazer**, **qual padrão do
tutorial reutilizar** e traz **a solução completa** — cole o código, faça funcionar,
e depois **leia até entender cada linha**: na apresentação do módulo, vocês vão
explicar essas partes.

Estão em ordem de dificuldade. Recomendação: um commit no Git ao final de cada um.

---

## Exercício 1 — Tela "Minhas inscrições" (RF13) ⭐

**O problema:** hoje o inscrito não tem como saber se sua obra foi homologada ou
rejeitada — o RF13 ("acompanhar o andamento") não está atendido.

**O que fazer:** uma página `/festver/minhas-inscricoes/` listando as inscrições do
usuário logado, com o status de cada uma.

**Padrão a reutilizar:** view com `@login_required` + `filter` + template com card
(igual às que você já viu três vezes).

### Solução

**1)** Adicione ao final de **`festver/views.py`**:

```python
@login_required
def minhas_inscricoes(request):
    """
    Tela do inscrito para acompanhar suas obras (RF13).
    Filtra pelas inscrições DO USUÁRIO LOGADO — cada um vê só as suas.
    """
    inscricoes = Inscricao.objects.filter(
        participante=request.user
    ).order_by('-criada_em')
    return render(
        request,
        'festver/minhas_inscricoes.html',
        {'inscricoes': inscricoes},
    )
```

**2)** Rota em **`festver/urls.py`**:

```python
    path('minhas-inscricoes/', views.minhas_inscricoes, name='minhas_inscricoes'),
```

**3)** Crie **`templates/festver/minhas_inscricoes.html`**:

```html
{% extends 'base.html' %}

{% block titulo %}Minhas inscrições{% endblock %}

{% block conteudo %}
    <a href="{% url 'festver:lista_eventos' %}" class="btn btn-link btn-sm text-decoration-none px-0 mb-2">← Todos os eventos</a>
    <h1 class="mb-4">Minhas inscrições</h1>

    <div class="card shadow-sm">
        <ul class="list-group list-group-flush">
            {% for inscricao in inscricoes %}
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <span>
                        {{ inscricao.titulo_obra }}
                        <small class="text-muted">
                            — {{ inscricao.categoria.nome }} ({{ inscricao.categoria.evento.nome }})
                            — enviada em {{ inscricao.criada_em|date:"d/m/Y" }}
                        </small>
                    </span>
                    {% if inscricao.status == 'HOM' %}
                        <span class="badge bg-success">Homologada</span>
                    {% elif inscricao.status == 'REJ' %}
                        <span class="badge bg-danger">Rejeitada</span>
                    {% else %}
                        <span class="badge bg-warning text-dark">Pendente</span>
                    {% endif %}
                </li>
            {% empty %}
                <li class="list-group-item text-muted">Você ainda não inscreveu nenhuma obra.</li>
            {% endfor %}
        </ul>
    </div>
{% endblock %}
```

**4)** Adicione o link no menu, em **`templates/base.html`** — dentro do
`{% if user.is_authenticated %}` da navbar, antes do "Olá":

```html
                    <a class="btn btn-outline-light btn-sm" href="{% url 'festver:minhas_inscricoes' %}">Minhas inscrições</a>
```

**Teste:** inscreva-se com um usuário, deixe pendente, e veja o badge amarelo;
homologue no admin e recarregue — badge verde.

**Para entender:** por que o `filter(participante=request.user)` é uma questão de
**segurança**, e não só de conveniência? O que aconteceria se a view listasse
`Inscricao.objects.all()`?

---

## Exercício 2 — Validação do upload (formato e tamanho) ⭐⭐

**O problema:** o `FileField` aceita **qualquer** arquivo de **qualquer** tamanho.
Num sistema aberto à comunidade (RNF04), isso é um risco real: alguém pode subir um
executável ou um vídeo de 4 GB.

**O que fazer:** aceitar somente PDF, MP3, MP4, JPG e PNG, com no máximo 20 MB.

**Padrão a reutilizar:** validators, como os `MinValueValidator`/`MaxValueValidator`
que já usamos na nota da `Avaliacao` — só que agora escrevendo um validator próprio.

### Solução

**1)** Crie o arquivo **`festver/validators.py`** (novo):

```python
from django.core.exceptions import ValidationError

TAMANHO_MAXIMO_MB = 20
EXTENSOES_PERMITIDAS = ['.pdf', '.mp3', '.mp4', '.jpg', '.jpeg', '.png']


def validar_tamanho_obra(arquivo):
    """Rejeita arquivos maiores que TAMANHO_MAXIMO_MB."""
    if arquivo.size > TAMANHO_MAXIMO_MB * 1024 * 1024:
        raise ValidationError(
            f'O arquivo tem {arquivo.size / (1024 * 1024):.1f} MB. '
            f'O tamanho máximo permitido é {TAMANHO_MAXIMO_MB} MB.'
        )
```

**2)** Em **`festver/models.py`**, importe no topo:

```python
from django.core.validators import FileExtensionValidator

from .validators import validar_tamanho_obra
```

E altere o campo `arquivo_obra` do model `Inscricao`:

```python
    arquivo_obra = models.FileField(
        'arquivo da obra',
        upload_to='festver/obras/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'mp3', 'mp4', 'jpg', 'jpeg', 'png'],
                message='Formato não permitido. Envie PDF, MP3, MP4, JPG ou PNG.',
            ),
            validar_tamanho_obra,
        ],
        help_text='Formatos: PDF, MP3, MP4, JPG, PNG. Máximo 20 MB.',
    )
```

**3)** Como mudamos o model, gere a migration:

```powershell
python manage.py makemigrations
python manage.py migrate
```

**Teste:** tente inscrever um `.txt` ou um `.exe` — o formulário deve recusar com a
mensagem, **sem** salvar nada (o erro aparece no campo, pelo bloco `campo.errors` que
o template de inscrição já tem).

**Para entender:** o `FileExtensionValidator` já existe pronto no Django (validação
por extensão); o de tamanho tivemos que escrever. Por que a validação fica no
**model** e não na view? (Dica: quantos caminhos existem para criar uma Inscricao?
Lembre do admin...)

---

## Exercício 3 — Relatório CSV de inscrições (RF12) ⭐⭐

**O problema:** o RF12 (relatórios) não foi implementado. O organizador precisa, no
mínimo, de uma planilha de inscritos por evento.

**O que fazer:** um botão no admin? Não — mais simples: uma URL
`/festver/evento/1/relatorio/` que baixa um CSV, restrita a staff.

**Padrão a reutilizar:** uma view, só que devolvendo `HttpResponse` com CSV em vez de
`render` com template. Nem toda view devolve HTML!

### Solução

**1)** Adicione ao final de **`festver/views.py`**:

```python
import csv

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse


@staff_member_required
def relatorio_inscricoes(request, evento_id):
    """
    Relatório CSV das inscrições de um evento (RF12).
    @staff_member_required: só o organizador (staff) acessa;
    quem não for staff é mandado para o login do admin.
    """
    evento = get_object_or_404(Evento, pk=evento_id)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="inscricoes_{evento.id}.csv"'
    )
    # BOM: faz o Excel abrir o UTF-8 com acentos corretos
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Categoria', 'Título da obra', 'Participante',
        'Status', 'Média do júri', 'Votos populares', 'Data',
    ])

    inscricoes = Inscricao.objects.filter(
        categoria__evento=evento
    ).select_related('categoria', 'participante').order_by('categoria__nome')

    for i in inscricoes:
        media = i.media_juri
        writer.writerow([
            i.categoria.nome,
            i.titulo_obra,
            i.participante.get_full_name() or i.participante.username,
            i.get_status_display(),
            f'{media:.2f}'.replace('.', ',') if media is not None else '',
            i.total_votos_populares,
            i.criada_em.strftime('%d/%m/%Y %H:%M'),
        ])

    return response
```

**2)** Rota em **`festver/urls.py`**:

```python
    path('evento/<int:evento_id>/relatorio/', views.relatorio_inscricoes, name='relatorio'),
```

**3)** Link na página do evento, em **`templates/festver/detalhe_evento.html`** —
dentro da `<div class="mb-4">` dos botões:

```html
        {% if user.is_staff %}
            <a href="{% url 'festver:relatorio' evento.id %}" class="btn btn-outline-secondary">📄 Relatório CSV</a>
        {% endif %}
```

**Teste:** logado como staff, clique no botão — um CSV baixa e abre no Excel com
acentos corretos e uma linha por inscrição (inclusive pendentes e rejeitadas — o
organizador vê tudo).

**Para entender:** três detalhes profissionais escondidos aí — o `\ufeff` (BOM) e o
`delimiter=';'` (Excel brasileiro usa ponto-e-vírgula!); o `select_related`, que evita
uma consulta ao banco por linha do relatório; e o `get_status_display()`, que traduz
`'HOM'` para `'Homologada'` automaticamente (o Django gera esse método para todo campo
com `choices`).

---

## Exercício 4 — Aviso por e-mail na homologação (RF17) ⭐⭐⭐

**O problema:** o RF17 (avisos por e-mail) ficou de fora do MVP. O aviso mais valioso
é: "sua inscrição foi homologada/rejeitada".

**O que fazer:** enviar e-mail ao participante **quando o status da inscrição muda**.
Sem servidor de e-mail ainda: usaremos o backend de **console** do Django, que
"envia" imprimindo no terminal — perfeito para desenvolvimento.

**Padrão novo:** sobrescrever o `save()` do model detectando mudança de campo (vocês
já viram um `save()` customizado no `VotoPopular`).

### Solução

**1)** No final de **`config/settings.py`**:

```python
# E-mail: em desenvolvimento, "envia" imprimindo no terminal do runserver.
# Em produção, trocar por SMTP (ver comentário abaixo).
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'labsoft@veranopolis.ifrs.edu.br'

# Para produção com SMTP real, seria algo como:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = '...'
# EMAIL_HOST_PASSWORD = '...'  # NUNCA commitar senha! Usar variável de ambiente.
```

**2)** Em **`festver/models.py`**, importe no topo:

```python
from django.core.mail import send_mail
```

E, dentro da classe `Inscricao`, adicione o método `save` (depois das properties):

```python
    def save(self, *args, **kwargs):
        """
        Detecta mudança de status e avisa o participante por e-mail (RF17).
        Técnica: antes de salvar, busca a versão antiga no banco e compara.
        """
        status_antigo = None
        if self.pk:  # já existe no banco (é edição, não criação)
            status_antigo = (
                Inscricao.objects.filter(pk=self.pk)
                .values_list('status', flat=True)
                .first()
            )

        super().save(*args, **kwargs)

        mudou_para_decisao = (
            status_antigo is not None
            and status_antigo != self.status
            and self.status in (self.Status.HOMOLOGADA, self.Status.REJEITADA)
        )
        if mudou_para_decisao and self.participante.email:
            if self.status == self.Status.HOMOLOGADA:
                assunto = f'Inscrição homologada — {self.categoria.evento.nome}'
                corpo = (
                    f'Olá, {self.participante.first_name or self.participante.username}!\n\n'
                    f'Sua obra "{self.titulo_obra}" foi HOMOLOGADA na categoria '
                    f'{self.categoria.nome}. Boa sorte!\n\n'
                    f'— Organização do {self.categoria.evento.nome}'
                )
            else:
                assunto = f'Inscrição não homologada — {self.categoria.evento.nome}'
                corpo = (
                    f'Olá, {self.participante.first_name or self.participante.username}.\n\n'
                    f'Infelizmente sua obra "{self.titulo_obra}" não foi homologada '
                    f'na categoria {self.categoria.nome}. Em caso de dúvidas, '
                    f'procure a organização.\n\n'
                    f'— Organização do {self.categoria.evento.nome}'
                )
            send_mail(
                assunto,
                corpo,
                None,  # usa o DEFAULT_FROM_EMAIL
                [self.participante.email],
                fail_silently=True,  # e-mail falhando não pode travar a homologação
            )
```

**Teste:** garanta que seu usuário tem e-mail preenchido (admin → Users). Mude o
status de uma inscrição no admin e **olhe o terminal do runserver**: o e-mail completo
aparece impresso lá.

**Para entender:** três decisões importantes no código — (a) comparar com o banco
*antes* do `super().save()` é o jeito de detectar "mudou de X para Y"; (b)
`fail_silently=True`: se o servidor de e-mail cair, a homologação **não pode** falhar
junto — o e-mail é acessório, o dado é essencial; (c) por que o e-mail dispara no
model e não na view? Porque a homologação acontece pelo **admin** (`list_editable`),
que não passa pelas nossas views!

*Observação honesta:* em sistemas maiores, isso seria feito com **signals**
(`post_save`) ou uma fila de tarefas (Celery). O `save()` sobrescrito é a versão
didática — e suficiente nesta escala.

---

## Exercício 5 — Desempate no pódio (RN nova) ⭐⭐⭐

**O problema:** a especificação não define desempate, e com notas 0–10 e poucos
jurados, empates são quase certos. Hoje, dois empatados aparecem em ordem arbitrária —
numa edição real, alguém vai reclamar.

**Decisão a implementar (registrem como RN no documento!):** em caso de empate na
média do júri, desempata quem tiver **mais votos populares**; persistindo, declaram-se
empatados (mesma posição).

**Padrão a reutilizar:** a `key` do `sorted` com tupla — quanto mais elementos na
tupla, mais critérios de ordenação em cascata.

### Solução

Na view `resultados` em **`festver/views.py`**, troque o `ranking_juri` por:

```python
        # Ranking do júri com desempate por votos populares (RN de desempate):
        # a tupla ordena em cascata: 1º sem-nota para o fim,
        # 2º maior média, 3º mais votos populares.
        ranking_juri = sorted(
            homologadas,
            key=lambda i: (
                i.media_juri is None,
                -(i.media_juri or 0),
                -i.total_votos_populares,
            ),
        )
```

**Teste:** crie duas inscrições com as mesmas notas e votos populares diferentes — a
com mais votos deve vir primeiro.

**Para entender:** e o "persistindo, declaram-se empatados"? O template numera com
`list-group-numbered`, que não sabe de empates. Como exercício-desafio (sem solução
pronta!): na view, percorra o ranking e atribua a cada inscrição uma `posicao`,
repetindo o número quando média E votos forem iguais ao anterior — e exiba essa
posição no template no lugar da numeração automática.

---

## Exercício 6 — Especificação v2.0 (sem código!) ⭐⭐

O desenvolvimento **corrigiu o levantamento** — isso acontece em todo projeto real.
Atualizem o documento de requisitos para a versão 2.0, incorporando:

1. **Novo RF:** "O organizador cadastra critérios de avaliação por categoria" (hoje
   isso não existe como requisito, mas o sistema faz!).
2. **Novo RF:** homologação de inscrições, com a enumeração dos status
   (Pendente/Homologada/Rejeitada) no RF16.
3. **Novo RF:** tela "minhas inscrições" (Exercício 1) como forma de atender o RF13.
4. **Novas RN:** RN05 (voto popular: um por usuário por categoria, transferível,
   ranking separado do júri) e RN06 (desempate — Exercício 5).
5. **Novo RNF:** restrições de upload (formatos e tamanho — Exercício 2).
6. **Novo RNF:** privacidade/consentimento — o evento envolve estudantes menores de
   idade e as obras/nomes ficam públicos. O que precisa constar na ficha de inscrição?
   (Pesquisem: termo de autorização de uso de imagem/obra e LGPD para menores.)
7. **Seção "Decisões de projeto":** copiem a tabela D1–D7 do início deste tutorial —
   decisões tomadas durante o desenvolvimento fazem parte da documentação.

---

## Para onde ir depois (desafios sem solução pronta)

- **Login próprio do portal:** hoje o "Entrar" leva ao login do admin. Criar telas de
  login/logout do portal com `django.contrib.auth.views.LoginView` e `LogoutView`.
- **Página "Meu painel de jurado":** listar todas as obras que o jurado ainda não
  avaliou, entre os eventos em que é jurado.
- **Ranking no banco:** trocar o `sorted` da view de resultados por
  `annotate(media=Avg('avaliacoes__nota')).order_by('-media')` — o "jeito
  profissional" citado no Passo 12.
- **PostgreSQL:** trocar o SQLite (necessário para o RNF05 em produção).
- **O segundo módulo do portal:** escolham um sistema do campus e repitam o ciclo
  inteiro — levantamento, decisões documentadas, models, admin, views, templates.
  O FestVer é o mapa; o caminho agora é de vocês. 🚀

---

*Tutorial construído no LABSOFT — IFRS Campus Veranópolis, julho de 2026, em sessão de
desenvolvimento passo a passo com o professor. Os erros documentados no quadro de
troubleshooting aconteceram de verdade durante a construção — errar, ler o erro e
corrigir é o método.*
