# Model of the Mammalian ET cell

Computational model and files to recreate the results from the paper "A Computational Model of the Mammalian External Tufted Cell" https://doi.org/10.1016/j.jtbi.2018.10.003 

Author: Ryan Viertel

## Usage:

data = ET(input,sampling_rate);

input: input vector, if no input then just a vector of zeros

sampling_rate: rate at which the input vector should be sampled. 1000 for milisecond

returns the following struct:

data.T - time vector
data.X - ODE variables at each time step
* data.X(:,1) - Membrane Potential
* data.X(:,2) - nK
* data.X(:,3) - hNaP
* data.X(:,4) - hH
* data.X(:,5) - mLVA
* data.X(:,6) - hLVA
* data.X(:,7) - mBK
* data.X(:,8) - Calcium
* data.X(:,9) - nHVK

data.events - list of spike events

data.which - event type
* 1 - spike
* 2 - burst start
* 3 - burst end

data.current - system currents
* data.current(:,1) = transient sodium
* data.current(:,2) = fast potassium
* data.current(:,3) = leak
* data.current(:,4) = persistent sodium
* data.current(:,5) = hyperpolarization activated
* data.current(:,6) = LVA calcium
* data.current(:,7) = HVA calcium
* data.current(:,8) = large conductance potassium
* data.current(:,9) = HVK current

## example

### create the input vector
input = zeros(1,5000);
### run the model
data = ET(input,1000);
### plot the voltage trace
plot(data.T,data.X(:,1))

## ME-PCM
The code used to sample the model throughout parameter space to determine stability and investigate the effect of model parameters on model output is found in the ME-PCM directory

## xpp
The ODE file to recreate the bifurcation diagram is found in the xpp directory 
