%This script can be used to run and plot the output of multiple .set files
%for a specific .ode file in XPPAUT. This script relies on functions from 
%Rob Clewly's XPP-Python interface.
%S. Wittman, 6 October 2019

file='4p-e.ode';
sets = {'4p-e_intact.set'};

for i=1:length(sets)
    success=RunXPP(file,sets{i}); %Formatting of this line is dependent on the version of RunXPP
    if success==0
        display('Failed to run');
        return
    end
    
    start_var = 1; %This can remove the beginning of a run, like transience
    data=load('output.dat');
    time=data(start_var:end,1);
    time = time; %If there is any transience, adjust for it by subtracting

    v1=data(start_var:end,2); %The correct columns from output.dat must be specified
    v2=data(start_var:end,6);
    v3=data(start_var:end,9);
    v4=data(start_var:end,12);
    
    a=figure;
    hold on
    plot(time,v1,'color',[0,0,0],'LineWidth',2)
    plot(time,v2,'color',[0,0,1],'LineWidth',2)
    plot(time,v3,'color',[0,0.7,0],'LineWidth',2)
    plot(time,v4,'color',[0.85,0.33,0.1],'LineWidth',2)
    leg=legend('V_p_b_c','V_b_c','V_k_f_-_e','V_k_f_-_i');
    leg.FontSize = 10;
    leg.Box = 'off';
    leg.Orientation = 'horizontal';
    xlabel('Time (ms)');
    ylabel('(mV)');
    axis([0 5000 -80 0]);
    % title(sets(i).name);
    title(sets{i},'Interpreter','none');
    box off;
    set(a,'color','white');
end
