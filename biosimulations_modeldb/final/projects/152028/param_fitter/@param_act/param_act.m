function a_ps = param_act(param_init_vals, id, props)
  
% param_act - Holds parameters of an (in)activation function, y = 1./(1 + exp((x-p.V_half) ./ p.k)).
%
% Usage:
%   a_ps = param_act(param_init_vals, id, props)
%
% Parameters:
%   param_init_vals: Initial values of function parameters, p = [V_half k].
%   id: An identifying string for this function.
%   props: A structure with any optional properties.
% 	   (Rest passed to param_func)
%		
% Returns a structure object with the following fields:
%	param_func.
%
% Description:  
%   Specialized version (subclass) of param_func for activation and
% inactivation curves.
%
% Additional methods:
%	See methods('param_act')
%
% See also: param_func, param_gate_inf, tests_db, plot_abstract
%
% $Id: param_act.m 312 2011-01-21 23:44:19Z cengiz $
%
% Author: Cengiz Gunay <cgunay@emory.edu>, 2009/05/29

  var_names = {'voltage [mV]', 'activation'};
  param_names = {'V_half', 'k'};
  func_handle = @(p,x) 1./(1 + exp((x-p.V_half) ./ p.k));

  props = defaultValue('props', struct);
  id = defaultValue('id', ''); % complain if id is not supplied?
  label = getFieldDefault(props, 'label', 'm');
  
  xpp_func = @(p) [ properAlphaNum(label) ' = 1 / (1 + exp((V - ' num2str(p.V_half) ...
                    ') / ' num2str(p.k) '))' ];

  props = mergeStructs(props, ...
                       struct('xMin', -100, 'xMax', 100, ...
                              'paramRanges', [-100 100; -100 100]', ...
                              'trans2XPP', @(tauf) xpp_func(getParamsStruct(tauf))));

  if nargin == 0 % Called with no params
    a_ps = struct;
    a_ps = class(a_ps, 'param_act', ...
                 param_func(var_names, repmat(NaN, 1, length(param_names)), param_names, func_handle, '', props));
  elseif isa(param_init_vals, 'param_act') % copy constructor?
    a_ps = param_init_vals;
  else
    a_ps = struct;
    a_ps = class(a_ps, 'param_act', ...
                 param_func(var_names, param_init_vals, param_names, ...
                           func_handle, id, props));
  end

