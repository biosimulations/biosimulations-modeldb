%% -----control coditions, a model without spike-prodcing currents---------  
% To add spike producing currents set gbarNa=50 and gDR=2 in DAneuronDB.cpp
% this part produces voltage trace and a phase plane for the reduced model
%mex DAneuronDB.cpp % build mex file
%--------inputs----------------
dt=0.02; TT=5000; N=TT/dt; % step, total time (5000 msec or 5 sec), number of steps
gl=0.18,gh=0; % leak conductance, H-current conductance
gbarnmda=zeros(1,N); % NMDAR conductance (set to 0)
ggaba=zeros(1,N); % GABAR conductance (set to 0)
gampa=zeros(1,N); % AMPAR conductance (set to 0)
Iapp=zeros(1,N); % applied current (set to 0)
% ----------output---------------------- 
[V,Ca] = DAneuronDB(TT,ggaba,gbarnmda,gampa,gh,Iapp); % voltage and calcium
% plot voltage and calcium
close all
figure('Position', [10, 50, 1100, 770]);
subplot(1,3,1:2), plot(dt:dt:TT,V,'k','linewidth',2)
hold on, plot(dt:dt:TT,Ca,'b','linewidth',2)
legend('Voltage','Ca')
xlabel('Time (ms)'), ylabel('Voltage (mV)')
title('Voltage and Ca traces')
set(gca, 'FontSize',14); set(gca,'box','off','color','none')

%plot phase space for the reduced model (no Na, DR and H currents)
% parameters to plot nullcline
k=160; buf=0.00023; zF=0.019298; tc=0.52; r=0.2; gL=0.18; ECa=50; caleak=0.1; gbarCa=2.5;
gbarKCa=7.8; EL=-35; ENa=55; gSNa=0.13; gbarK=1; EK=-90;
vhna=-50; slna=5; VHK=-10; VSK=7;Vcah=-52; Sca=3; Mg=0.5; me=0.062;
gbarnmda=0; ggaba=0;
subplot(1,3,3)
h1=ezplot( @(V,Ca) gbarnmda./(1+0.28*Mg*exp(-me*V))*(0-V) + ggaba.*(-90-V)...
    + gbarCa.*((((-0.0032.*(V-Vcah)./(exp(-(V-Vcah)./Sca) - 1.)))./(((-0.0032.*(V-Vcah)./(exp(-(V-Vcah)/Sca) - 1.)))...
    +(0.05*exp(-(V-Vcah+5)./40.)))).^4).*(ECa-V)+ gL.*(EL-V)+ gSNa.*(1./(1+exp(-(V-vhna)./slna))).*(ENa-V)...
    + gbarK./(1. + exp(-(V-VHK)./VSK)).*(EK-V)+gbarKCa*(Ca.^4./(k.^4+Ca.^4)).*(EK-V),[-100 10],[0 200]);
title('Phase plane')
set(h1,'Color','k','Linewidth',2,'LineStyle','--')
hold on, plot(V,Ca,'k','linewidth',2)
set(gca, 'FontSize',14); set(gca,'box','off','color','none')

%% ------------this part produces a figure for a disinhibition burst and a pause ------------------
dt=0.02; TT=8000; N=TT/dt; % step, total time, number of steps
gbarnmda=[repmat(20,1,4000/dt), repmat(0,1,2000/dt), repmat(20,1,2000/dt)]; % NMDAR conductance
ggaba=[repmat(5.9,1,1500/dt), repmat(0,1,1500/dt), repmat(5.9,1,5000/dt)]; % AMPAR conduactance
gampa=zeros(1,N); % AMPAR conductance
Iapp=zeros(1,N); % applied current
figure('Position', [50, 50, 1100, 770]);
subplot(3,1,1), plot(ggaba,'linewidth',2); hold on; plot(gbarnmda,'linewidth',2)
set(gca,'box','off','color','none'); set(gca, 'FontSize',14);
set(gca,'xTick',[]); set(gca,'xColor','w')
ylabel('g (mS/cm^2)')
text(7000,24,'NMDA','Fontsize',13); text(7000,0,'GABA_A','Fontsize',13);
Vm = DAneuronDB(TT,ggaba,gbarnmda,gampa,0,Iapp);
subplot(3,1,2:3), plot(dt:dt:TT,Vm,'k','linewidth',2)
xlabel ('Time (ms)'); ylabel('Voltage (mV)')
set(gca, 'FontSize',14);set(gca,'box','off','color','none')
ylim([-90 0])

