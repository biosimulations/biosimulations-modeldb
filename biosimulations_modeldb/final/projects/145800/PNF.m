function [output] = PNF(varargin)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% simple model with PNF structure
% Generated: 11-Sep-2012 19:25:57
% Generated by Jae Kyoung Kim and Daniel Forger by using SBtoolbox2.  
%
% [output] = PNF() => output = initial conditions in column vector
% [output] = PNF('states') => output = state names in cell-array
% [output] = PNF('algebraic') => output = algebraic variable names in cell-array
% [output] = PNF('parameters') => output = parameter names in cell-array
% [output] = PNF('parametervalues') => output = parameter values in column vector
% [output] = PNF(time,statevector) => output = time derivatives in column vector
% [t,x]=ode15s(@PNF,[0 20],PNF()); => output = solution
% 
% State names and ordering:
% 
% statevector(1): M
% statevector(2): Pc
% statevector(3): P
% statevector(4): R
% statevector(5): A
% 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

global time
parameterValuesNew = [];

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% HANDLE VARIABLE INPUT ARGUMENTS
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if nargin == 0,
	% Return initial conditions of the state variables (and possibly algebraic variables)
	output = [0.1, 0.1, 0.1, 0.1, 0.1];
	output = output(:);
	return
elseif nargin == 1,
	if strcmp(varargin{1},'states'),
		% Return state names in cell-array
		output = {'M', 'Pc', 'P', 'R', 'A'};
	elseif strcmp(varargin{1},'algebraic'),
		% Return algebraic variable names in cell-array
		output = {};
	elseif strcmp(varargin{1},'parameters'),
		% Return parameter names in cell-array
		output = {'ao', 'at', 'ah', 'bo', 'bt', 'bh', 'ro', 'rt', 'do', 'dt', ...
			'Kd'};
	elseif strcmp(varargin{1},'parametervalues'),
		% Return parameter values in column vector
		output = [1, 1, 1, 1, 1, 1, 1, 0.0395, 0.2, 0.2, ...
			1e-05];
	else
		error('Wrong input arguments! Please read the help text to the ODE file.');
	end
	output = output(:);
	return
elseif nargin == 2,
	time = varargin{1};
	statevector = varargin{2};
elseif nargin == 3,
	time = varargin{1};
	statevector = varargin{2};
	parameterValuesNew = varargin{3};
	if length(parameterValuesNew) ~= 11,
		parameterValuesNew = [];
	end
elseif nargin == 4,
	time = varargin{1};
	statevector = varargin{2};
	parameterValuesNew = varargin{4};
else
	error('Wrong input arguments! Please read the help text to the ODE file.');
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STATES
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
M = statevector(1);
Pc = statevector(2);
P = statevector(3);
R = statevector(4);
A = statevector(5);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% PARAMETERS
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if isempty(parameterValuesNew),
	ao = 1;
	at = 1;
	ah = 1;
	bo = 1;
	bt = 1;
	bh = 1;
	ro = 1;
	rt = 0.0395;
	do = 0.2;
	dt = 0.2;
	Kd = 1e-05;
else
	ao = parameterValuesNew(1);
	at = parameterValuesNew(2);
	ah = parameterValuesNew(3);
	bo = parameterValuesNew(4);
	bt = parameterValuesNew(5);
	bh = parameterValuesNew(6);
	ro = parameterValuesNew(7);
	rt = parameterValuesNew(8);
	do = parameterValuesNew(9);
	dt = parameterValuesNew(10);
	Kd = parameterValuesNew(11);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% DIFFERENTIAL EQUATIONS
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
M_dot = ao*(A-P-Kd+((A-P-Kd)^2+4*A*Kd)^0.5)/(2*A)-bo*M;
Pc_dot = at*M-bt*Pc;
P_dot = ah*Pc-bh*P;
R_dot = ro*(A-P-Kd+((A-P-Kd)^2+4*A*Kd)^0.5)/(2*A)-do*R;
A_dot = rt*R-dt*A;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% RETURN VALUES
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STATE ODEs
output(1) = M_dot;
output(2) = Pc_dot;
output(3) = P_dot;
output(4) = R_dot;
output(5) = A_dot;
% return a column vector 
output = output(:);
return

