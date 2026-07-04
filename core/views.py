from django.shortcuts import render


def home(request):
    """Página inicial do portal, que lista os módulos disponíveis."""
    return render(request, 'core/home.html')