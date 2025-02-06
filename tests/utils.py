from io import StringIO


class NamedStringIO(StringIO):
    def __init__(self, *args: str, name: str = "__init__.py") -> None:
        super().__init__(*args)
        self.name = name
