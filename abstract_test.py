class Main:
    def __init__(self):
        self.x = 5

    def test_method(self):
        print("Test_method: {}".format(self.x))
        self.sub_method()

class Sub(Main):
    def __init__(self):
        super().__init__()
        self.x += 1

    def sub_method(self):
        print("Sub_method: {}".format(self.x))

sub = Sub()
sub.test_method()
