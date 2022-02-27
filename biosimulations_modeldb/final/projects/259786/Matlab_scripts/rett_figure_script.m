%This script was used to generate figures tracking the mean and standard
%deviation of the model cycles across a range of inhibition. This script
%allows the exploration of this relationship across multiple models, 
%multiple regimes, and a range of noise levels. For this script to work, 
%the appropriate model and set fies must be on the Matlab path. This script
%relies on functions from Rob Clewly's XPP-Python interface.
%S. Wittman, 6 October 2019
inhib_list=(1:-.025:0);
noise_list=(0.45:0.05:0.55);
%For regime, 1 corresponds to intact, 0 to vagotomy
regime_list=[1,0]; 
update_par(1).name='kf_par';
update_par(1).type='PAR';
update_par(2).name='dscale';
update_par(2).type='PAR';
update_par(3).name='vago';
update_par(3).type='PAR';
files={'4p-e.ode','4p-r.ode'}; %Produce figures for multiple models at once
sets={'4p-e_intact.set','4p-r_intact.set'}; %Each model needs its own set
T_T_mean=zeros(length(inhib_list),length(regime_list),length(files),3); % change the 3 to n if want to do n>3 noise levels
T_T_dev=zeros(length(inhib_list),length(regime_list),length(files),3);
T_T_upper=zeros(length(inhib_list),length(regime_list),length(files),3);
T_T_lower=zeros(length(inhib_list),length(regime_list),length(files),3);
T_T_poly=zeros(2*length(inhib_list),length(regime_list),length(files),3);

for r=1:length(files) %1=LB, 2=RB
    filename=files{r};
    setname=sets{r};
for m=1:length(regime_list)
    %This loop switches between intact and vagotomy
    update_par(3).val=regime_list(m);
    success=ChangeXPPsetFile(setname,update_par(3));
    if success==0
        disp('Failed to change set');
        return
    end
for s=1:3
    update_par(2).val=noise_list(s);
    success=ChangeXPPsetFile(setname,update_par(2));
    if success==0
        disp('Failed to change set');
        return
    end
for j=1:length(inhib_list)
    %This loop changes between various levels of inhibition to the KF
    update_par(1).val=inhib_list(j);
    success=ChangeXPPsetFile(setname,update_par(1));
    if success==0
        disp('Failed to change set');
        return
    end
    success=RunXPP(filename,setname);
    if success==0
        disp('Failed to run file')
        return
    end
    %Get data
    data=load('output.dat');
    time=data(:,1);
    v1=data(:,2);
    v2=data(:,3);
    v3=data(:,4);
    v4=data(:,5);

    %Period vectors and their indexes
    t_tot=zeros(1000,1);
    t_tot_i=1;
    t_e=zeros(2000,1);
    t_e_i=1;
    t_i=zeros(2000,1);
    t_i_i=1;

    %Initialize flags
    i_up=0;
    i_down=0;
    i_up_new=0;
    e_up=0;
    e_down=0;

    %This loop may be useful in other programs
    for i=2:length(v1)
        %find up and down flags for I and E, calculate periods
        if v1(i)>=-40
            if v1(i-1)<-40
                i_up_new=time(i);
                if i_up>0
                    t_tot(t_tot_i)=i_up_new-i_up;
                    t_tot_i=t_tot_i+1;
                end
                i_up=i_up_new;
            end
        end
        if v2(i)>=-40
            if v2(i-1)<-40
                e_up=time(i);
            end
        end
        if v1(i)<-40
            if v1(i-1)>=-40
                i_down=time(i);
                if i_up>0
                    t_i(t_i_i)=i_down-i_up;
                    t_i_i=t_i_i+1;
                end
            end
        end
        if v2(i)<-40
            if v2(i-1)>=-40
                e_down=time(i);
                if e_up>0
                    t_e(t_e_i)=e_down-e_up;
                    t_e_i=t_e_i+1;
                end
            end
        end
    end

    t_tot=t_tot(t_tot>0);
    t_i=t_i(t_i>0);
    t_e=t_e(t_e>0);
    T_T_mean(j,m,r,s)=mean(t_tot);
    save('T_T_mean.mat', 'T_T_mean');
    disp('Model, Regime, Noise, Inhib');
    disp(r);
    disp(m);
    disp(j);
    disp('Dev=');
    disp(sqrt(var(t_tot)));
    T_T_dev(j,m,r,s)=sqrt(var(t_tot));
    
   
end
end
end
end

T_T_upper=T_T_mean+T_T_dev;
T_T_lower=T_T_mean-T_T_dev;

Inhib=[transpose(inhib_list); transpose(fliplr(inhib_list))];
for j=1:length(regime_list)
    for k=1:length(files)
        for c=1:length(noise_list)
            T_T_poly(:,j,k,c)=[T_T_upper(:,j,k,c); flipud(T_T_lower(:,j,k,c))];
        end
    end
end

%Figures are the neediest part of code when you change parameters
models={'4p-e ','4p-r '};
regimes={'Intact ','Vago '};
for k=1:length(files)
    for j=1:length(regime_list)
        for c=1:3
            figure;
            hold on
            fill(Inhib,T_T_poly(:,j,k,c),'c');
            plot(inhib_list,T_T_mean(:,j,k,c), 'b');
            xlabel('Normalized KF Inhibition')
            ylabel('Period (ms)')
            title([models{k}, regimes{j}, 'Noise=', num2str(noise_list(c))]);
            savefig([models{k}, regimes{j}, 'Noise=', num2str(noise_list(c)),'.fig']);
        end
    end
end





