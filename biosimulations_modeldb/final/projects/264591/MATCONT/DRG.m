function out = DRG
%
%
out{1} = @init;
out{2} = @fun_eval;
out{3} = @jacobian;
out{4} = @jacobianp;
out{5} = [];%@hessians;
out{6} = [];%@hessiansp;
out{7} = [];
out{8} = [];
out{9} = [];
% 
% --------------------------------------------------------------------------

function dfdt = fun_eval(t,y,V12,Is,gNa17d,gNa18d,gKd,gKAd)
kv=150;
kt=30; %Length of an action potential approximately
g=gNa17d;

gNa17=gNa17d/g;
gNa18=gNa18d/g;
gK=gKd/g;
gKA=gKAd/g;

v=y(1);
m17=y(2);
h17=y(3);
s17=y(4);
m18=y(5);
h18=y(6);
n=y(7);
nKA=y(8);
hKA=y(9);

I=Is/(kv*g);


gl=0.0575/g;
vna=67.1/kv;
vk=-84.7/kv;
vl=-58.91/kv;
c=0.93;
A=21.68;
% A=1;

%Time scales

TmNa17=1;
ThNa17=1;
TsNa17=1;
TmNa18=1;
ThNa18=1;
Tn=1;
TnKA=1;
ThKA=1;

%Functions for Nav1.7

am17=15.5/(1+exp(-(v*kv-5)/12.08));
bm17=35.2/(1+exp((v*kv+72.7+V12)/16.7));
taum17=TmNa17*(1/(am17+bm17));
minf17=am17/(am17+bm17);

ah17=0.38685/(1+exp((v*kv+122.35)/15.29));
bh17=-0.00283+2.00283/(1+exp(-(v*kv+5.5266)/12.70195));
tauh17=ThNa17*(1/(ah17+bh17));
hinf17=ah17/(ah17+bh17);

as17=0.00003+0.00092/(1+exp((v*kv+93.9)/16.6));
bs17=132.05-132.05/(1+exp((v*kv-384.9)/28.5));
taus17=TsNa17*(1/(as17+bs17));
sinf17=as17/(as17+bs17);

%Functions for Nav1.8

am18=2.85-(2.839/(1+exp((v*kv-1.159)/13.95)));
bm18=7.6205/(1+exp((v*kv+46.463)/8.8289));
taum18=TmNa18*(1/(am18+bm18));
minf18=am18/(am18+bm18);

tauh18=ThNa18*(1.218+42.043*exp(-((v*kv+38.1)^2)/(2*15.19^2)));
hinf18=1/(1+exp((v*kv+32.2)/4));

%Functions for Kv

if -v~=14.273/kv 
    an = 0.001265*(v*kv+14.273)/(1-exp(-(v*kv+14.273)/10)); 
else
    an = 0.001265*10; 
end
bn=0.125*exp(-(v*kv+55)/2.5);
taun=Tn*(1/(an+bn)+1);
ninf=1/(1+exp(-(v*kv+14.62)/18.38));

%Functions for KA
ninfKA=(1/(1+exp(-(v*kv+5.4)/16.4)))^4;
taunKA=TnKA*(0.25+10.04*exp(-(v*kv+24.67)^2/(2*34.8^2)));
hinfKA=1/(1+exp((v*kv+49.9)/4.6));
tauhKA1=ThKA*(20+50*exp(-(v*kv+40)^2/(2*40^2)));
if tauhKA1<5*ThKA
    tauhKA=5*ThKA;
else
    tauhKA=tauhKA1;
end

dvdt=(kt*g/c)*((I/A)-gNa17*m17^3*h17*s17*(v-vna)-gNa18*m18*h18*(v-vna)-gK*n*(v-vk)-gKA*nKA*hKA*(v-vk)-gl*(v-vl));

dm17dt=kt*(minf17-m17)/taum17;
dh17dt=kt*(hinf17-h17)/tauh17;
ds17dt=kt*(sinf17-s17)/taus17;

dm18dt=kt*(minf18-m18)/taum18;
dh18dt=kt*(hinf18-h18)/tauh18;

dndt=kt*(ninf-n)/taun;

dnKAdt=kt*(ninfKA-nKA)/taunKA;
dhKAdt=kt*(hinfKA-hKA)/tauhKA;    

dfdt=[dvdt;dm17dt;dh17dt;ds17dt;dm18dt;dh18dt;dndt;dnKAdt;dhKAdt];
% --------------------------------------------------------------------------

function [tspan,y0,options] = init
tspan = [0; 1000];
%v=-65.4406,m17=0.0032,h17=0.3797,s17=0.9038,m18=0.0050,h18= 0.9997,n=0.0592,nKA=3.9452e-07,hKA= 0.9670
yo=[-65.4406/150;0.0032;0.3797;0.9038;0.0050;0.9997;0.0592;3.9452e-07;0.9670];


handles = feval(@DRG);

% --------------------------------------------------------------------------

function dfdxy = jacobian(t,y,V12,Is,gNa17,gNa18,gK,gKA)
v=y(1);
m17=y(2);
h17=y(3);
s17=y(4);
m18=y(5);
h18=y(6);
n=y(7);
nKA=y(8);
hKA=y(9);
kv=150;
I=Is;

dfdxy = J_D(v,m17,h17,s17,m18,h18,n,nKA,hKA,V12,I,gNa17,gNa18,gK,gKA, gNa17);
if -v==14.273/kv
    dfdxy(7,:)=JN_D(v,m17,h17,s17,m18,h18,n,nKA,hKA,V12,I,gNa17,gNa18,gK,gKA, gNa17);
end

tauhKA1=20+50*exp(-(v*kv+40)^2/(2*40^2));
if tauhKA1<5
    dfdxy(9,:)=JhKA_D(v,m17,h17,s17,m18,h18,n,nKA,hKA,V12,I,gNa17,gNa18,gK,gKA,gNa17);
end


% --------------------------------------------------------------------------

function dfdp = jacobianp(t,y,V12,Is,gNa17,gNa18,gK,gKA)
v=y(1);
m17=y(2);
h17=y(3);
s17=y(4);
m18=y(5);
h18=y(6);
n=y(7);
nKA=y(8);
hKA=y(9);
% kv=150;
I=Is;
dfdp = JP_D(v,m17,h17,s17,m18,h18,n,nKA,hKA,V12,I,gNa17,gNa18,gK,gKA,gNa17);
% --------------------------------------------------------------------------
