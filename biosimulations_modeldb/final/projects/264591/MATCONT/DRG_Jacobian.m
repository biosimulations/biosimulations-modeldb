syms v m17 h17 s17 m18 h18 n nKA hKA gNa17 gNa18 gK gKA gl I V12 g

kv=150;
kt=30; %Length of an action potential approximately
%gNa17 = 18;
vna = 67.1/kv; %Check this number
% I Na1.7


am17 = 15.5 / (1 + exp( -(v*kv -5 )/12.08));
bm17 = 35.2 / (1 + exp( (v*kv+72.7+ V12)/16.7 ));
tm17 = 1 / (am17 + bm17);
minf17 = tm17 * am17;

fm17 = kt*(minf17 - m17)/tm17;

ah17 = 0.38685 / (1 + exp( (v*kv + 122.35)/15.29 ));
bh17 = -0.00283 + 2.00283 / (1 + exp( -(v*kv + 5.5266)/12.70195 ));
th17 = 1 /(ah17 + bh17);
hinf17 = th17*ah17;

fh17 = kt*(hinf17 - h17)/th17;


as17 = 0.00003 + 0.00092 / (1 + exp( (v*kv + 93.9)/16.6 ));
bs17 = 132.05 - (132.05 / (1 + exp( (v*kv - 384.9)/28.5 )));
ts17 = 1 / (as17 + bs17);
sinf17 = ts17*as17;

fs17 = kt*(sinf17 - s17)/ts17;

INa17 = gNa17 * m17^3 * h17 * s17 * (v-vna) / g;

% I Na1.8

%gNa18 = 7;



am18 = 2.85 - (2.839 / (1 + exp ( (v*kv-1.159)/13.95 )));
bm18 = 7.6205 / ( 1 + exp( (v*kv + 46.463)/8.8289 ));
tm18 = 1 / (am18 + bm18);
minf18 = tm18*am18;

fm18 = kt*(minf18 - m18)/tm18;

th18 = 1.218 + 42.043 * exp ( - ((v*kv+38.1)^2)/(2*15.19^2) );
hinf18 = 1 / (1 + exp( (v*kv + 32.2)/4 ));

fh18 = kt*(hinf18 - h18)/th18;

INa18 = gNa18 * m18 * h18 * (v - vna) / g;

% I K

%gK = 4.78;
vk = -84.7/kv; %Check this


an = 0.001265*(v*kv + 14.273) / (1 - exp( -(v*kv + 14.273)/10 ));
an2 = 0.001265*10;
bn = 0.125*exp(- (v*kv + 55)/2.5 );
ninf = 1 / (1 + exp(- (v*kv + 14.62) / 18.38 ));
tn = (1 / (an + bn)) + 1;
tn2 = (1 / (an2 + bn)) + 1;
fn = kt*(ninf - n)/tn;
fn2 = kt*(ninf - n)/tn2;

IK = gK * n * (v - vk) / g;

% I KA

%gKA = 8.33;

ninfKA = ( 1 / (1 + exp( - (v*kv + 5.4) / 16.4 ))) ^ 4;
ntKA = 0.25 + 10.04*exp( -(v*kv + 24.67)^2 / (2*34.8^2) );

fnKA = kt*(ninfKA - nKA)/ntKA;

hinfKA = 1 / (1 + exp((v*kv+49.9)/4.6 ));
htKA = 20 + 50*exp(-(v*kv+40)^2/(2*40^2));
htKA2 = 5;
fhKA = kt*(hinfKA - hKA)/htKA;
fhKA2 = kt*(hinfKA - hKA)/htKA2;

IKA = gKA * nKA * hKA * (v-vk) / g;

% I leak
%gl = 0.0575;
vl = -58.91/kv;
gl=0.0575;

Il = gl*(v-vl) / g;

c=0.93;
A=21.68;

fv = (kt*g/c)*(I/(A*kv*g) - (INa17 + INa18 + IK + IKA + Il));


J = jacobian([fv, fm17, fh17, fs17, fm18, fh18, fn, fnKA, fhKA],[v, m17, h17, s17, m18, h18, n, nKA, hKA]);

JP = jacobian([fv, fm17, fh17, fs17, fm18, fh18, fn, fnKA, fhKA],[V12,I,gNa17,gNa18,gK,gKA]);

JN = jacobian([fn2],[v, m17, h17, s17, m18, h18, n, nKA, hKA]);

JhKA = jacobian([fhKA2],[v, m17, h17, s17, m18, h18, n, nKA, hKA]);

digits(4);
J=vpa(J);
JP=vpa(JP);
JN=vpa(JN);
JhKA=vpa(JhKA);

matlabFunction(J,'Vars',[v m17 h17 s17 m18 h18 n nKA hKA V12 I gNa17 gNa18 gK gKA g],'file','J_D.m');
matlabFunction(JP,'Vars',[v m17 h17 s17 m18 h18 n nKA hKA V12 I gNa17 gNa18 gK gKA g],'file','JP_D.m');
matlabFunction(JN,'Vars',[v m17 h17 s17 m18 h18 n nKA hKA V12 I gNa17 gNa18 gK gKA g],'file','JN_D.m');
matlabFunction(JhKA,'Vars',[v m17 h17 s17 m18 h18 n nKA hKA V12 I gNa17 gNa18 gK gKA g],'file','JhKA_D.m');

