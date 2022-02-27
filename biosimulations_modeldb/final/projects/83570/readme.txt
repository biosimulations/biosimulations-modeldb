This is the readme.txt for a model associated with the publication:

Goldberg JA, Rokni U, Sompolinsky H (2004) Patterns of ongoing
activity and the functional architecture of the primary visual
cortex. Neuron 42:489-500

Notes from Josh Goldberg:

This model is at the heart of our 2004 Neuron paper. It is analyzed in
and about figure 3 in that paper. The initial code was run in Matlab
and the paper includes a variety of models that elaborate on this
model.... I do believe that this is the most elegant/central part of
the paper.

Usage notes:

To run the .tab file must be in the same directory as the .ode file.
... run the program as usual in the main XPP window, that is: I,G.
Then once you fill in the the entries in the Edit Arrayplot Window
(see the begining of NoisyRing.ode), you must press "redraw". then
each time you continue the integration in the main XPP window (e.g.,
E,I,L) do "redraw" again and see the continuation of the
simulation.

The model has three states, homogeneous for low gains (lambda<1) and
then Marginal for lambda that is between 1 and 2 (for mu>0). (the
integration diverges for lambda larger than 2). this is all explained
in the paper. Marginal means that you get a noisy hill of activity.  I
think it is important to point out that this model corresponds only to
figure 3 in that paper.

Default values lambda=1.8 and mu=1 give a nice hill of activity with
some of the neurons with rates that are very close to zero. (The
spatial pattern on the ring is a noisy clipped sinusoid).

Finally the line

aux phiang=atan(rfunds/rfundc)

gives the phase of the order parameter (between -pi and pi) and it 
corresponds to the position of the center of the hill of activity along 
the ring. It is well defined when there is a nice hill, as in the case 
of the above default values of lambda and mu.
