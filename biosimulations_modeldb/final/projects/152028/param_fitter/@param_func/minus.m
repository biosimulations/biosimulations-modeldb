function a_pf = minus(left_pf, right_pf, props)

% minus - left_pf minus right_pf.
%
% Usage:
% a_pf = minus(left_pf, right_pf, props)
%
% Parameters:
%   left_pf, right_pf: param_func objects.
%   props: A structure with any optional properties.
%		
% Returns:
%   a_pf: Resulting object.
%
% Description:
%
% Example:
% >> a_pf = minus(vc1, vc2)
% OR
% >> a_pf = vc1 - vc2;
% plot the result
% >> plot(a_pf)
%
% See also: param_func, minus
%
% $Id: minus.m 1174 2009-03-31 03:14:21Z cengiz $
%
% Author: Cengiz Gunay <cgunay@emory.edu>, 2010/10/11

a_pf = binary_op(left_pf, right_pf, @minus, '-');
