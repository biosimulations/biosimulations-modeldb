function a_db = XPPrange2CIPdb(filename, cip_times, cip_vals, props)

% XPPrange2CIPdb - Converts XPP model data to CIP measures database (i.e., extracts spiking measures in response to current injection).
%
% Usage: 
% a_db = XPPrange2CIPdb(filename, cip_times, cip_vals, props)
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
%     recalc: If 1, overwrite DB file even if it exists.
%     Ihold: [nA] Specifies holding current if different than first step value.
%     dt: Simulation time step of recorded data [s]. Use dt*nout of XPP (Default=1e-3).
%     paramsVary: Structure with variable name associated with an
%     		array. If only one value is given cip_vals, use the
%     		values for this variable for the multiple trials found in file.
%     (others are passed to XPP2current_clamp)
%
% Returns:
%   a_db: A params_tests_db.
%
% Description:
%   Saves the database as a MAT file for loading later and it will skip
% generating the database if it finds an existing file.
%
% See also: XPP2current_clamp, plotXPPparamRanges, current_clamp
%
% $Id: XPPrange2CIPdb.m 1188 2010-04-09 19:56:27Z cengiz $
%
% Author: Cengiz Gunay <cgunay@emory.edu>, 2011/03/25

% Copyright (c) 2011 Cengiz Gunay <cengique@users.sf.net>.
% This work is licensed under the Academic Free License ("AFL")
% v. 3.0. To view a copy of this license, please look at the COPYING
% file distributed with this software or visit
% http://opensource.org/licenses/afl-3.0.php.

props = defaultValue('props', struct);

file_suffix = '_db.mat';
db_file = '';

[pathstr,basename,ext] = fileparts(filename);

if ~isempty(pathstr)
  db_file = [pathstr filesep];
end
db_file = [db_file basename file_suffix];

if exist(db_file , 'file')
  disp(['Loading existing DB file: ' db_file ]);
  load(db_file);
else
  a_db = ...
      params_tests_db(XPP2current_clamp(filename, ...
                                        cip_times, cip_vals, ...
                                        props));
  disp(['Saving DB to file: ' db_file ]);
  save(db_file, 'a_db');
end
