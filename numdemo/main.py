import matplotlib.pyplot as plt
import numpy as np


class Dog:

    def __init__(self, name):
        self.name = name

    def bark(self):
        for n in range(5):
            print(self.name, " wang wang!")

    def setName(self, name):
        self.name = name



tony = Dog("tony")
tony.bark();
