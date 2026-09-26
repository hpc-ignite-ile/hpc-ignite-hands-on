help([[
hpc-mesa: Python 3.12 and Mesa 3.5.1 environment for the pv915002
HPC IGNITE qualification run on 2026-09-25.
]])

whatis("Python 3.12 / Mesa 3.5.1 environment for HPC IGNITE")

local prefix = "/project/pv915002-hpcign/wdiazcar/hpc-ignite-rerun-20260925/envs/hpc-mesa-3.5.1"
prepend_path("PATH", pathJoin(prefix, "bin"))
setenv("HPC_MESA_ENV", prefix)
setenv("PYTHONNOUSERSITE", "1")
