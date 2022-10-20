import pandas as pd
import matplotlib.pyplot as plt

dir = "data/100622 - Pool Testing/"

df1 = pd.read_csv(dir+"Intensities1.csv",names=["Range", "Acoustic Intensity"])
df7 = pd.read_csv(dir+"Intensities7.csv",names=["Range", "Acoustic Intensity"])

x1 = df1['Range']
y1 = df1['Acoustic Intensity']
x7 = df7['Range']
y7 = df7['Acoustic Intensity']

print("Distance to wall:" + str(x1[y1[100:].argmax()+100]))
print("Distance to barrel: " + str(x7[y7[150:].argmax()+150]))

# plot
plt.scatter(x1,y1)
plt.scatter(x7,y7)
plt.title("Comparison of SONAR Readings")
plt.xlabel("Range from Sensor [m]")
plt.ylabel("Acoustic Intensity [ADC Counts]")
plt.axvline(x=0.75, color="red", linestyle="-.")
plt.legend(["Deadzone cutoff", "SONAR facing wall", "SONAR facing barrel"])
# plt.show()