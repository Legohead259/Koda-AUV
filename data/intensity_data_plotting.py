import pandas as pd
import matplotlib.pyplot as plt

dir = "data/100622 - Pool Testing/"

for i in range(1, 14):
    file = "Intensities" + str(i) + ".csv"
    df = pd.read_csv(dir+file,names=["Range", "Acoustic Intensity"])
    print (df)

    x = df['Range']
    y = df['Acoustic Intensity']

    # plot
    plt.scatter(x,y)
    plt.title(file)
    plt.xlabel("Range from Sensor [m]")
    plt.ylabel("Acoustic Intensity [ADC Counts]")
    plt.axvline(x=0.75, color="red", linestyle="-.")
    # plt.show()
    plt.savefig(fname=dir+"plots/"+"intensity_" + str(i) + "_100622.png")
    plt.clf()