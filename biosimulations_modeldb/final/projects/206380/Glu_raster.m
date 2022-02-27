function [CinppoisGlu,st]=Glu_raster(lambda,Tmax)
N=Tmax;
M=35; % number of neurons
dt=Tmax/(N-1);

for j=1:M
    T=[];
    T(1)=0;
    i=1;
    while T(i) < Tmax
        U=rand(1,1);
        T(i+1)=T(i)-(1/lambda)*(log(U));
        i=i+1;
    end    
    i=1;
    for i=2:numel(T)-1
        k=round(T(i)/Tmax*N);
        if k<=0   k=1; end
        if k>N k=N; end
        C00(j,k)=1;
    end
    
end
% st
for i=1:size(C00,1)
    st{i}=find(C00(i,:)>0);
end

Glupoissum=sum(C00);
Glupoissum1=[];
Glupoissum1=Glupoissum;
Glupoissum1(Glupoissum1<2)=0; %To simulate convergence of synaptic inputs on the DA neuron,
%we threshold NMDAR to activate only by coincidence of two or more spikes
Glupoissum1(Glupoissum1>1)=1;
dt=0.02; % integration step in mex file
CinputpoisGlu=zeros(length(Glupoissum1),1/dt);
for i=1:length(Glupoissum1)
    for j=1:1/dt
        CinputpoisGlu(i,j)= Glupoissum1(1,i);
    end
end;
%
CinputpoisGlu=CinputpoisGlu';
%
CinppoisGlu=CinputpoisGlu(:);