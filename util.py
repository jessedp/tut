def chunks(l, n):
    """Yield successive n-sized chunks from l"""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def print_dict(dictionary, prefix='\t', braces=1):
    """ Recursively prints nested dictionaries."""

    for key, value in dictionary.items():
        if isinstance(value, dict):
            print()
            print('%s%s%s%s' % (prefix, braces * '[', key, braces * ']'))

            print_dict(value, prefix + '  ', braces + 1)
        else:
            width = 20 - len(prefix)
            w_fmt = '{:' + str(width) + '}'
            txt = prefix + w_fmt.format(key) + " = " + str(value)
            print(txt)
            # print( + '%s = %s' % (key, value))
