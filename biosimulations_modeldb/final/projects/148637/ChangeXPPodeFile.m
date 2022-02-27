function success = ChangeXPPodeFile(filename,parset)
%ChangeXPPodeFile  Change parameters / initial conditions in XPP ODE file
%  (c) Robert Clewley, August 2004, 2007
%
%  Usage: success = ChangeXPPodeFile(filename,parset) changes the parameters and initial
%  conditions named in the parset structure to new values by directly modifying the named
%  ODE file. The return value success is a boolean.
%
%  IMPORTANT: All initial conditions to be changed must be explicitly declared in the ODE file
%  using 'init' or 'i', not using the format 'x(0)' for a variable x, etc. Also, implicitly-declared
%  zero initial conditions cannot be altered by this function. For these, you might find it better
%  to use the ChangeXPPsetFile function instead, with the setfile option of RunXPP.
%
%  'number' declarations in XPP are also not supported as range parameters.
%
%  Input arguments:
%  filename should end with the extension '.ode'
%  parset is a structure array with fields 'type', 'name', and 'val'. type must be one
%   of the strings 'PAR' or 'IC'.

success = false;

if isempty(filename) || exist(filename,'file') ~= 2
    error(' Problem with filename passed: file does not exist in specified path')
else
    if ~strcmp('.ode',filename(length(filename)-3:length(filename)))
        error(' Problem with filename passed: must end in `.ode`')
    end
end

cstr = computer;
if strcmp(cstr, 'MAC')
    compix = 0;
elseif strcmp(cstr, 'PCWIN')
    compix = 1;
else % assume UNIX etc. (no-one uses VMS any more)
    compix = 2;
end

fid = fopen(filename,'r');
file_done = false;
pars_found = false;
lineCount = 0;
odefile = {};
lenpars = length(parset);
parnames = cell(1,lenpars);
parnames = {parset(1:lenpars).name}; % make a simple cell array list of parnames to be changed
foundOccurrence = zeros(1,lenpars);

fieldsexpected = {'name','val','type'};
for ix=1:lenpars
    if ~isempty(setdiff(fieldnames(parset(ix)),fieldsexpected))
        fclose(fid);
        error([' Incorrect fields found in argument parset for entry ' num2str(ix)])
    end
	if ~ismember(parset(ix).type,{'PAR','IC'})
        fclose(fid);
        error([' Invalid type, ' parset(ix).type ', specified in entry ' num2str(ix)])
	end
end

% change specified pars when encountered
parsDone = false;
while ~parsDone
    fline = fgetl(fid);
    if ~ischar(fline) % then premature EOF
        fclose(fid);
        error(' End of file reached before specified params found. Cannot continue')
    end
    [token rest] = strtok(fline);
    isParType = strcmp(token, 'par') | strcmp(token, 'p');
    isICType = strcmp(token, 'init') | strcmp(token, 'i');
    if isParType || isICType
        [parsed numparsed] = ParseParLine(rest);
        if numparsed == 0 || isnan(parsed(numparsed).num)
            fclose(fid);
            error(' Problem parsing numerical value of parameter / initial condition in ODE file. Cannot continue')
        end
        if isParType
            flineNew = ['par '];
            typeStr = 'par';
        else
            flineNew = ['init '];
            typeStr = 'ic';
        end
        for i=1:numparsed
            [ispres ix] = ismember(parsed(i).name, parnames);
            if ispres % then a par to be changed has been found
                if (strcmp(parset(ix).type,'PAR') && ~isParType) || (strcmp(parset(ix).type,'IC') && isParType)
                    fclose(fid);
                    error([' Found ' typeStr '`' parset(ix).name '` that didn`t correspond to specified type ' parset(ix).type])
                end
                foundOccurrence(ix) = 1;
                if numparsed==1 || i==numparsed
                    flineNew = [ flineNew, parsed(i).name '=' num2str(parset(ix).val)  ];
                else
                    flineNew = [ flineNew, parsed(i).name '=' num2str(parset(ix).val) ', ' ];
                end
            else
                if numparsed==1 || i==numparsed
                    flineNew = [ flineNew, parsed(i).name '=' num2str(parsed(i).num)  ];
                else
                    flineNew = [ flineNew, parsed(i).name '=' num2str(parsed(i).num) ',' ];
                end
            end
        end
    else
        flineNew = fline;
    end
    odefile = {odefile{:}, flineNew};
    lineCount = lineCount + 1;
    if sum(foundOccurrence) == lenpars % then made all changes necessary
        parsDone = true;
    end
end

% pull in rest of file once params changed
while ~file_done
    fline = fgetl(fid);
    if ~ischar(fline) % then EOF
        file_done = true;
    else
        odefile = {odefile{:}, fline};
        lineCount = lineCount + 1;
    end
end
fclose(fid);

if compix == 1
	% windows uses \r\n line termination
	lineterm = '\r\n';
else
	lineterm = '\n';
end

fidw = fopen( filename ,'w');
if fidw ~= -1
	for line=1:lineCount
        fprintf(fidw, ['%s' lineterm], odefile{line});
	end
	fclose(fidw);
else
    error([' Problem opening file ' filename ' for writing.']);
end
success = true;
return


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


function [parsed, numparsed] = ParseParLine(full_line)
parseddef.num = NaN;
parseddef.name = '';
fline = full_line(isspace(full_line)==0); % get rid of whitespace
fline = strrep(fline,'=',' '); % convert = to space
fline = strrep(fline,',',' '); % convert , to space
numparsed = 0;
endofline = false;
while ~endofline
    [nameStr restStr] = strtok(fline);
    if isempty(nameStr)
        endofline = true;
        continue
    end
    numparsed = numparsed + 1;
    [numStr restStr] = strtok(restStr);
    if isempty(numStr) || isempty(nameStr)
        parsed = parseddef;
        error('Param parse error: Parameter name or value missing!')
    end
    if ~isNum(numStr(isspace(numStr)==0))
        parsed = parseddef;
        error('Param parse error: Parameter value not a number!')
    end
    parsed(numparsed).name = nameStr(isspace(nameStr)==0); % get rid of all whitespace
    parsed(numparsed).num  = str2num(numStr);
    fline = restStr;
end
return


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function result = isNum(data)
% parameter `data` is a string
result = false;
pointCount = 0;
num = [char(48:57),'.','-','e'];
for i=1:length(data)
    if data(i) == '.'
        pointCount = pointCount + 1;
        if pointCount > 1
            return % false
        end
    end
    if ~ismember(data(i),num)
        return % false
    end
end

result = true; % can only get here if all chars were numeric
return
