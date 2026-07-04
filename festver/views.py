from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InscricaoForm
from .models import Evento

from django.core.exceptions import PermissionDenied

from .models import Avaliacao, Inscricao

from .models import VotoPopular


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


@login_required
def votar(request, inscricao_id):
    """
    Voto popular em uma inscrição (RF08).
    DECISÃO: um voto por usuário por categoria (unique no model).
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

def resultados(request, evento_id):
    """
    Resultados do evento (RF09, RF10, RF11).
    DECISÃO: dois rankings separados por categoria —
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

        # Ranking do júri: ordena pela property media_juri (RN04).
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