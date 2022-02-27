function data = ET(ORNtrace, ORNsamplingrate)

    %% set up params
	PARS = parameters;
  % PARS.gNaP = gPerSodium;

    ics = [-51.408534874838772   0.055706295559466   0.139259083672574   0.157733123889777   0.048620921041047   0.216830183163897 0.118223401083348   0.000398391792190   0.049382804823416]; % just after end of burst at equilibrium state

    odeopts = odeset('Events',@spikedetect,'MaxStep',2);

    data = integrator(@vfield_ET, odeopts, ics, PARS, ORNtrace, ORNsamplingrate);
end

function xdot = vfield_ET(t,x,p)
% Vector field for the minimal ET model.
%
%   INPUTS:
%   t -- current time
%   x -- (9,1) vector of current vector values
%   p -- struct containing parameter values in p.ET.param_name format
%
%   OUTPUT:
%   xdot -- derivative w.r.t. time

%% Phase variables

V = x(1);
nK = x(2);
hNaP = x(3);
hH = x(4);
mLVA = x(5);
hLVA = x(6);
mBK = x(7);
Ca = x(8);
nHVK = x(9);

% auxiliary quantities for the BK current
theta_mBK = -20 + 59.2*exp(-90*Ca) + 96.7*exp(-470*Ca);
p_mBK = 2.9 + 6.3*exp(-360*Ca);
s = -25.3 + 107.5*exp(-120*Ca);
f = 1/(10*(exp(-(V + 100 - s)/63.6)+exp((-150+(V + 100 - s))/63.6))) - 5.2;



% infinity curves
mNa_inf = 1./(1+exp((V - p.theta_mNa)./p.beta_mNa));
nK_inf = 1./(1+exp((V - p.theta_nK)./p.beta_nK));
mNaP_inf = 1./(1+exp((V - p.theta_mNaP)./p.beta_mNaP));
hNaP_inf = 1./(1+exp((V - p.theta_hNaP)./p.beta_hNaP));
hH_inf = 1./(1+exp((V - p.theta_hH)./p.beta_hH));
mLVA_inf = 1/(1+exp((V - p.theta_mLVA)/p.beta_mLVA));
hLVA_inf = 1/(1+exp((V - p.theta_hLVA)/p.beta_hLVA));
mHVA_inf = 1/(1+exp((V - p.theta_mHVA)/p.beta_mHVA));
mBK_inf = 1/(1+exp((V - theta_mBK)/p.beta_mBK));
mHVK_inf = 1./(1+exp((V - p.theta_mHVK)/p.beta_mHVK));
nHVK_inf = 1./(1+exp((V - p.theta_nHVK)/p.beta_nHVK));

% time constants
nHVK_tau = 1000./(1.0+exp(-(V+35))) + 1000;
nK_tau = p.tau_nK./cosh((V-p.theta_nK)/(2.0*p.beta_nK));
hNaP_tau = p.tau_hNaP./cosh((V-p.theta_hNaP)/(2.0*p.beta_hNaP));
hH_tau = p.tau_hH_T*exp(p.delta_hH_T*(V-p.theta_hH_T)/p.beta_hH_T)/(1+exp((V-p.theta_hH_T)/p.beta_hH_T));
mLVA_tau = p.tau_mLVA./cosh((V-p.theta_mLVA)/(2.0*p.beta_mLVA));
hLVA_tau = p.tau_hLVA./cosh((V-p.theta_hLVA)/(2.0*p.beta_hLVA));
mBK_tau = -(p_mBK - 1.0)*(f - 0.2)/0.8 + p.mBK_base;

% compute values for the currents
INa = p.gNa.*(1-nK)*mNa_inf.^3*(V - p.vNa);
IHVK = p.gHVK*mHVK_inf*nHVK*(V - p.vK);
IK = p.gK.*nK.^4.*(V - p.vK);
IL = p.gL.*(V - p.vL);
IH = p.gH.*hH.*(V - p.vH);
INaP = p.gNaP.*mNaP_inf*hNaP*(V - p.vNa);
ILVA = p.gLVA.*mLVA.^2.*hLVA.*(V - p.vCa);
IHVA = p.gHVA*mHVA_inf*(V - p.vCa);
IBK = p.gBK*mBK*(V - p.vK);

%% get ORN input for t
Input = p.intrace(floor(t / p.ORNsamplingfactor)+1);


