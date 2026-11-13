from django.contrib import admin
from .models import Cliente, Servico, Agendamento


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'criado_em']
    search_fields = ['nome', 'telefone']


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco', 'duracao_minutos', 'ativo']
    list_filter = ['ativo']


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'data', 'hora', 'cliente', 'barbeiro', 'servico', 'status', 'pago']
    list_filter = ['data', 'status', 'barbeiro']
    search_fields = ['cliente__nome', 'cliente__telefone']
    readonly_fields = ['duracao_minutos', 'valor_cobrado']

    def has_add_permission(self, request):
        # Para garantir checks transacionais, criar agendamentos pela API.
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
