from django.urls import path, include
from django.shortcuts import render
from . import views

urlpatterns = [
    path("browse/", views.browse_view, name="browse"),
    path("borrow_product/<int:product_id>/", views.borrow_product_view, name="borrow_product"),
    path("manage/", views.manage_view, name="manage"),
    path("add_product/", views.add_product_view, name="add_product"),
    path("edit_product/<int:product_id>/", views.edit_product_view, name="edit_product"),
    path("delete_product/<int:product_id>", views.delete_product_view, name="delete_product"),
    path("manage_borrow/", views.manage_borrow_view, name="manage_borrow"),
    path("manage_users/", views.manage_users_view, name="manage_users"),
    path("patron_manage_borrow/", views.patron_manage_borrow_view, name="patron_manage_borrow"),
    path("collections/", views.collections_view, name="collections"),
    path("add_to_collections/", views.add_to_collections_view, name="add_to_collections"),
    path('edit_collection/<int:collection_id>/', views.edit_collection, name='edit_collection'),
    path('delete_collection/<int:collection_id>/', views.delete_collection, name='delete_collection'),
    path('collections/<int:collection_id>/request-access/', views.request_access, name='request_access'),
    path('collections/<int:collection_id>/handle-request/<int:user_id>/', views.handle_access_request, name='handle_access_request'),

]