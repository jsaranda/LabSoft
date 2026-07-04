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
        if evento is not None:
            self.fields['categoria'].queryset = evento.categorias.all()
        # Aplica as classes do Bootstrap a todos os campos
        for nome, campo in self.fields.items():
            if nome == 'categoria':
                campo.widget.attrs['class'] = 'form-select'
            else:
                campo.widget.attrs['class'] = 'form-control'