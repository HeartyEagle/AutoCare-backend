def object_to_dict(obj) -> dict:
    """
    Convert a dataclass object to a dictionary.
    Args:
        obj (dataclass): The dataclass object to convert.
    Returns:
        dict: Dictionary representation of the dataclass object.
    """
    if not obj:
        return {}
    return {key: value for key, value in vars(obj).items() if not key.startswith("_")}
