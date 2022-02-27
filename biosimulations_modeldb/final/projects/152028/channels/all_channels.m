% Requires CG's param-fitter Matlab package
addpath ../param_fitter

% ****************************************
% Na CHANNEL - O'Dowd and Aldrich (1988)
% ****************************************

% NaT (DmNav10) - updated 2012/06/04 after modeling it in Neuron
f_DmNav10_ODowd_minf_v = ...
    param_act([-29.13 -8.92], 'm_{Na,\infty}');
f_DmNav10_ODowd_mtau_v = ...
    param_tau_v([0.1270 3.434 45.35 5.98], '\tau_{Na,m}');

m_DmNav10_ODowd = param_act_int_v(f_DmNav10_ODowd_minf_v, f_DmNav10_ODowd_mtau_v, 'm');

f_DmNav10_ODowd_hinf_v = ...
    param_act([-47 5], 'h_{Na,\infty}');
f_DmNav10_ODowd_htau_v = ...
    param_tau_exp_v([0.36 1 20.65 -10.47], '\tau_{Na,h}');

h_DmNav10_ODowd = param_act_int_v(f_DmNav10_ODowd_hinf_v, f_DmNav10_ODowd_htau_v, 'h');

I_DmNav10_ODowd_v = param_HH_chan_int_v([3 368 70 1], m_DmNav10_ODowd, ...
                                        h_DmNav10_ODowd, 'I_DmNav10', ...
                                        struct('name', 'Na'));

