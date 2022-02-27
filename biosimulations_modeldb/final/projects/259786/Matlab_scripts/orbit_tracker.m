%This script was used to generate figures tracking model trajectories
%near fixed points. For this script to work, the specified set must have
%some kind of orbital behavior in a certain predictable region. The limits
%in this script must be manually set to provide a good window which
%contains the orbital behavior. Each individual orbit cycle is plotted in a
%different color. This script relies on functions from Rob Clewly's XPP-Python
%interface.
%S. Wittman, 6 October 2019
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
filename='4p-r.ode'; %THIS BLOCK FOR 4P-R
setname='4p-r.set';
limits = [-36.3 -33.2 0.28 0.29];
=1;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% filename='4p-e.ode'; %THIS BLOCK FOR 4P-E
% setname='4p-e.set';
% limits=[-61.5 -59.1 0.89 0.91];
% dir=2;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
success=RunXPP(filename,setname);
if success==0
    disp('Failed to run file')
    return
end
data=load('output.dat');
half_y = mean(limits(3:4)); 
half_x = mean(limits(1:2));
start =  1;
fin = 100000;

time=data(:,1);
time = time - 1000;
v1=data(1:end,2); 
h1=data(1:end,3);
v2=data(1:end,4);
h2=data(1:end,5);
v3=data(1:end,6);
h3=data(1:end,7);
v4=data(1:end,8);
h4=data(1:end,9);
v5=data(1:end,10);
h5=data(1:end,11);
 
for p=1:20 %ADJUST THIS IF YOU ADJUST THE DURATIONS IN THE SET (i.e, 20*10,000=200,000) %
    if ~(p==1)
        start = start + 90000; %THESE VALUES ADJUST THE LENGTH OF EACH PLOT
        fin = fin + 100000; 
    end
    if dir==1
        vvar=v3(start:fin); 
        hvar=h3(start:fin);
    else
        vvar = v1(start:fin);
        hvar = h1(start:fin);
    end
    figure;
    hold on
    Or=zeros(1000,1);
    axis(limits);
    %This loop may be useful in other programs
    in_range=0;
    hflag=0;
    vflag=0;
    z=1;
    q=1;
    r=1;
    Orbit_Time=zeros(1000,1);

    for i=2:length(vvar)
        %find up and down flags for I and E, calculate periods
        if dir == 1
           if vvar(i)<limits(2) && vvar(i-1)>=limits(2)
               test1 = 1;
           else
               test1 = 0;
           end
           if vvar(i)<limits(1) && in_range==1 && vvar(i-1)>=limits(1)
               test2 = 1;
           else
               test2 = 0;
           end
        elseif dir == 2
           if vvar(i)>limits(1) && vvar(i-1)<=limits(1)
               test1 = 1;
           else
               test1 = 0;
           end
           if vvar(i)>limits(2) && in_range==1 && vvar(i-1)<=limits(2)
               test2 = 1;
           else
               test2 = 0;
           end 
        end
        if test1
            in_range=1;
            j=1;
            orbits=0;
            M=zeros(10000,2);
        end
        if test2
            in_range=0;
            M=M(M(:,2)>0,:);
            Or(z)=orbits;
            z=z+1;
            if r == 1
                col = 'k';
            elseif r == 2
                col = 'r';
            elseif r == 3
                col = 'c';
            elseif r == 4
                col = 'm';
            elseif r == 5
                col = 'g';
            elseif r == 6
                col = 'y';
                r = 0;
            end
            disp(M);
            plot(M(:,1),M(:,2),'color',col,'LineWidth',1);
            r = r + 1;
        end
        if vflag==0 && in_range==1
            if hvar(i-1)< half_y
                if hvar(i)>= half_y
                    hflag=1;
                end
            end
            if hvar(i-1)>= half_y
                if hvar(i)< half_y
                    hflag=0;
                end
            end
        end
        if hflag==1 && in_range==1
            if vvar(i-1)< half_x 
                if vvar(i)>= half_x
                    vflag=1;
                end
            end
            if vvar(i-1)>= half_x
                if vvar(i)< half_x
                    vflag=0;
                end
            end
        end
        if vflag==1 && hflag==1 && in_range==1
            if hvar(i-1)>=half_y
                if hvar(i)<half_y
                    orbits=orbits+1;
                    if orbits>=2
                        Orbit_Time(q)=time(i)-orbit_timer;
                        q=q+1;
                    end
                    orbit_timer=time(i);
                    vflag=0;
                    hflag=0;
                end
            end
        end
        if in_range==1
            M(j,1)=vvar(i);
            M(j,2)=hvar(i);
            j=j+1;
        end
    end

    Or=Or(1:z);
    Orbit_Time=Orbit_Time(1:q);
    mean(Orbit_Time)
end

