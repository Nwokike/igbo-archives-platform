from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'REST API'

    def ready(self):
        """
        Dynamically patch djangorestframework-mcp to support ImageField and FileField.
        This allows the MCP Server to expose URL upload endpoints to AI agents natively,
        while completely avoiding pollution of the standard REST API Schema.
        """
        try:
            from djangorestframework_mcp.schema import FIELD_TYPE_REGISTRY
            from rest_framework import serializers

            def get_media_url_schema(field):
                return {
                    "type": "string",
                    "format": "uri",
                    "description": f"Public HTTP/HTTPS URL to the {field.__class__.__name__.lower().replace('field', '')} file (max 50MB).",
                }

            # Inject DRF's native media fields into the schema mapping
            FIELD_TYPE_REGISTRY[serializers.ImageField] = get_media_url_schema
            FIELD_TYPE_REGISTRY[serializers.FileField] = get_media_url_schema

        except ImportError:
            # djangorestframework-mcp might not be installed in all environments
            pass
