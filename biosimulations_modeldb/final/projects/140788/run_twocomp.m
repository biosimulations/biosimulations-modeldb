function run_twocomp
% Basic two compartment SCI motoneuron model with synaptic inputs
% Based on Booth Rinzel model parameters 
% Appropriate ICs has been put in
% Soma is coupled with the dendrite using a coupling conductance
% Synaptic inputs have been added to the dendrites
% A ramp current in soma is used to activate the cell 
% This program calls the ODE solver to solve the system

% First define all of the constant parameters

% Input membrane parameters from file

% Soma pulse current         
%scales=20;
%tons=1000;
%toffs=3000;

% Soma ramp current
offset=0;
scale=0.01;
ton=0;
toff=10000;
tswitch=2500;

% Synaptic pulse current parameters
scaled=0;
tond=1340;
toffd=2500;

gc=0.1;
p=0.1;
c=1;

gna=120;
ena=55;
thetamna=-35;           
kmna=-7.8;
thetahna=-55;
khna=7;

gkdr=100;
ek=-80;
thetan=-28;
kn=-15;

gscan=14;
eca=80;
thetamsca=-30;
kmscan=-5;
taumscan=16;            % Different from BR model
thetahsca=-45;
khscan=5;
tauhscan=160;           % Different from BR model

gskca=3.136;
gdkca=.69;

gl=0.51;
el=-60;                
f=0.01;
alpha1=0.009;
alpha2=0.009;
kca=2;

gcap=0.33;              % Parameters for fig.2e and 2f
thetamcap=-40;
kmcap=-7;
taumcap=40;

gnap=0.2;               % Parameters for fig.2e and 2f
thetamnap=-25;
kmnap=-4;
taumnap=40;

% No Synaptic Inputs
gsynbar=0; 
esyn=0;
tausyn=0.2;
period=20;

% Excitatory Synaptic parameters
%gsynbar=.1;  
%esyn=0;
%tausyn=0.2;
%period=20;

% Inhibitory Synaptic parameters
%gsynbar=.05;   
%esyn=-81;
%tausyn=0.65;
%period=20;

% Set up vector of variables
soma_var=6;             % First 6 entries are for soma variables
dend_var=4;             % # of variables in dendrite compartment
sy=soma_var + dend_var; % # of equations
y0 = zeros(sy,1);       % Allocate vector for solver

% Define the initial conditions
% No input steady state
y0(1)=-55.1076;         % vs
y0(2)=0.5038;	          % hna
y0(3)=0.1410;	          % n
y0(4)=0.0066;           % mscan
y0(5)=0.8830;           % hscan
y0(6)=0.0003;           % cas

y0(7)=-53.2093;         % vd
y0(8)=0.0260;           % cad
y0(9)=0.1316;           % mcap
y0(10)=0.0009;          % mnap

% Solve the system 
tic;
[t,y]=ode15s(@compmini,[0,10000],y0);
time=toc

z=length(t);
Isapp=zeros(z,1);
ICaP=zeros(z,1);
for i=1:z
    %Isapp(i)=scales*heav(t(i)-tons)*heav(toffs-t(i)); %for pulse
    Isapp(i)=offset+scale*(t(i)-ton)*(heav(t(i)-ton)*heav(toff-t(i)))+...
      2*scale*(tswitch-t(i))*(heav(t(i)-tswitch)*heav(toff-t(i))); % for ramp
    %ICaP(i)=gcap*y(i,9)*(y(i,7)-eca);
end

save temp1 t y Isapp ICaP;
% Plot membrane potentials 
y1=y(:,1);
ramp(t,y(:,1),Isapp); %ramp.m MATLAB code makes the plots in figure 2 format


%----------------------------------------------------------------
% Beginning of nested functions
%----------------------------------------------------------------

function h=heav(t)
    
% Define the heaviside function, since the command `heaviside(t)' 
% in matlab gives NaN when t = 0.

        h=zeros(size(t));
        h(t>0)=1;
end                      % end of heav function compmini

%----------------------------------------------------------------
function yp=compmini(t,y)

% Two compartment SCI motoneuron model
% Function defines rhs of system for solving
% Grab variables for soma and vectors for dendrite from previous 
% timestep
 
vs=y(1);
hna=y(2);
n=y(3);
mscan=y(4);
hscan=y(5);
cas=y(6);

vd=y(7);
cad=y(8);
mcap=y(9);
mnap=y(10);

% Initialize output vector y prime
sy = length(y);
yp = zeros(sy,1);

% rhs for Soma Compartment

% Membrane potential equation
mna=1/(1+exp((vs-thetamna)/kmna));
INa=gna*mna^3*hna*(vs-ena);
IKdr=gkdr*n^4*(vs-ek);
IsCaN=gscan*mscan^2*hscan*(vs-eca);
IsKCa=gskca*(cas/(cas+0.2))*(vs-ek);
Isleak=gl*(vs-el);
% Pulse Input
%Isapp=scales*heav(t-tons)*heav(toffs-t);
%Idapp=scaled*heav(t-tond)*heav(toffd-t);
% Ramp Input
Isapp=offset+scale*(t-ton)*(heav(t-ton)*heav(toff-t))+...
      2*scale*(tswitch-t)*(heav(t-tswitch)*heav(toff-t));

% equation for soma membrane potential
yp(1)=(-INa-IKdr-IsCaN-IsKCa-Isleak+Isapp+gc*((vd-vs)/p))/c;
		  
% equation for hna
hnainf=1/(1+exp((vs-thetahna)/khna));
tauhna=120/(exp((vs+50)/15)+exp(-(vs+50)/16));
yp(2)=(hnainf-hna)/tauhna;

% equation for n
ninf=1/(1+exp((vs-thetan)/kn));
taun=28/(exp((vs+40)/40)+exp(-(vs+40)/50));
yp(3)=(ninf-n)/taun;

% equation for mscan
mscaninf=1/(1+exp((vs-thetamsca)/kmscan));
yp(4)=(mscaninf-mscan)/taumscan;

% equation for hscan
hscaninf=1/(1+exp((vs-thetahsca)/khscan));
yp(5)=(hscaninf-hscan)/tauhscan;

% equation for cas
yp(6)=f*(-alpha1*IsCaN-kca*cas);

% Now dendrite Compartments
IdKCa=gdkca*(cad/(cad+0.2))*(vd-ek);
Idleak=gl*(vd-el);
ICaP=gcap*mcap*(vd-eca);
INaP=gnap*mnap*(vd-ena);

tloc=mod(t,period)*heav(t-tond)*heav(toffd-t);
gsyn=gsynbar*(tloc/tausyn)*(exp(1-(tloc/tausyn)));
Isyn=gsyn*(vd-esyn);


% Equation for vd
%yp(7)=(-IdKCa-ICaP-INaP-Idleak+gc*((vs-vd)/(1-p)))/c;

% Equation for vd with synapse
yp(7)=(-IdKCa-ICaP-INaP-Idleak-Isyn+gc*((vs-vd)/(1-p)))/c;


% Equation for cad
yp(8)=f*(-alpha2*ICaP-kca*cad);

% Equation for mcap
mcapinf=1/(1+exp((vd-thetamcap)/kmcap));
yp(9)=(mcapinf-mcap)/taumcap;

% Equation for mnap
mnapinf=1/(1+exp((vd-thetamnap)/kmnap));
yp(10)=(mnapinf-mnap)/taumnap;

end                      % end of function compmini

%----------------------------------------------------------------
% End of nested functions 
%----------------------------------------------------------------

end                      % end of function run_twocomp