class NestedModelSerializer:
    """
    This defines Brand serializer.
    """
    def create(self, validated_data):
        view = self.context['view']
        if hasattr(view , 'get_parents_query_dict'):
            parents_query_dict = view.get_parents_query_dict(**view.kwargs)
            for key, value in parents_query_dict.items():
                validated_data[key+'_id'] = value
        return super().create(validated_data)
