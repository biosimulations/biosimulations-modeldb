%This script should be run in a directory containing a single ode 
%and multiple set files. It creates a bar graph of the average
%inspiratory, expiratory, and total periods, as well as standard
%deviations. This script relies on functions from Rob Clewly's XPP-Python
%interface as well as the free Matlab function barwitherr.
%S. Wittman, 6 October 2019

file=dir('*.ode');
file = file.name;
sets = dir('*.set');
sets = sets.name;
T_T_mean=zeros(length(sets),1);
T_E_mean=zeros(length(sets),1);
T_I_mean=zeros(length(sets),1);
T_T_var=zeros(length(sets),1);
T_E_var=zeros(length(sets),1);
T_I_var=zeros(length(sets),1);
T_T_dev=zeros(length(sets),1);
T_E_dev=zeros(length(sets),1);
T_I_dev=zeros(length(sets),1);


for j=1:length(sets)
    s=sets{j};
    success=RunXPP(file,s);
    if success==0
        disp('Failed to run file')
        return
    end
    %Get data
    data=load('output.dat');
    time=data(50000:end,1); %Ignoring transient noise model dynamics at the beginning of the trial
    v1=data(50000:end,2);
    v2=data(50000:end,3);

    %Period vectors and their indexes
    t_tot=zeros(1000,1);
    t_tot_i=1;
    t_e=zeros(1000,1);
    t_e_i=1;
    t_i=zeros(1000,1);
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
        if v1(i)>=v2(i)
            if v1(i-1)<v2(i-1)
                i_up_new=time(i);
                if i_up>0
                    t_tot(t_tot_i)=i_up_new-i_up;
                    t_tot_i=t_tot_i+1;
                end
                i_up=i_up_new;
            end
        end
        if v2(i)>=v1(i)
            if v2(i-1)<v1(i-1)
                e_up=time(i);
            end
        end
        if v1(i)<v2(i)
            if v1(i-1)>=v2(i-1)
                i_down=time(i);
                if i_up>0
                    t_i(t_i_i)=i_down-i_up;
                    t_i_i=t_i_i+1;
                end
            end
        end
        if v2(i)<v1(i)
            if v2(i-1)>=v1(i-1)
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
    T_T_mean(j)=mean(t_tot);
    T_E_mean(j)=mean(t_e);
    T_I_mean(j)=mean(t_i);
    T_T_var(j)=var(t_tot);
    T_E_var(j)=var(t_e);
    T_I_var(j)=var(t_i);
    T_T_dev(j)=sqrt(var(t_tot));
    T_E_dev(j)=sqrt(var(t_e));
    T_I_dev(j)=sqrt(var(t_i));    
    
end

figure;

Q1=[T_I_dev(1),T_E_dev(1),T_T_dev(1),;
    T_I_dev(2),T_E_dev(2),T_T_dev(2);
    T_I_dev(3),T_E_dev(3),T_T_dev(3);
    T_I_dev(4),T_E_dev(4),T_T_dev(4);
    T_I_dev(5),T_E_dev(5),T_T_dev(5);
    T_I_dev(6),T_E_dev(6),T_T_dev(6);
    T_I_dev(7),T_E_dev(7),T_T_dev(7);
    T_I_dev(8),T_E_dev(8),T_T_dev(8)];

Q2=[T_I_mean(1),T_E_mean(1),T_T_mean(1);
    T_I_mean(2),T_E_mean(2),T_T_mean(2);
    T_I_mean(3),T_E_mean(3),T_T_mean(3);
    T_I_mean(4),T_E_mean(4),T_T_mean(4);
    T_I_mean(5),T_E_mean(5),T_T_mean(5);
    T_I_mean(6),T_E_mean(6),T_T_mean(6);
    T_I_mean(7),T_E_mean(7),T_T_mean(7);
    T_I_mean(8),T_E_mean(8),T_T_mean(8)];

barwitherr(Q1,Q2);

