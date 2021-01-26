def to_string(bytes_data:bytes):
    return bytes_data.decode('utf-8')

def to_list(list_data):
    return [d.decode('utf-8') for d in list_data]

def to_dict(dict_data:dict):
    return {k.decode('utf-8'):v.decode('utf-8') for k,v in dict_data.items()}

def to_set(set_data:set):
    return [d.decode('utf-8') for d in set_data]