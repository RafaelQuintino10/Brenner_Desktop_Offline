from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from barbeiros.views import BarbeiroViewSet, FolgaViewSet
from agendamentos.views import (
    ClienteViewSet, ServicoViewSet, AgendamentoViewSet,
    PublicCatalog, PublicAvailableSlots, PublicBooking,
    PublicBarbers, PublicServices, PublicProducts,
)
from produtos.views import ProdutoViewSet
from vendas.views import VendaViewSet, RecebimentoServicoViewSet
# from balanco_financeiro.views import DespesaViewSet, ResumoFinanceiro, FechamentosView
from balanco_financeiro.views import (
    DespesaViewSet,
    ResumoFinanceiro,
    FechamentosView
)
from balanco_financeiro.relatorio_excel import RelatorioExcelView
# from config.views import LoginView, WhoAmI, LogoutView, HealthView
from config.views import (
    LoginView,
    BalconistaLoginView,
    WhoAmI,
    LogoutView,
    HealthView,
)

from balanco_financeiro.views import StatusPeriodoFinanceiro
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register('barbeiros', BarbeiroViewSet, basename='barbeiros')
router.register('folgas', FolgaViewSet, basename='folgas')
router.register('clientes', ClienteViewSet, basename='clientes')
router.register('servicos', ServicoViewSet, basename='servicos')
router.register('agendamentos', AgendamentoViewSet, basename='agendamentos')
router.register('produtos', ProdutoViewSet, basename='produtos')
router.register('vendas', VendaViewSet, basename='vendas')
router.register('recebimentos-servicos', RecebimentoServicoViewSet, basename='recebimentos-servicos')
router.register('despesas', DespesaViewSet, basename='despesas')

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/health/', HealthView.as_view()),
    # path('api/auth/login/', LoginView.as_view()),
    # path('api/auth/logout/', LogoutView.as_view()),
    # path('api/auth/me/', WhoAmI.as_view()),
    path('api/auth/login/', LoginView.as_view()),

    path(
        'api/auth/login-balconista/',
        BalconistaLoginView.as_view()
    ),

    path('api/auth/logout/', LogoutView.as_view()),
    path('api/auth/me/', WhoAmI.as_view()),
    path('api/public/catalogo/', PublicCatalog.as_view()),
    path('api/public/barbeiros/', PublicBarbers.as_view()),
    path('api/public/servicos/', PublicServices.as_view()),
    path('api/public/produtos/', PublicProducts.as_view()),
    path('api/public/disponibilidade/', PublicAvailableSlots.as_view()),
    path('api/public/agendamentos/', PublicBooking.as_view()),
    # path('api/financeiro/resumo/', ResumoFinanceiro.as_view()),
    # path('api/financeiro/fechamentos/', FechamentosView.as_view()),
    # path('api/financeiro/resumo/', ResumoFinanceiro.as_view()),
    # path('api/financeiro/excel/', RelatorioExcelView.as_view()),
    path('api/financeiro/resumo/', ResumoFinanceiro.as_view()),

    path(
        'api/financeiro/status-periodo/',
        StatusPeriodoFinanceiro.as_view()
    ),

    path('api/financeiro/excel/', RelatorioExcelView.as_view()),
    path('api/financeiro/fechamentos/', FechamentosView.as_view()),
    path('api/', include(router.urls)),
]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )