#MSUB -l nodes=10:ppn=8
#MSUB -l walltime=1:40:00
#MSUB -e /lustre/jhome15/hhh24/hhh242/TEST/mrun//my-error.txt
#MSUB -o /lustre/jhome15/hhh24/hhh242/TEST/mrun//my-out.txt
#MOAB -v PSMOM_LOG_ACCOUNT

### start of jobscript
module purge

module load parastation/mpi2-intel-5.0.27-1
module load intel/12.1.4

cd $PBS_O_WORKDIR
echo "workdir: $PBS_O_WORKDIR"

# NSLOTS = nodes * ppn = 10 * 8 = 64
NSLOTS=80
echo "running on $NSLOTS cpus ..."

mpiexec -np $NSLOTS --exports=LD_LIBRARY_PATH  /lustre/jhome15/hhh24/hhh242/sven_remo2008_gletscher_Lake_nk/libs//sven_remo2008 < INPUT


