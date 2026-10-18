from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user","role","department","created_at"]
    list_filter  = ["role"]
