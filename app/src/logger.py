class Logger():

    def __init__(self, file):
        self.file = file
        self.lines = ""

    def add_to_file(self, message):
        self.lines += message

        with open(self.file, "a", encoding="utf-8") as file:
            file.write(message)

    def write_new_file(self, message):
        self.lines = message

        with open(self.file, "w", encoding="utf-8") as file:
                    file.write(message)

    def get_lines(self):
        return self.lines