from django.contrib import admin
from .models import Despesa, Fechamento, PeriodoFinanceiro


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'data', 'valor']
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Fechamento)
class FechamentoAdmin(admin.ModelAdmin):
    list_display = ['mes', 'saldo_proprietario', 'fechado_em']
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PeriodoFinanceiro)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ['mes', 'fechado']
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
