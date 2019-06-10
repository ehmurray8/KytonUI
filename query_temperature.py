import visa
import time

LOCATION = "GPIB0::12::INSTR"

if __name__ == "__main__":
    man = visa.ResourceManager()
    dev = man.open_resource(LOCATION, read_termination='\r\n', open_timeout=2500)

    while True:
        reading = float(dev.query("KRDG? B"))
        print("{}K - {}C".format(round(reading, 2), round(reading - 273.15, 2)))
        time.sleep(1)
