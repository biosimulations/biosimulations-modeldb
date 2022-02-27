function [rko] = transeq2(delt)
% ==============================================

global x1 y gsyn ta tb c1 c2 c3 tk r1 r2 r3 ga tmed 
global z2 tlo

do=(1.0-exp(-x1/ta))/(1.0-exp(-x1/ta)*exp(-y/tb));
%do=0.7;
gpeak=gsyn*do;
gs=gpeak*exp(-z2/tk);
gatf=ga*(1.0-exp(-z2/tlo));
rko=r1*gatf*exp(-delt/tmed)+r2*gs*exp(-delt/tk)-r3;

