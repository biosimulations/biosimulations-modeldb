This is the XPP code associated with the paper:

J.E. Rubin and J.C. Smith, "Robustness of respiratory rhythm
generation across dynamic regimes", PLoS Computational Biology, 2019

This code was contributed by J.E. Rubin.

basenet.ode, basenet.ode.set:

These files were used for simulations without PiCo and without block
of inhibition.  They include several auxiliary variables that can be
used to plot the inhibition level to each neuron in the network and
the output level from each neuron in the network.

basenetpico3.ode, basenetpico3.ode.set3:

These files are similar but have been augmented to include the PiCo,
including an additional auxiliary variable represented PiCo output.

basenetTA.ode, basenetTA.ode.set:

These files allow for easy block of the inhibition to units in the
preBotC or to units in the BotC.  They are set-up to run from the
command line in silent mode, which I do with the command:

xpp basenetTA.ode -silent -setfile basenetTA.ode.set

Note that in the ode file:

— The line “only t,fv1,v1” means that only these three variables will
be saved.

— The line “@ output=b31range_ton.test” specifies that these variables
will be saved into the file b31range_ton.test. This can be edited to
save data under a different file name.  Values of each variable are
saved in a corresponding column in the file.

— The additional numerical instructions set up integration over a
range of values of a parameter; the default parameter is b31.  This
range information also shows up in the set file.  To change it for a
particular run, I change the information in the set file, where it is
stored under “#Range information”.
