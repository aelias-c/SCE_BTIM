find $HOME/L0_JAXA/weekly -name "*.hdf.gz" -exec gunzip {} \;
find $HOME/L0_JAXA/weekly -name "*.hdf" > all_hdf_files.txt

cat all_hdf_files.txt | parallel --wd $PWD -j 40 python ./process_single_hdf.py {}

