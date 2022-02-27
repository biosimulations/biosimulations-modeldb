function pars = parameters

%% Reversal potentials (mV)
pars.vL = -62.5;
pars.vH = -35;
pars.vNa = 45;
pars.vK = -105;
pars.vCa = 120;

%% Conductances (mS/cm^2)
% gL = 2.5;
% gH = 20;
% gNaP = 8.3244;
% gLVA = 15.0213;
% gNa = 29.17;
% gK = 12.96;
% gHVA = 2;
% gBK = 5;
% gHVK = 10;

pars.gL = 2.5;
pars.gH = 20;
pars.gNaP = 8.3244; % 5.6 - 120 changes burst frequency
pars.gLVA = 15.0213;
pars.gNa = 29.17;
pars.gK = 12.96;
pars.gHVA = 2;
pars.gBK = 5;
pars.gHVK = 10;

%% Na
pars.theta_mNa = -25;
pars.beta_mNa = -6.5;

%% K
pars.theta_nK = -26;
pars.beta_nK = -9;
pars.tau_nK = 10;

%% LVA
pars.theta_mLVA = -37.1;
pars.beta_mLVA = -4.8916;
pars.tau_mLVA = 40;
pars.theta_hLVA = -59.2;
pars.beta_hLVA = 11.2326;
pars.tau_hLVA = 350;

% HVA
pars.theta_mHVA = -10.0;
pars.beta_mHVA = -6.5;

%% NaP
pars.theta_mNaP = -40;
pars.beta_mNaP = -4;
pars.theta_hNaP = -54;
pars.beta_hNaP = 5;
pars.tau_hNaP = 500;

%% H
pars.theta_hH = -61.32;
pars.beta_hH = 5.855;
pars.tau_hH_T = 100;
pars.delta_hH_T = 0.205;
pars.theta_hH_T = -65.95;
pars.beta_hH_T = 4.44;

% HVK 
pars.theta_mHVK = -40.0;
pars.beta_mHVK = -2.0;
pars.theta_nHVK = -30.0;
pars.beta_nHVK = -2.0;

%% BK
pars.mBK_base = 170; %base time constant (ms)
pars.beta_mBK = -15.6;

%% other parameters
pars.Ca0 = 0.00002; %concentration of calcium (mM)
pars.tau_Ca = 8; %calcium concentration time constant (ms)
pars.Ca_buffer = 0.5; %accounts for quick calcium buffering
pars.Ca_z = 2; %unitless number
pars.d = 1; %depth where calcuim concentration is relevent (microns)
pars.C = 21; % capacitance (microF/cm^2)
pars.F = 96485; %Faraday's constant (C/mol)

end
