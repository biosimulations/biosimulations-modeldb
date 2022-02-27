function [upc,upf,downc,downf]=ramp(test)

mydata=load('test.dat');
[r,c]=size(mydata);
t=mydata(:,1);
v=mydata(:,2);
iapp=mydata(:,23);


a=1;
peak=[0;0];
curr=[0;0];
t2=[0;0];
tf=[0;0];
for i=2:r-1
    if v(i)>-20
        if v(i)>v(i-1)
            if v(i+1)<v(i)
                peak(a)=t(i);
                curr(a)=iapp(i);
                a=a+1;
            end
        end
    end
end
[r2,c2]=size(peak);
peak2=peak;
peak=peak/1000;
freq=[0;0];
curr2=[0;0];

for i=1:r2-1
    freq(i+1)=1/(peak(i+1)-peak(i));
    curr2(i+1)=curr(i+1);
end

[r3,c3]=size(peak2);

b=2;
for i=1:r
    if b<r3+1
        if peak2(b)==t(i)
            tf(i)=freq(b);
            b=b+1;
        else tf(i)=NaN;
        end
    else tf(i)=NaN;    
    end
end

[Y,I]=max(curr);
upc=curr2(2:I);
downc=curr2(I:r2);
upf=freq(2:I);
downf=freq(I:r2);

MxF=max(freq);
MxT=max(t);
MxC=max(upc);
MnC=min(downc);

tf=tf+55;

figure;
plot(t,v,'k',t,iapp-100,'k',t,tf,'k*-');
axis([0 10000 -120 150]);
xlabel('Time (ms)');
ylabel('Membrane Potential (mV)');


figure;
plot(upc,upf,'k*-',downc,downf,'ko-');
axis([-40 30 0 60]);
%axis([MnC-0.2 MxC+0.2 0 MxF+10]);
xlabel('Current (\muA/cm^2)');
ylabel('Frequency (Hz)');
