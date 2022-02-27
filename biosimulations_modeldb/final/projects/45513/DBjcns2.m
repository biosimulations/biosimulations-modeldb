function [tfo] = transeq1(tf)
% ==============================================

global x1 y gsyn ta tb c1 c2 c3 tk tw

do=(1.0-exp(-x1/ta))/(1.0-exp(-x1/ta)*exp(-y/tb));
%do=0.7;
gpeak=gsyn*do;
tfo=gpeak*c1*exp(-tf/tk)+c2*exp(-tf/tw)-c3;


