%% Integrate the equations to reach steady state solution
OPTIONS = [];
OPTIONS=odeset('RelTol',1e-8);
hls = DRG;
Is=0;
V12=0;
v0=-65.4406/150;
gNa18=7;
[t,y] = ode15s(hls{2},[0 10000],[v0 0.0032 0.3797 0.9038 0.0050 0.9997 0.0592 3.9452e-07 0.9670],OPTIONS,V12,Is, 18, gNa18, 4.78, 8.33);

%% Continuation of steady state solution
%function DRG starting with I as a bifurcation parameter.
opt=contset;
opt = contset(opt,'MaxCorrIters',20);
opt = contset(opt,'MaxTestIters',20);
opt = contset(opt,'FunTolerance',10e-7);
opt = contset(opt,'VarTolerance',10e-7);
opt = contset(opt,'TestTolerance',10e-6);
opt=contset(opt,'Singularities',1);
opt=contset(opt,'Eigenvalues',1);
opt = contset(opt,'MaxNumPoints',1000);
opt = contset(opt,'MaxStepsize',0.5);
V12=0;
kv=150;
IC = y(end,:)';
[x0,~]=init_EP_EP(@DRG,IC,[V12; 0; 18; gNa18; 4.78; 8.33],[2]);
[x,v,s,h,f]=cont(@equilibrium,x0,[],opt);

%% Continuation of periodic branch. 
% First, integrate till s17 starts oscillating periodically. Then,
% integrate for approx 1-1.5 times the period.
% Depending on Is, the period in line 43 should change.

Is=118;
[~,y] = ode15s(hls{2},[0 10000],[v0 0.0032 0.3797 0.76315 0.0050 0.9997 0.0592 3.9452e-07 0.9670],OPTIONS,V12,Is, 18, gNa18, 4.78, 8.33);

x1 = y(end,:);
[t,y] = ode15s(hls{2},[0 1.6],x1,OPTIONS,V12,Is, 18, gNa18, 4.78, 8.33);

p=[V12;Is; 18; gNa18; 4.78; 8.33];
ap=[2];
%% Continuation of periodic branch
tolerance=1e-4;
[x0,v0]=initOrbLC(@DRG,t,y,p,ap,300,4,tolerance);

opt=contset;
opt = contset(opt,'MaxNumPoints',40);
opt = contset(opt,'Multipliers',1);
opt = contset(opt,'Adapt',1);
opt=contset(opt,'Backward',0);
opt = contset(opt,'MaxStepsize',5);
opt = contset(opt,'MaxCorrIters',20);
opt = contset(opt,'MaxTestIters',20);
opt=contset(opt,'Singularities',1);
opt = contset(opt,'FunTolerance',10e-7);
opt = contset(opt,'VarTolerance',10e-7);
opt = contset(opt,'TestTolerance',10e-7);
[xlc,vlc,slc,hlc,flc]=cont(@limitcycle,x0,v0,opt);

