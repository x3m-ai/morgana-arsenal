import marshmallow as ma

from app.objects.interfaces.i_object import FirstClassObjectInterface
from app.utility.base_object import BaseObject


class TagSchema(ma.Schema):
    name = ma.fields.String(required=True)
    value = ma.fields.String(required=True)
    created = ma.fields.DateTime(format=BaseObject.TIME_FORMAT, dump_only=True)

    @ma.post_load
    def build_tag(self, data, **kwargs):
        return None if kwargs.get('partial') is True else Tag(**data)


class Tag(FirstClassObjectInterface, BaseObject):
    """
    Tag object for categorizing and labeling agents and operations.
    Tags have a name and a value and can be associated with multiple objects.
    """

    schema = TagSchema()

    @property
    def unique(self):
        return self.hash(f'{self.name}:{self.value}')

    @property
    def display(self):
        return self.schema.dump(self)

    def __init__(self, name, value):
        super().__init__()
        from datetime import datetime, timezone
        self.name = name
        self.value = value
        self.created = datetime.now(timezone.utc)

    def __eq__(self, other):
        return isinstance(other, Tag) and self.name == other.name and self.value == other.value

    def __hash__(self):
        return hash(self.unique)

    def store(self, ram):
        existing = self.retrieve(ram['tags'], self.unique)
        if not existing:
            ram['tags'].append(self)
            return self.retrieve(ram['tags'], self.unique)
        return existing

    def match(self, criteria):
        if not criteria:
            return True
        for k, v in criteria.items():
            if getattr(self, k, None) != v:
                return False
        return True
