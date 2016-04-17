from argparse import ArgumentParser
from collections import namedtuple
from inspect import isfunction, getsourcefile, signature

def _to_option(py_name):
    return '--' + py_name.replace('_', '-')

def auto_cli(live_vars, src_file):
    if live_vars is None:
        live_vars = globals()
    ArgInfo = namedtuple('ArgInfo', ('name', 'type', 'used_by'))
    functions = {}
    arg_map = {}
    for var_name, value in live_vars.items():
        if var_name.startswith('_') or not isfunction(value) or getsourcefile(value) != src_file:
            continue
        functions[var_name] = var_name + str(signature(value))
        for param_name, parameter in signature(value).parameters.items():
            if param_name in arg_map:
                arg_info = arg_map[param_name]
                arg_info.used_by.append(var_name)
            else:
                arg_info = ArgInfo(name=param_name, type=set(), used_by=[var_name])
            if parameter.default != parameter.empty:
                param_type = type(parameter.default)
                if param_type in (int, float, str, bool):
                    if len(arg_info.type) != 0:
                        pass # FIXME should probably raise something
                    arg_info.type.add(param_type)
            arg_map[param_name] = arg_info
    arg_parser = ArgumentParser()
    fn_group = arg_parser.add_argument_group("FUNCTIONS").add_mutually_exclusive_group(required=True)
    for fn_name, params in sorted(functions.items()):
        fn_group.add_argument(_to_option(fn_name), dest='_op', action='store_const', const=fn_name, help=params)
    opt_group = arg_parser.add_argument_group("FUNCTION ARGUMENTS")
    for name, ai in sorted(arg_map.items()):
        help = 'used by ' + ', '.join(fn + '()' for fn in sorted(ai.used_by))
        if ai.type:
            opt_group.add_argument(_to_option(name), help=help, type=ai.type.pop())
        else:
            opt_group.add_argument(_to_option(name), help=help)
    args = arg_parser.parse_args()
    fn = live_vars[getattr(args, '_op')]
    fn_args = {}
    for param_name, parameter in signature(fn).parameters.items():
        arg = getattr(args, param_name)
        if arg is not None:
            fn_args[param_name] = arg
    return fn(**fn_args)
