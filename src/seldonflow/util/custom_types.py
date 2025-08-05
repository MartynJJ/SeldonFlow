# types.py cannot be used as conflicts with built in types
from typing import NewType

TimeStamp = NewType("TimeStamp", float)
Seconds = NewType("Seconds", int)
TempC = NewType("TempC", float)
TempF = NewType("TempF", float)


class Temp:
    temp_c: TempC
    temp_f: TempF

    def __init__(self, temp_c: TempC) -> None:
        if isinstance(temp_c, float):
            self._celsius = temp_c
            self._fahrenheit = TempF(self._celsius * 9 / 5 + 32)
        else:
            raise TypeError("Unexpected type for temperature")

    def as_celsius(self) -> TempC:
        return self._celsius

    def as_fahrenheit(self) -> TempF:
        return self._fahrenheit

    @staticmethod
    def from_f(temp_f: TempF):
        return Temp(TempC((temp_f - 32) * 5 / 9))

    def __str__(self) -> str:
        return f"Temperature: {self._celsius}°C / {self._fahrenheit}°F"

    def __repr__(self) -> str:
        return f"Temperature: {self._celsius}°C / {self._fahrenheit}°F"

    def __eq__(self, other):
        if isinstance(other, Temp):
            return self._celsius == other._celsius
        return False

    def __lt__(self, other):
        if isinstance(other, Temp):
            return self._celsius < other._celsius
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Temp):
            return self._celsius <= other._celsius
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Temp):
            return self._celsius > other._celsius
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Temp):
            return self._celsius >= other._celsius
        return NotImplemented


def main():
    time_stamp = TimeStamp(100.1)
    seconds = Seconds(1)
    temp_c = TempC(100.0)
    temp_f = TempF(100.0)


if __name__ == "__main__":
    main()