xdot = zeros(size(x));
xdot(1) = -(INa + IK + ILVA + IH + INaP + IL + IHVA + IBK + IHVK - Input)./p.C;
xdot(2) = (nK_inf-nK)/nK_tau;
xdot(3) = (hNaP_inf-hNaP)/hNaP_tau;
xdot(4) = (hH_inf-hH)./hH_tau;
xdot(5) = (mLVA_inf-mLVA)/mLVA_tau;
xdot(6) = (hLVA_inf-hLVA)/hLVA_tau;
xdot(7) = (mBK_inf - mBK)/mBK_tau;
xdot(8) = -p.Ca_buffer*10*(ILVA + IHVA)/(p.Ca_z*p.F*p.d) + (p.Ca0 - Ca)/p.tau_Ca;
xdot(9) = (nHVK_inf - nHVK)./nHVK_tau;
end

function data = integrator(odefun, odeopts, ics, PARS, ORNtrace, ORNsamplingrate)

    ics = ics(:);

    PARS.intrace = ORNtrace;
    PARS.ORNsamplingfactor = 1000 / ORNsamplingrate;

    %% Integration tolerances
    atol = 1e-6;
    rtol = 1e-6;
    options = odeset('reltol',rtol,'abstol',atol,'InitialStep',0.5);
    options = odeset(options, odeopts); %override odeopts

    %% time span
    tstart = 0;
    tend = (length(ORNtrace) - 1) * PARS.ORNsamplingfactor;

    %% integrate
    tout = tstart;
    xout = ics';
    teout = [];
    ieout = [];

    tic
    while tstart < tend
        [t,x,te,xe,ie] = ode15s(odefun,[tstart tend],ics,options,PARS);

        nt = length(t);
        tout = [tout; t(2:nt)];
        xout = [xout; x(2:nt,:)];
        tstart = t(nt);

        if ~isempty(te)
            teout = [teout; te];
            ieout = [ieout; ie];

            ics = xe(end,:);

            options = odeset(options,'InitialStep',t(nt)-t(nt-1)); %use most recent timestep
        end
    end

    %%%%%%%%%%%%%calculate currents%%%%%%
    % 1 = transient sodium
    % 2 = fast potassium
    % 3 = leak
    % 4 = persistent sodium
    % 5 = hyperpolarization activated
    % 6 = LVA calcium
    % 7 = HVA calcium
    % 8 = large conductance potassium
    % 9 = HVK current
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    current(:,1) = PARS.gNa.*(1-xout(:,2)).*(1./(1+exp((xout(:,1)-PARS.theta_mNa)./PARS.beta_mNa))).^3.*(xout(:,1)-PARS.vNa);
    current(:,2) = PARS.gK.*xout(:,2).^4.*(xout(:,1)-PARS.vK);
    current(:,3) = PARS.gL.*(xout(:,1)-PARS.vL);
    current(:,4) = PARS.gNaP.*(1./(1+exp((xout(:,1)-PARS.theta_mNaP)./PARS.beta_mNaP))).*xout(:,3).*(xout(:,1)-PARS.vNa);
    current(:,5) = PARS.gH.*xout(:,4).*(xout(:,1)-PARS.vH);
    current(:,6) = PARS.gLVA.*xout(:,5).^2.*xout(:,6).*(xout(:,1)-PARS.vCa);
    current(:,7) = PARS.gHVA.*1./(1+exp(-(xout(:,1) + 20)./9)).*(xout(:,1)-PARS.vCa);
    current(:,8) = PARS.gBK.*xout(:,7).*(xout(:,1)-PARS.vK);

    mHVK_inf = 1./(1+exp((xout(:,1) - PARS.theta_mHVK)/PARS.beta_mHVK));
    current(:,9) = PARS.gHVK.*mHVK_inf.*xout(:,9).*(xout(:,1)-PARS.vK);

    data = struct('T', tout, 'X', xout, 'events', teout, 'which', ieout, 'current', current);
    toc

end

function [value,isterminal,direction] = spikedetect(~,y,~)
    value(1) = y(1); % spikes
    value(2) = y(2) - 0.25; % burst start
    value(3) = y(2) - 0.25; % burst end
    isterminal(1) = 0;
    isterminal(2) = 0;
    isterminal(3) = 0;
    direction(1) = 1;
    direction(2) = 1;
    direction(3) = -1;
end
