% A: time series (each columns are observations)
% eigval: eigen values

function eigval=pca(A)
[M,N]=size(A); 
B=A-ones(M,1)*mean(A);
C=cov(B);
eigval=eig(C)';        
return