%% ---------this part reproduces part of the figure 1 with asynchronous Glu and GABA inputs----------
% asynchronous Glu and GABA inputs produce low frequency firing in DA neuron
%mex DAneuronGABApopulationDB.cpp % 1 DA neurons and a population of GABA neurons

TT=5000; dt=0.02; N=TT/dt; lambda=0.01;% total time (ms), step, number of steps, poisson rate
[Gluinp,st1]=Glu_raster(lambda,TT); % spiketimes of Glu spikes
gbarnmda=repmat(4,1,N); ggaba=repmat(8,1,N);
[Vda,sgaba,Ca,snmda,Vgabaall]=DAneuronGABApopulationDB(TT,Gluinp,ggaba,gbarnmda,0);
NG=30; % number of GABA neurons
Vgabaall1=reshape(Vgabaall,[],NG)';
Vthresh=0;
for i=1:size(Vgabaall1,1)
    crossings(i,:)=(Vgabaall1(i,:)>Vthresh);
    di(i,:)=diff(crossings(i,:));
    stgaba{i}=(find(di(i,:)>0)); % GABA spiketimes
end
frgaba=length(stgaba{2})./(TT/10^3); % mean frequency of GABA neurons
%
figure('Position', [100, 50, 1100, 770]);
positionVector1 = [0.1, 0.82, 0.85, 0.13]; subplot('Position',positionVector1);
for ii=1:length(st1)
    t = st1{ii};
    for jj = 1:length(t)
        line([t(jj) t(jj)],[ii-1 ii],'Color','k','linewidth',1);
    end
end
xlim([50 st1{1}(end)]); set(gca,'YTick',[0:10:35]); ylim([0 35])
ylabel('Neuron #');
set(gca,'box','off','color','none'); set(gca, 'FontSize',14)
set(gca,'xTick',[]); set(gca,'xColor','w')
title('Glu raster','FontSize',14)

positionVector2 = [0.1, 0.62, 0.85, 0.13]; subplot('Position',positionVector2)
for ii=1:length(stgaba)
    t = stgaba{ii};
    for jj = 1:length(t)
        line([t(jj) t(jj)],[ii-1 ii],'Color','k','linewidth',1);
    end
end
xlim([50 stgaba{1}(end)]); set(gca,'YTick',[0:10:30]); ylim([0 30])
ylabel('Neuron #');
title('GABA raster','FontSize',14)
set(gca,'box','off','color','none'); set(gca, 'FontSize',14)
set(gca,'xTick',[]); set(gca,'xColor','w')

positionVector3 = [0.1, 0.48, 0.85, 0.08]; subplot('Position',positionVector3)
plot(sgaba(50/dt:end),'black')
title('GABAR synaptic activation','FontSize',14)
set(gca,'box','off','color','none'); set(gca, 'FontSize',14)
set(gca,'xTick',[]); set(gca,'xColor','w')
ylabel('s_{GABA}');ylim([0 1])

positionVector4 = [0.1, 0.34, 0.85, 0.08]; subplot('Position',positionVector4)
plot(snmda(50/dt:end),'black')
title('NMDAR synaptic activation','FontSize',14)
set(gca,'xTick',[]); set(gca,'xColor','w')
set(gca,'box','off','color','none'); set(gca, 'FontSize',14)
ylabel('s_{NMDA}'); ylim([0 1])

positionVector5 = [0.1, 0.07, 0.85, 0.2];
subplot('Position',positionVector5)
plot(0:dt:TT-50,Vda(50/dt:end),'black')
title('DA neuron voltage','FontSize',14)
xlabel('Time (ms)'); ylabel('Voltage (mV)')
set(gca,'YTick',[-100:20:0]); ylim([-90 0])
set(gca,'box','off','color','none'); set(gca, 'FontSize',14)
