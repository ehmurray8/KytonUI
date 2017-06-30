import visa
import controller_340_wrapper

iRM = visa.ResourceManager()
instr = iRM.list_resources()
print(instr)
iTC = iRM.open_resource('GPIB0::12::INSTR', read_termination='\n')
#iTC.get_temp_c()
#print(controller_340_wrapper.get_temp_c(iTC))
print(iTC.query("CRDG?\n"))

# iGP = iRM.open_resource('GPIB0::3::INSTR', read_termination='\n')

__all__ = ['contoller_340_wrapper.py']

"""print("TCclass is "+iTC)
print(iTC.query("KRDG?\n"))
print(iTC.query("CRDG?\n"))
print(iTC.query("PID?\n"))
print(iTC.query("PID 1,5,5,1\n"))
"""

"""from prettytable import PrettyTable
t = PrettyTable(['Name', 'Age'])
t.add_row(['Alice', 24])
t.add_row(['Bob', 19])
print t
"""
