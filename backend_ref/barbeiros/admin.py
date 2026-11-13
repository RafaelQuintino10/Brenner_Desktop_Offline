from django.contrib import admin
from .models import Barbeiro, HorarioBarbeiro, Folga


class HorarioInline(admin.TabularInline):
    model = HorarioBarbeiro
    extra = 0


@admin.register(Barbeiro)
class BarbeiroAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome', 'ativo', 'comissao_servico', 'comissao_produto']
    list_filter = ['ativo']
    search_fields = ['nome']
    inlines = [HorarioInline]


@admin.register(Folga)
class FolgaAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'data', 'motivo']
    list_filter = ['data']
