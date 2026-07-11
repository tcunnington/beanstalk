"""Known-bad fixture: inheritance the no-inheritance checker must flag.

Never imported — only parsed by the checker tests.
"""


class Animal:
    pass


class Mixin:
    pass


class Cow(Animal):  # ARCH101: Animal is not on the allow-list
    def moo(self) -> str:
        return "moo"


class MultiCow(Animal, Mixin):  # 2x ARCH101 + ARCH102 (multiple inheritance)
    pass
