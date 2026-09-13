from enum import StrEnum


class LanguageRole(StrEnum):
    NATIVE = "NATIVE"
    FLUENT = "FLUENT"
    LEARNING = "LEARNING"


class CEFRLevel(StrEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"
