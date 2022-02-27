**************************************************************************************************
**************************************************************************************************
**************************************************************************************************

The code can be used to reproduce time series and bifurcation diagrams shown in Figs. 4 and 5.

Time series (obtained from time_series.ode):
a.) time series for ‘par vle=720’:
    - parameter specification from line 33
b.) time series for ‘par vle=3700’:
    - parameter specification from line 34

Bifurcation diagrams (obtained from continuatons.ode)
c.) bifurcation diagram for ‘par vle=720’:
    - initial conditions from line 64-68 (instead of line 72-76)
    - parameter specification from line 87 (instead of line 88) 
    - change ‘PARMIN=-250’ to ‘PARMIN=-50’ in line 201
    - change ‘XAUTOMIN=-250’ to ‘XAUTOMIN=-50’ in line 202 
    - forward and backward continuation as described in the general instructions 1-8.) given below

d.) upper branch of bifurcation diagram for ‘par vle=3700’:
    - initial conditions from line 72-76
    - parameter specification from line 88
    - default values for  ‘PARMIN’ and ‘XAUTOMIN’ in lines 201-202 
    - forward and backward continuation as described in the general instructions 1-8.) given below

d.) lower branch of bifurcation diagram for ‘par vle=3700’:
    - initial conditions from line 64-68
    - parameter specification from line 88
    - default values for  ‘PARMIN’ and ‘XAUTOMIN’ in lines 201-202 
    - forward and backward continuation as described in the general instructions 1-8.) given below




The fixed point curves from Figs. 4 and 5 can be obtained as follows:

1.) open file with XPPAUT
2.) run simulation twice to make sure the system is in its fixed point:
     click "Initialconds" + "(G)o"; "Initialconds" + "(L)ast"
     (keyboard shortcuts: "I" + "G", "I" + “L")
3.) open AUTO interface:
     click "File" + "Auto"
     (keyboard shortcut: "F" + “A")
4.) run 'forward' fixed point continuation:
     click "Run" + "Steady state"
     (keyboard shortcut: "R" + “S")
5.) grab point to start 'backward' continuation if desired: 
     click “Grab”, then navigate along the curve with "tab” key, press
     "enter" to choose point
6.) set continuation step size to negative: 
     click "Numerics” and change 'Ds:0.002' to 'Ds:-0.002’, click "Ok"
7.) run backward coninuation by clicking "Run"
8.) save the fixed point curves and bifurcation information: 
     click "File" + "All info”, choose a filename and click "Ok"

**************************************************************************************************
**************************************************************************************************
**************************************************************************************************
