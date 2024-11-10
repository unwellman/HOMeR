from homer import homer

def get_cfg (fp):
    with open(fp, 'r') as cfg:
        lines = cfg.readlines()
    ret = {}
    for line in lines:
        tmp = line.strip().split('=')
        ret[tmp[0]] = tmp[1]
    return ret
    

if __name__ == '__main__':
    cfg = get_cfg('cfg.txt')
    homer.set_admin(int(cfg['admin']))
    homer.run(cfg['app_secret'])

