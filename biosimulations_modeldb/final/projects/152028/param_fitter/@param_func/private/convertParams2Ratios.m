function param_vals = convertParams2Ratios(param_vals, props)

% convertParams2Ratios - Converts parameter values into relative range ratios.
%
% Usage:
%   param_vals = convertParams2Ratios(param_vals, props)
%
% Parameters:
%   param_vals: Vector of parameter values.
%   props: A structure with any optional properties.
%     onlyIdx: Set only these parameters
%
% Returns:
%   param_vals: Vector of updated parameter values.
%
% Description:
%
% Example:
%   >> new_params = convertParams2Ratios([2 3 4], a_ps.props)
%
% See also: param_func
%
% $Id: convertParams2Ratios.m 88 2010-04-08 17:41:24Z cengiz $
%
% Author: Cengiz Gunay <cgunay@emory.edu>, 2009/06/01

% Copyright (c) 2009 Cengiz Gunay <cengique@users.sf.net>.
% This work is licensed under the Academic Free License ("AFL")
% v. 3.0. To view a copy of this license, please look at the COPYING
% file distributed with this software or visit
% http://opensource.org/licenses/afl-3.0.php.

if ~ exist('props', 'var')
  props = struct;
end

if isfield(props, 'onlyIdx')
  idx = props.onlyIdx;
else
  idx = ':';
end

% convert only if ranges are defined
if isfield(props, 'paramRanges')
  param_ratios = (param_vals - props.paramRanges(1, idx)) ./ ...
      diff(props.paramRanges(:, idx), 1, 1);
  nonnan_idx = ~isnan(param_ratios);
  param_vals(nonnan_idx) = param_ratios(nonnan_idx);
end