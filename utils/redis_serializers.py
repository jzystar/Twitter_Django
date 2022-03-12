from django.core import serializers
from utils.json_encoder import JSONEncoder


class DjangoModelSerializer:

    @classmethod
    def serialize(cls, instance):
        # serializers can ONLY serialize queryset or list
        return serializers.serialize('json', [instance], cls=JSONEncoder)

    @classmethod
    def deserialize(cls, serialized_data):
        # to get original instance => [instance][0]
        return list(serializers.deserialize('json', serialized_data))[0].object