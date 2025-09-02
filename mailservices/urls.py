from django.urls import path
from django.views.decorators.cache import cache_page

from mailservices.apps import MailsevicesConfig

# from .views import (
#     HomeView,
#     ContactsView,
#     ProductDetailView,
#     ProductsCreateView,
#     ProductsDeleteView,
#     ProductsUpdateView,
#     ProductsByCategoryView,
# )

# app_name = MailsevicesConfig.name
#
# urlpatterns = [
#     path("", HomeView.as_view(), name="home"),  # главная страница
#     path("contacts/", ContactsView.as_view(), name="contacts"),
#     path("product/<int:pk>/", cache_page(15)(ProductDetailView.as_view()), name="product"),
#     path("product/create/", ProductsCreateView.as_view(), name="create"),
#     path("product/update/<int:pk>/", ProductsUpdateView.as_view(), name="update"),
#     path("product/delete/<int:pk>/", ProductsDeleteView.as_view(), name="delete"),
#     path("category/<int:category_id>/",ProductsByCategoryView.as_view(),name="products_by_category",),
# ]