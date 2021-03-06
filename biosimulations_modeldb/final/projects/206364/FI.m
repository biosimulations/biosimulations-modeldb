N=500; %ms
trial=1;

dt=0.1;

n_spike=0;
sum=0;

Imeanmax=1000;
dImean=1;
Imean=-10000;

% cell 1
c=268; 
gl=8.47;
el=-51.31; 
vt=-53.23;
delta=0.85; 
vreset=-60.35;
a=37.79; tauw=20.76; b=441.12;


% dendritic filtering
tauc=0.317;       % ms
taus=30.91;       % ms2
c1=66.97;         % microF/cm^2
cm=1;             % microF
S1=c1/cm;         % S_dend, calculated acccording "pulse" fit
p=0.065;          % S_soma / (S_soma + S_dend)
gc=cm*p*(1-p)*(1/tauc-1/taus); % coupling conductance
G=gl +gc/p/(1-p); % total conductance: leak conductance + coupling conductance;

vspike=0;

IN=Imean+dImean:dImean:Imeanmax;  % all input currents

for q=1:1:round((Imeanmax-Imean)/dImean)
    Imean=Imean+dImean;
                                                                     
                 
            for j=1:1:trial
            
                % set initial conditions for every trial
            vd(1)=-56;
            wd(1)=0;
            V(1)=0;
     
     %       vn(1)=-56;
     %       wn(1)=0;
                
                for i=2:1:round(N/dt)
                     t(i)=(i-1)*dt;    

% "pure" input I with no dendrite
% input=Imean*S1;
% gc=0;


% input with dendrite present
 input=Imean;
 
% input with compensation for dendrite
% input=S1*Imean/(1-gc/p/G);


 % dendrite diff equation
 vd(i)=dt/c*( -gl*(vd(i-1)-el) +gl*delta*exp((vd(i-1)-vt)/delta) -wd(i-1) + input/S1 -gc/p*V(i-1) ) + vd(i-1);
 V(i)=dt/c*( -G*V(i-1) +input/S1 ) + V(i-1);
 wd(i)=dt/tauw*(a*(vd(i-1)-el)-wd(i-1)) + wd(i-1);

 
 % no dendrite
% vn(i)=dt/c*(-gl*(vn(i-1)-el)+gl*delta*exp((vn(i-1)-vt)/delta)-wn(i-1)+input) + vn(i-1);
% wn(i)=dt/tauw*(a*(vn(i-1)-el)-wn(i-1)) + wn(i-1);
 
             if  vd(i)>=vspike
                 vd(i-1)=0;            % add sticks to the previous step     
                 vd(i)=vreset;
                 wd(i)=wd(i) + b;
                 n_spike=n_spike+1;
             end

%              if vn(i)>=vspike
%                 vn(i-1)=0;            % add sticks to the previous step     
%                 vn(i)=vreset;
%                 wn(i)=wn(i) + b;
%                 n_spike=n_spike+1;
%             end
   
                    
                end
                sum=sum+n_spike;
                n_spike=0;
            end   
    freq(q)=sum/N/trial*1000; %averaged frequency after N iteration, *1000 to get Hz
    sum=0;
    
end



plot(IN,freq,'.');
xlabel('I_{hold}, pA');
ylabel('Frequency, Hz');