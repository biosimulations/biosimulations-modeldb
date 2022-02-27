This is the README for the code for the article

N. Hubel and M. A. Dahlem: "Dynamics from seconds to hours in
Hodgkin-Huxley model with time-dependent ion concentrations and buffer
reservoirs" PLoS Comp Biol (2014)

email: niklas.huebel@gmail.com
Oct. 7, 2014

This model requires XPP which is freely available from:
http://www.math.pitt.edu/~bard/xpp/xpp.html

Notes on the supplied two XPP simulation files:

spreading-depression.ode:

This code computes time series like in Fig. 5. SD is triggered either
by current stimulation (dynamics of variable "stim") or by pump
interruption (dynamics of pump coefficient "z"). Two regulation
schemes for potassium are implemented: glial buffering and diffusive
coupling to the vascular system (with a switch parameter "s", see
below). For diffusive coupling with elevated "k_bath" values the time
series of Fig. 7 can be simulated.

spreading-depression-bistable-cont.ode:

To compute the fixed point continuation of Fig. 2 run xppaut with this
file. To reach the exact fixed point use (I)nitial and (G)o
first. Then use (F)ile + (A)UTO to open the AUTO interface. (R)un +
(S)teady state will start the forward continuation. Then change the
(N)umerics parameter DS from 0.2 to -0.2, (G)rab (+ 'Enter') the
starting point of the forward continuation curve, and (R)un again.
(Remark: The Hopf line of Fig. 4 can only be obtained by changing this
code so that also "cli" is a parameter.)
