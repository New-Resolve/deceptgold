def parse_args(args):
    parsed = {}
    if args:
        if not args[0] is None:
            for arg in args:
                if '=' not in arg:
                    continue

                key, value = arg[:].split('=', 1)

                key = key.replace('-', '_').strip().lower()
                value = value.strip().lower()

                if value in ('true', '1', 'yes', 'on'):
                    parsed[key] = True
                elif value in ('false', '0', 'no', 'off'):
                    parsed[key] = False
                else:
                    parsed[key] = value

    return parsed

def my_self_developer():
    with open(__file__, 'r', encoding='utf-8') as my_self_dev:
        return '# Pyarmor' != my_self_dev.read(9).strip()