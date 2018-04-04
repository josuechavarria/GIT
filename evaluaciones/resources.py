from import_export import resources 
from .models import departamentos

class ImportarDepartamentos(resources.ModelResource):
    class Meta:
        model = departamentos