% NaP (DmNav10 WHL oocyte #1)

f_DmNav10_P_WHLoocyte1_minf_v = ...
    param_act([-48.77 -3.68], 'm_\infty');
% this is unknown, so it is same as above
f_DmNav10_P_WHLoocyte1_mtau_v = ...
    param_func_const('time const [ms]', 1, 'DmNav10_P_oocyte1_taum');

m_DmNav10_P_WHLoocyte1 = param_act_int_v(f_DmNav10_P_WHLoocyte1_minf_v, f_DmNav10_P_WHLoocyte1_mtau_v, 'm');

I_DmNav10_P_WHLoocyte1_v = ...
    param_I_v([1 0 5 45], m_DmNav10_P_WHLoocyte1, param_func_nil, 'I_DmNav10_P_WHLoocyte1');



% ****************************************
% K CHANNELS
% ****************************************

load('Kfs.mat');

% => should create I_Kf_v3 and I_Ks_v3, objects of param_I_2tauh_int_v
% and param_I_int_v

% **************************************************
% Export Na/K chans to Neuron for other figures
% **************************************************


% $$$ minfNa(V) = 1/(1+exp((V+29.13-modNaAct)/(-8.922)))
% $$$ mtauNa(V) = 3.861-3.434/(1+exp((V+51.35)/(-5.98)))

% for tau, fill a Neuron Vector from -100 mV to 50 mV vals
V=-100:.1:50;
%mtauNa = 3.861-3.434./(1+exp((V+51.35)./(-5.98)));
% better format:
%mtauNa = 0.4270 + 3.434./(1+exp((V+51.35)./(5.98)));
% mod:
mtauNa = 0.1270 + 3.434./(1+exp((V+45.35)./(5.98)));
figure; plot(V, mtauNa)

writeNeuronVecAscii(['neuron-vec-ODowd-Na-chan-act-tau.dat'], V, mtauNa, ...
                      1e-3, 1e-3, 'V', 's', ['DmNav-taum'])

%htauNa = 2.834-2.371./(1+exp((V+21.9)./(-2.641)));
% better this way:
%htauNa = 0.4630 + 2.371./(1+exp((V+21.9)./(2.641)));
% mod a bit to get the right responses:
%htauNa = 0.4030 + .871./(1+exp((V+21.9)./(2.641)));
% replace with exp for better fit to ODowd figs:
htauNa = 0.36 + exp(-(V+20.65)./10.47);
figure; plot(V, htauNa)

writeNeuronVecAscii(['neuron-vec-ODowd-Na-chan-inact-tau.dat'], V, htauNa, ...
                      1e-3, 1e-3, 'V', 's', ['DmNav-tauh'])

% play with Na tau values:

mtauNa = 0.3270 + 2.434./(1+exp((V+51.35)./(5.98)));
htauNa = 0.4630 + 2.371./(1+exp((V+21.9)./(2.641)));
plotFigure(plot_abstract({V, mtauNa, V, htauNa}, {'V', '\tau'}, '', ...
                         {'\tau_m', '\tau_h'}, 'plot', ...
                         struct('axisLimits', [-40 20 NaN NaN], ...
                                'grid', 1)), '', struct('figureHandle', 18))

% $$$ mtauKs(V) = 2.03 + 1.96 /(1+exp((V-29.83)/3.32))  

mtauKs = 2.03 + 1.96 ./(1+exp((V-29.83)./3.32));
figure; plot(V, mtauKs)
writeNeuronVecAscii(['neuron-vec-Kslow-chan-act-tau.dat'], V, mtauKs, ...
                      1e-3, 1e-3, 'V', 's', ['DmKdr-taum'])

mtauKf = 1.94+2.66./(1+exp((V-8.12)./7.96));
figure; plot(V, mtauKf)
writeNeuronVecAscii(['neuron-vec-Kfast-chan-act-tau.dat'], V, mtauKf, ...
                      1e-3, 1e-3, 'V', 's', ['DmKA-taum'])

htauK = 1.79+515.8./(1+exp((V+147.4)./(28.66)));
figure; plot(V, htauK)
writeNeuronVecAscii(['neuron-vec-Kfast-chan-inact-tau.dat'], V, htauK, ...
                      1e-3, 1e-3, 'V', 's', ['DmKA-tauh'])

% ****************************************
% FIGURE 1A: NaT channel simulation
% ****************************************

% under ../morphological/, run soma-vclamp-testbed.ses with nrngui
% and insert the channel in chan-DmNaT-ODowd.hoc to simulate it.
% example:
% $ nrngui soma-vclamp-testbed.ses
% oc> load_file("chan-DmNaT-ODowd.hoc")
%
% To insert the channel, select Build->"single compartment" from the
% menu, and in the window that opened, check "DmNaT". Open a new
% current graph to watch VClamp[0].i - select "Keep lines" from the
% right-click menu.  Simulate DmNaT with "VClamp Family" from the already
% open I/V Clamp Electrode window. Clicking on "Vary Test level"
% should produce Fig 1A.

% ****************************************
% FIGURE 1B: NaT recording from 3rd instar aCC
% ****************************************

% load data
na_vc_L3_dirname = '../data/';
cell1_vc1 = ...
    abf2voltage_clamp([ na_vc_L3_dirname '09n09001.abf' ], 'L3 Na VC', struct('ichan', 2));
cell1_vc2 = ...
    abf2voltage_clamp([ na_vc_L3_dirname '09n09002.abf' ], 'L3 Na VC', struct('ichan', 2));
cell1_vc3 = ...
    abf2voltage_clamp([ na_vc_L3_dirname '09n09003.abf' ], 'L3 Na VC', struct('ichan', 2));
cell1_vc4 = ...
    abf2voltage_clamp([ na_vc_L3_dirname '09n09004.abf' ], 'L3 Na VC', struct('ichan', 2));

% do an current average
cell1_avg_vc = cell1_vc1;
cell1_avg_vc.i = avgTraces([cell1_vc1.i cell1_vc2.i cell1_vc3.i cell1_vc4.i ]);
plot(cell1_avg_vc)

% limit voltage steps
plot(setLevels(cell1_avg_vc, [4:9]), '', ...
     struct('axisLimits', [122 133 NaN NaN], ...
            'fixedSize', [2 3], 'ColorOrder', gray(1), ...
            'xTicksPos', 'bottom', 'noTitle', 1, ...
            'yLabelsPos', 'none', ...
            'relativeSizes', [3 2]))

print -depsc2 L3-Na-VC/marley-cell-2009-11-09-VC-Na.eps


% ****************************************
% FIGURE 1C/D: Kf and Ks channels
% ****************************************

% Requires the model_data_vcs_Kprepulse object defined in this
% directory, which is a subclass of Pandora's model_data_vcs
% class. Also needs the param_fitter toolbox.

% VC data files are required to get Kslowfast_vc and Kslow_vc:
Kfastslow_datadir = '../data/';
Kslow_vc = abf2voltage_clamp([ Kfastslow_datadir 'trace008_p9.abf' ...
                   ], '', struct('ichan', ':'));
Kslowfast_vc = abf2voltage_clamp([ Kfastslow_datadir 'trace009_p9.abf' ...
                   ], '', struct('ichan', ':'));

% there is a bug with parfor
I_Kf_v3.props.parfor=0;
I_Ks_v3.props.parfor=0;
I_Ktot_capleak_delay_v.props.parfor = 0;
    
% simulate the channels and save the data
Kall_data_high_vs_Ktotal_2tauh_p4_model_capleak_Kmd = ...
    model_data_vcs_Kprepulse(I_Kf_v3 + I_Ks_v3, ...
                             Kslowfast_vc, Kslow_vc, ...
                             ['3rd instar Marley data 2009/08/26 vs ' ...
                    'Kf_2tauh_v2 + Ks_p4 Neurofit model, Kf taum sigmoid']);

% make nicer plot
plotFigure(plotDataCompare(Kall_data_high_vs_Ktotal_2tauh_p4_model_capleak_Kmd, '', ...
                           struct('showV', 1, ...
                                  'axisLimits', [105 160 NaN NaN], ...
                                  'xTicksPos', 'bottom', ...
                                  'fixedSize', [4 5])))


% ****************************************
% FIGURE 1F: activation and time constant 
% voltage dependence
% ****************************************

% plot all together, with the v3 version with Kf+Ks
plotFigure(plot_superpose({...
  plot_abstract(I_Kf_v3.m.inf.^4, '', ...
                    struct('noTitle', 1, 'fixedSize', [4 2], ...
                           'ColorOrder', [0 0 1; 0 0 1; 1 0 0; 0 0.6 0; 0 0.6 0; 0 0.6 0], ...
                           'legendLocation', 'EastOutside', ...
                           'axisLimits', [-65 45 NaN NaN], ...
                           'grid', 1, 'plotProps', ...
                           struct('LineWidth', 2))), ...
  plot_abstract(I_Kf_v3.h.inf), plot_abstract(I_Ks_v3.m.inf.^4), ...
  plotInfs(I_DmNav10_ODowd_v), plot_abstract(I_DmNav10_P_WHLoocyte1_v.m.inf)}))

% put inact lines dashed 
print -depsc2 doc/model-all-act-inact-curves-Kf+Ks-v3-Na-ODowd-mod.eps

% taus
plotFigure(plot_superpose({...
  plot_abstract(I_Kf_v3.m.tau, '', ...
           struct('noTitle', 1, 'fixedSize', [3 2], ...
                  'ColorOrder', [0 0 1; 0 0 1; 1 0 0; 0 0.6 0; 0 0.6 0], ...
                  'noLegends', 1, ...
                  'axisLimits', [-65 45 NaN NaN], ...
                  'grid', 1, 'plotProps', ...
                  struct('LineWidth', 2))), ...
  plot_abstract(I_Kf_v3.h.tau), plot_abstract(I_Ks_v3.m.tau), plotTaus(I_DmNav10_ODowd_v)}));

% put inact lines dashed 
print -depsc2 doc/model-all-tau-curves-Kf+Ks-v3-Na-ODowd-mod.eps


