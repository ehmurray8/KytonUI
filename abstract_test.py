class Main:
    def __init__(self):
        self.x = 5

    def test_method():
        print(self.x)
        sub_method()

class Sub(Main):
    def __init__(self):
        #super().__init__()
        super()
        super().x += 1

    def sub_method():
        print(x)

sub = Sub()
sub.test_method()
