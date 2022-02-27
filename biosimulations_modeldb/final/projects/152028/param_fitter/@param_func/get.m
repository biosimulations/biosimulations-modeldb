function b = get(a, attr)
% get - Defines generic attribute retrieval for objects.
%
% Author: Cengiz Gunay <cgunay@emory.edu>, 2004/09/14

% Copyright (c) 2007 Cengiz Gunay <cengique@users.sf.net>.
% This work is licensed under the Academic Free License ("AFL")
% v. 3.0. To view a copy of this license, please look at the COPYING
% file distributed with this software or visit
% http://opensource.org/licenses/afl-3.0.php.
if isfield(struct(a), attr)
  b = a.(attr);
elseif find(ismember(getColNames(a.tests_db), attr))
  % TODO: stop using tests_db!
  b = onlyRowsTests(a.tests_db, 1, attr);
else
  b = get(a.tests_db, attr);
end
