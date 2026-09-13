import ipaddress

def validate_scope(task, config):
    args = task.get("arguments", [])
    target = None
    for i, arg in enumerate(args):
        if arg in ("-H", "--host", "-t"):
            if i + 1 < len(args):
                target = args[i + 1]
        elif not arg.startswith("-"):
            target = arg
    if not target:
        return True
    try:
        ip = ipaddress.ip_address(target)
        for net in config["scope"]["networks"]:
            if ip in ipaddress.ip_network(net):
                if target not in config["scope"]["exclude"]:
                    return True
        return False
    except ValueError:
        return any(target.endswith(d) for d in config["scope"]["domains"])