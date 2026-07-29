from django.urls import path

from . import views


urlpatterns = [
    path("", views.chat_page, name="chat"),
    path("members/<int:user_id>/", views.member_profile, name="chat_member_profile"),
    path("conversations", views.create_conversation, name="chat_create_conversation"),
    path("conversations/<int:conversation_id>/messages", views.message_list, name="chat_messages"),
    path("conversations/<int:conversation_id>/send", views.send_message, name="chat_send_message"),
    path("messages/<int:message_id>/attachment", views.message_attachment, name="chat_message_attachment"),
]
