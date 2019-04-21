import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(-1, 1, 50)
y = 2*x + 1
z = 2*x + 5

plt.figure()
plt.plot(x, y)
plt.plot(x, z)
plt.show()




