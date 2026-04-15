from import_export.admin import ImportExportModelAdmin as BaseImportExportModelAdmin


class EmptyRowsFilteringResourceMixin:
    @staticmethod
    def _is_empty_cell(value):
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        return False

    @classmethod
    def _is_empty_row(cls, row):
        return all(cls._is_empty_cell(value) for value in row)

    def before_import(self, dataset, **kwargs):
        super().before_import(dataset, **kwargs)

        for row_index in range(len(dataset) - 1, -1, -1):
            if self._is_empty_row(dataset[row_index]):
                del dataset[row_index]


class ImportExportModelAdmin(BaseImportExportModelAdmin):
    _resource_class_cache = {}

    @classmethod
    def _with_empty_rows_filter(cls, resource_class):
        if issubclass(resource_class, EmptyRowsFilteringResourceMixin):
            return resource_class

        cached_resource_class = cls._resource_class_cache.get(resource_class)
        if cached_resource_class:
            return cached_resource_class

        filtered_resource_class = type(
            f"{resource_class.__name__}WithEmptyRowsFiltering",
            (EmptyRowsFilteringResourceMixin, resource_class),
            {},
        )
        cls._resource_class_cache[resource_class] = filtered_resource_class
        return filtered_resource_class

    def get_import_resource_classes(self, request):
        resource_classes = super().get_import_resource_classes(request)
        if not resource_classes:
            return resource_classes
        return [
            self._with_empty_rows_filter(resource_class)
            for resource_class in resource_classes
        ]
