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
    DECISÃO: nota de 0 a 10 por critério, média simples entre
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
    DECISÃO: só inscrições HOMOLOGADAS recebem avaliação e votos.
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
    DECISÃO: um voto por usuário POR CATEGORIA. O ranking popular
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