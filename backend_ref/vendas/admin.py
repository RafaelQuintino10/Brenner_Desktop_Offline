from django.contrib import admin
from .models import Venda, VendaServico


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ['data', 'produto', 'barbeiro', 'quantidade', 'valor_total', 'comissao', 'estornada']
    list_filter = ['data', 'estornada']

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VendaServico)
class VendaServicoAdmin(admin.ModelAdmin):
    list_display = ['data', 'agendamento', 'barbeiro', 'valor', 'comissao']

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
