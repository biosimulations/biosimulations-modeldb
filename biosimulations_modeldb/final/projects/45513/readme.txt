This is the readme.txt for the models associated with the paper

Bose A, Manor Y, Nadim F. The activity phase of postsynaptic neurons in a 
simplified rhythmic network. J Comput Neurosci. 2004

Abstract:

Many inhibitory rhythmic networks produce activity in a range of frequencies.
The relative phase of activity between neurons in these networks is often a 
determinant of the network output. This relative phase is determined by the 
interaction between synaptic inputs to the neurons and their intrinsic 
properties. We show, in a simplified network consisting of an oscillator 
inhibiting a follower neuron, how the interaction between synaptic depression
and a transient potassium current in the follower neuron determines the 
activity phase of this neuron. We derive a mathematical expression to 
determine at what phase of the oscillation the follower neuron becomes 
active. This expression can be used to understand which parameters determine
the phase of activity of the follower as the frequency of the oscillator is 
changed. We show that in the presence of synaptic depression, there can be 
three distinct frequency intervals, in which the phase of the follower neuron
is determined by different sets of parameters. Alternatively, when the 
synapse is not depressing, only one set of parameters determines the phase of
activity at all frequencies.

---

This model is a a Morris-Lecar system with IA and depression.
The interesting phase plane for the "middle" branch is the v vs. ha. 
Note also that the v vs w phase plane can have a quintic v nullcline.

To run the models:
Matlab: after you add the path of the activityphase directory start the 
DBjcns1.m file.  It will compute and display fig 9D.

XPP: start with the command
xpp DBdep+A.ode

Click File, Read Set and then DBdep+A.ode.set
Type i g for Initial Conditions Go. 
You should see the voltage trace shown in Figure 10 corresponding to the 
unscaled version of Period = 800 (lower left).  You can change the period
by changing the parameter per.

Bard Ermentrout's website http://www.pitt.edu/~phase/
describes how to get and use xpp (Bard wrote xpp).
