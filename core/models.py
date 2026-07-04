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