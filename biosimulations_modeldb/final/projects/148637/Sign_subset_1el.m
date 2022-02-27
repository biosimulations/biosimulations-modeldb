function [sign_eigenval]=Sign_subset_1el%used to compute Figures 5 and 6 in DBS paper%uses PCA analysis to find the # of significant eigenvalues among those %computed via PCAgenerator.m%we use 80% threshold to choose the significant subset of eigenvaluesload PCA_eigenval_w0.3.matS = 0;M = 0;sign_eigenval = zeros(38,10,5); for i = 1:38     for j = 1:10       for k = 1:5            if size(pca_eigenval{i,j,k}) ~= 0                n = 10;                S = sum(pca_eigenval{i,j,k});                M = pca_eigenval{i,j,k}(n);              while n >= 1               n = n - 1;               if M > 0.8*S                   sign_eigenval(i,j,k) = 10 - n;                   n = 0;               else M = M + pca_eigenval{i,j,k}(n);               end                               end            else            sign_eigenval(i,j,k) = 0;            end       end    endendsave('Sign_eig_w0.3.mat','sign_eigenval')x1_ix = 1;for iapp = 5:5  x1_ix=x1_ix+1;  x2_ix = 0;  for gsyn = .5:.1:1.4    x2_ix=x2_ix+1;    x3_ix = 0;    for Kn = 0:2:74         x3_ix=x3_ix+1;        %use computed PCA with Cn=0 as a baseline              ii = sign_eigenval(x3_ix,x2_ix,x1_ix)-sign_eigenval(1,x2_ix,x1_ix);                        if ii <= -3                color='k';            elseif ii == -2                 color='b';            elseif ii == -1                 color='b';            elseif ii == 0                color='w';            elseif ii ==1                color='y';            elseif ii ==2                color='y';            elseif ii >= 3                color='r';            end                              scatter(gsyn,Kn,25,color,'filled')           hold on   end end    xlabel('g_{syn}');ylabel('K_n');fOut2 = sprintf('diffgsynKnplane_w0.3_%s%1.1f.fig','Iapp',iapp);hgsave(fOut2);endend
