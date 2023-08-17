""" 修饰器集合 """


def asEnumClass(*, repeatable=False, lowercase=False):
    """ 使成为枚举类 
    ## Parameter
    `no_same` - 不允许存在重复值\n
    `no_lowercase` - 不允许常量名小写
    ## Return
    类的实体对象
    ## Example
    >>> asEnumClass()
    >>> class Color: pass"""

    # """ 内层修饰器 """
    def asEnum_deco(cls):

        # """ 重置__setattr__方法 """
        def new_setattr(self, name, value): assert False, '禁止修改枚举类型的属性值'
        cls.__setattr__ = new_setattr

        # """ 检重复值和小写字母 """
        vset = set()
        # 遍历属性字典
        for key, value in vars(cls).items():
            # 跳过内置属性
            if key.startswith('__') and key.endswith('__'):
                continue
            # 检测本次循环的值
            assert key.isupper() or lowercase, f'检测到小写字母 ->"{key}"'
            assert value not in vset or repeatable, f'检测到重复枚举 ->"{key}"'
            # 添加本次循环不重复的值
            vset.add(value)
        # 返回实例对象
        return cls()
    # 返回参数固化后的修饰器
    return asEnum_deco


if __name__ == '__main__':

    @asEnumClass()
    class Color:
        RED = 0
        A = 1
