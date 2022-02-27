function a_pf = ...
      param_I_v(param_vals, a_param_act, a_param_inact, id, props)
  
% param_I_v - An (non)inactivating current integrated over a changing V.
%
% Usage:
%   a_pf = 
%     param_I_v(param_vals, a_param_act, a_param_inact, id, props)
%
% Parameters:
%   param_vals: Values for p, q, gmax [uS] and E [mV].
%   a_param_act, a_param_inact: param_act objects for m and h, resp.,
%   	obtained using the param_act_deriv_v function.
%   id: An identifying string for this function.
%   props: A structure with any optional properties.
% 	   (Rest passed to param_func)
%		
% Returns a structure object with the following fields:
%	a_pf: Holds the voltage->current function.
%
% Description:
%   Defines a function f(a_pf, struct('v', V [mV], 'dt', dt [ms])) where v is an array of voltage
% values [mV] changing with dt time steps [ms]. Initial values for the
% activation and inactivation variables are calculated from the first voltage
% value.
%
% Example:
% >> m_ClCa = param_act_deriv_v(f_IClCa_minf_v, f_IClCa_tau_v, 'm');
% >> f_IClCa_v = param_I_v([1 0 1 -41.7], m_ClCa, param_func_nil, 'I_ClCa');
%
% See also: param_act_deriv_v, param_func, tests_db, plot_abstract
%
% $Id: param_I_v.m 790 2014-01-09 19:23:27Z cengiz $
%
% Author: Cengiz Gunay <cgunay@emory.edu>, 2010/01/17

  if ~ exist('props', 'var')
    props = struct;
  end

  props = mergeStructs(props, ...
                       struct('paramRanges', ...
                              [0 4; 0 4; 0 1e3; -100 100]'));
  
  a_pf = ...
    param_mult(...
      {'time [ms]', 'current [nA]'}, ...
      [param_vals], {'p', 'q', 'gmax', 'E'}, ...
      struct('m', setProp(a_param_act, 'name', 'm'), 'h', setProp(a_param_inact, 'name', 'h')), ...
      @(fs, p, x) ...
      p.gmax * ...
      f(fs.m, x) .^ p.p .* ...
      f(fs.h, x) .^ p.q .* ...
      (x.dt - p.E), ...
      id, props);
end
