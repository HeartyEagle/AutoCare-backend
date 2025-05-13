def KeyType(basetype, primary=False, **kwargs):
    class _TypedKey(basetype):
        _primary = primary
        _options = kwargs
        _basetype = basetype

        def __new__(cls, value):
            return super().__new__(cls, value)

        def __repr__(self):
            return f"{basetype.__name__}({super().__repr__()})"

    return _TypedKey
