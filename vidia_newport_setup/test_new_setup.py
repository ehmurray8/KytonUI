import time
import visa
from threading import Thread
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
from sys import argv
import datetime
import os
from fbgui.devices.vidia_laser import VidiaLaser
from fbgui.devices.newport_power import NewportPower


# READ SETTINGS
REMOVE_POINTS = False
NUM_SCANS = int(argv[1])
START_WAVE = int(argv[2])
END_WAVE = int(argv[3])
POWER = int(argv[4])


wave = None
above_mean = False
waves = deque()
powers = deque()
all_waves = []
all_powers = []
pop = False
kill_thread = False


def animate(_):
    axes.clear()
    axes.set_ylabel("Power (dBm)")
    axes.set_xlabel("Wavelength (nm)")
    axes.scatter(waves, powers)


def collect():
    global above_mean
    count = 0
    while not kill_thread and (count < NUM_SCANS or NUM_SCANS == -1):
        try:
            wave = laser.get_wavelength()
            pow = power.get_power()
            if wave < START_WAVE or wave > END_WAVE or pow > POWER + .5:
                raise ValueError
            waves.append(wave)
            powers.append(pow)
            if wave > laser.get_mean_wavelength():
                above_mean = True
            if above_mean and wave < laser.get_mean_wavelength():
                count += 1
                above_mean = False
        except (ValueError, visa.VisaIOError) as r:
            pass
        time.sleep(.1)


if __name__ == "__main__":
    try:
        man = visa.ResourceManager()
        laser = VidiaLaser("GPIB1::8::INSTR", man, True)
        power = NewportPower("GPIB1::4::INSTR", man, True)
        laser.start_scan(num_scans=NUM_SCANS, start_wave=START_WAVE, end_wave=END_WAVE, power=POWER)
        mean_wave = (START_WAVE + END_WAVE) / 2.

        Thread(target=collect).start()

        try:
            if NUM_SCANS != 1:
                fig, axes = plt.subplots()
                fig.suptitle("Power vs. Wavelength")
                axes.set_ylabel("Power (dBm)")
                axes.set_xlabel("Wavelength (nm)")
                anim = FuncAnimation(fig, animate, interval=5)
                axes.scatter(powers, waves)
                plt.show()

            if NUM_SCANS == 1:
                plt.scatter(powers, waves)
                plt.ylabel("Power (dBm)")
                plt.xlabel("Wavelength (nm)")
                plt.title("Power vs. Wavelength")
                plt.show()
        except AttributeError:
            pass

        t = time.time()
        timestamp = datetime.datetime.fromtimestamp(t).strftime("%Y%m%dT%H%M%S")
        if not os.path.isdir(r"C:\Users\phils\Documents\FBGScans"):
            os.mkdir(r"C:\Users\phils\Documents\FBGScans")
        with open(os.path.join(r"C:\Users\phils\Documents\FBGScans",
                               "{}_scan_{}-{}.txt".format(str(timestamp), START_WAVE, END_WAVE)), "w") as f:
            for wave, power in zip(waves, powers):
                f.write("{}, {}\n".format(wave, power))

        kill_thread = True
        time.sleep(2)

        laser.stop_scan()
    except visa.VisaIOError:
        pass
