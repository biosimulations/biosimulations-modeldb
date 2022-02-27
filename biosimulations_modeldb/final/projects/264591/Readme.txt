Verma P, Kienle A, Flockerzi D, Ramkrishna D. Using Bifurcation Theory for Exploring Pain. Industrial & Engineering Chemistry Research. 2019.

Verma P, Kienle A, Flockerzi D, Ramkrishna D. Computational analysis of a 9D model for a small DRG neuron. arXiv preprint arXiv:2001.04915. 2020 Jan 14.

Verma P, Eaton M, Kienle A, Flockerzi D, Yang Y, Ramkrishna D. A mathematical investigation of chemotherapy-induced peripheral neuropathy. bioRxiv. 2020 Jan 1.

Both XPP (DRG.ode) and MATCONT (*.m) files are provided in the respective folders.

In MATCONT, analytical Jacobian was used. You can run DRG_Jacobian.m to generate the Jacobian matrix functions (J_D.m, JhKA_D.m, JN_D.m, JP_D.m). DRG.m contains the equations. DRG_Steady_Periodic_I.m can be used to perform continuation of equilibrium and periodic solutions for the set of equations. Note that an extra parameter V12 is introduced in the MATCONT equations. This is kept as zero, but can be varied as was done for the first aforementioned paper.

The MATCONT equations are scaled, while XPP equations are not.

20200521 An update from Parul Verma supplied another XPP file and the
bioRxiv citation was added to this Readme
