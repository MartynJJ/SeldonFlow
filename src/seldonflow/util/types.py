from typing import NewType, Union

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
    def from_f(temp_f: TempC):
        return Temp(TempC((temp_f - 32) * 5 / 9))

    def __str__(self) -> str:
        return f"Temperature: {self._celsius}°C / {self._fahrenheit}°F"
