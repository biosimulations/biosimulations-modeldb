function a_cc = XPP2current_clamp(filename, cip_times, cip_vals, props)

% XPP2current_clamp - Converts XPP model data to current-clamp object.
%
% Usage: 
% a_cc = XPP2current_clamp(filename, cip_times, cip_vals, props)
%
% Parameters:
%   filename: DAT filename obtained with the XPPAUTO's Graphics->Export
%   	data option.
%   cip_times: Start and end times of current injection [ms].
%   cip_vals: A vector of current injection (CIP) parameter values in the XPPAUTO
%   	simulation [nA]. At least provide a vector with the correct number of
%   	parameter values so the data file can be parsed. If there is only
%   	one trace, provide its applied current level as a scalar.
%   props: A structure with any optional properties.
%     Ihold: [nA] Specifies holding current if different than first step value.
%     dt: Simulation time step of recorded data [s]. Use dt*nout of XPP (Default=1e-3).
%     paramsVary: Structure with variable name associated with an
%     		array. If only one value is given cip_vals, use the
%     		values for this variable for the multiple trials found in file.
%     (others are passed to current_clamp)
%
% Returns:
%   a_cc: A current_clamp object.
%
% Description:
%
% See also: plotXPPparamRanges, current_clamp
%
% $Id: XPP2current_clamp.m 1188 2010-04-09 19:56:27Z cengiz $
%
% Author: Cengiz Gunay <cgunay@emory.edu>, 2011/03/04

% Copyright (c) 2011 Cengiz Gunay <cengique@users.sf.net>.
% This work is licensed under the Academic Free License ("AFL")
% v. 3.0. To view a copy of this license, please look at the COPYING
% file distributed with this software or visit
% http://opensource.org/licenses/afl-3.0.php.

% TODO: make this use trace+trace2cc. see example under
% flymotor/paper_full_model/figures_full_morph.m
% advertise this as XPP file loading cap

props = defaultValue('props', struct);

s = load(filename);

% if not varying CIP, take variable values from struct
if isfield(props, 'paramsVary')
  param_names = fieldnames(props.paramsVary);
  num_vals = 1;
  for param_num = 1:length(param_names)
    param_vals = props.paramsVary.(param_names{param_num});
    num_vals = num_vals * length(param_vals);
  end
  cip_vals = repmat(cip_vals, 1, num_vals);
end

num_traces = length(cip_vals);
num_allpts = size(s, 1);
num_onepts = num_allpts / num_traces;
data = reshape(s(:, 2), num_onepts, num_traces);

I_hold = getFieldDefault(props, 'Ihold', cip_vals(1));

time = s(1:num_onepts, 1);
dt = getFieldDefault(props, 'dt', diff(time(1:2)) * 1e-3);

current_steps = ...
    get(makeIdealClampV([cip_times num_onepts * dt * 1e3], I_hold, cip_vals, I_hold, dt * 1e3, ...
                        filename), 'data');

a_cc = ...
    current_clamp(current_steps, data, dt, 1e-9, 1e-3, ...
                  filename, ...
                  mergeStructs(props, struct('lowPassFreq', 1000, ...
                                             'filename', filename)));
