""" 函数集合 """


def parse_shortcut(path: str, *, os='Windows') -> str:
    """ 解析快捷方式的实际指向地址 
    ## Parameter
    `path` - 快捷方式的路径\n
    `os` - 操作系统 ['Windows','Linux']
    ## Return
    """
    if os == 'Windows':
        from win32com.client import Dispatch
        shell = Dispatch("WScript.Shell")
        return shell.CreateShortCut(path).Targetpath
    elif os == 'Linux':
        ...
        raise TypeError()
    else:
        raise TypeError()


def parse_path(path: str):
    """ 解析传入路径的实际路径
    ## Parameter
    `path` - 文件的路径 or 快捷方式
    ## Notice
    此快捷方式只能是绝对路径的形式，否则无法获取真正路径"""
    if path.endswith('.lnk'):
        return parse_shortcut(path)
    else:
        return path
