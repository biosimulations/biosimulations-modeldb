Reproduces figures 5 - 8 from

Dovzhenok, A., C. Park, R.M. Worth, L.L. Rubchinsky. 
Failure of delayed feedback deep brain stimulation for intermittent
pathological synchronization in Parkinson's disease.
PLoS One 8(3):e58264, 2013.

Implemented by Andrey Dovzhenok, to whom questions should be
addressed.

Usage:

1. Unzip Dovzhenoketal2013.zip into an empty directory.

2. Open the folder in Matlab.

3a. Run PCAgenerator1el.m to compute principal components for the
arrangement with a single electrode. The ode file with a single
electrode arrangement is used.
3b Run PCAgenerator.m to compute principal components for the
arrangements with two or three electrodes. Included ode-files
correspond to the various electrode arrangements considered in the
paper.  Specify the name of the ode-file corresponding to the desired
electrode arrangements on line 9 in odeFileName variable.

4a. Run Sign_subset_1el.m with the outcome of the step 3a to generate
figures 6A and 6B.
4b. Run Sign_subset.m with the outcome of the step 3b to generate
figure 5 and the rest of figure 6.

5a. Run Max_plane_1el.m with the outcomes of the step 3a to generate
figures 8A and 8B.
5b. Run Max_plane.m with the outcomes of the step 3b to generate
figure 7 and the rest of figure 8.
