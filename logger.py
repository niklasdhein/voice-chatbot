class Logger():
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def log(self, message: str) -> None:
        print(f"{self.prefix}{message}")

class WarningLogger(Logger):
    def __init__(self) -> None:
        super().__init__("[ WARNING ] ")

class DebugLogger(Logger):
    def __init__(self) -> None:
        super().__init__("[ DEBUG ] ")