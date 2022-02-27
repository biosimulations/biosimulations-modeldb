%%  THIS IS FOR TA CONSTANT WITH A-CURRENT
clear;

global x1 y gsyn ta tb c1 c2 c3 tk tw tmed tlo c4 ga c5
global r1 r2 r3 
global z2

xmin=10.0;
xmax=1000.0;
dx=5.0;
x=[xmin:dx:xmax];
k=length(x);

% parameters
c1=4.0;
c2=4.6;
c3=3.0;
ta=400.0;
tb=5.0;
tk=125.0;
tw=15.0;
gsyn=4.0;
y=5.0;
tmed=1200.0;
tlo=465.0;
c4=1.0;
ga=3.5;
c5=1.0;
r1=5.0;
r2=0.1;
r3=5.0;

% initial guess
z2=2.0;
z4=5.0;

% find tf for different x
for i=1:k
   x1=x(i);
   z2=fzero('DBjcns2',z2);
   tf(i)=z2;
%   delt(i)=tmed*log((1-exp(-z2/tlo))/c4);
    z3=ga*(1.0-exp(-z2/tlo))/c4;
%   z3=(1.0-exp(-z2/tlo))/c4;
%   z4=ga*((1-exp(-z2/tlo))/c4);
    z4=fzero('DBjcns3',z4); 
    delt(i)=0.0;
%   if (z3 > 1.0) delt(i)=tmed*log(z4);
    if (z3 > 1.0) delt(i)=z4;
    end;
%      else {delt(i)=0.0};

%  delt(i)=tmed*log(z3);

% % checks solutions graphically ...    
%     t=[0:0.01:1000.0];
%     do=(1-exp(-x1/ta))/(1-exp(-x1/ta)*exp(-y/tb));
%	  	 gpeak=gsyn*do;
%		 tfo=(gpeak*c1*exp(-t/tk)+c2*exp(-t/tw)-c3);
%		 clf;
%     plot(t,tfo);
%     hold on
%     plot([0,1000.0],[0,0]);
%     z2
%     pause(0.1);
end;

% plot phase vs period
period=x+y;
%phase=(tf+delt)./(y+x);
phase=(tf+delt)./period;
figure(1)
%clf;
plot(period,phase,'linewidth',2);
xlabel('period','fontsize',14);
ylabel('phase','fontsize',14);

% plot gpeak vs period
%do=(1-exp(-x./ta))./(1-exp(-x./ta)*exp(-y/tb));
%gpeak=gsyn*do;
%figure(2)
%clf;
%plot(period,gpeak,'linewidth',2);
%xlabel('period','fontsize',14);
%ylabel('gpeak','fontsize',14);

% plot ta vs period
%figure(3)
%clf;
%plot(period,delt,'linewidth',2);
%xlabel('period','fontsize',14);
%ylabel('tf','fontsize',14);
