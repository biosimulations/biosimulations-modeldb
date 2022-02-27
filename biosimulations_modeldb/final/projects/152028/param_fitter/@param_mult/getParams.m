function param_vals = getParams(a_ps, props)

% getParams - Gets the parameters of all contained functions.
%
% Usage:
%   param_vals = getParams(a_ps, props)
%
% Parameters:
%   a_ps: A param_mult object.
%   props: A structure with any optional properties.
%     recursive: If 1, include all child objects (default=1).
%     (rest passed to param_func/getParams)
%		
% Returns:
%   param_vals: Vector of parameter values.
%
% Description:
%
% Example:
% Get absolute parameter values:
%   >> params = getParams(a_ps)
% Set relative ratios:
%   >> param_ratios = getParams(a_ps, struct('direct', 1))
%
% See also: param_func, param_mult
%
% $Id: getParams.m 464 2011-05-16 21:37:05Z cengiz $
%
% Author: Cengiz Gunay <cgunay@emory.edu>, 2009/12/09

% Copyright (c) 2009 Cengiz Gunay <cengique@users.sf.net>.
% This work is licensed under the Academic Free License ("AFL")
% v. 3.0. To view a copy of this license, please look at the COPYING
% file distributed with this software or visit
% http://opensource.org/licenses/afl-3.0.php.

if ~ exist('props', 'var')
  props = struct;
end
isRec = getFieldDefault(props, 'recursive', 1);

param_vals = getParams(a_ps.param_func, props);

if isRec ~= 0
  for a_f = struct2cell(a_ps.f)'
    a_f = a_f{1};
    param_vals = [ param_vals, getParams(a_f, props) ];
  end
end
